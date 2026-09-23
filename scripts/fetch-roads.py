#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
幹線道路と高速道路の位置を OpenStreetMap から取る。

  python3 scripts/fetch-roads.py

騒音には、人が出す音と、車が出す音の2種類がある。これまで静かさを
「駅から300m以内の酒場と飲食店の少なさ」だけで測っていたため、
繁華街から離れていても幹線道路に面している駅を、静かだと判定していた。
岩本町は昭和通りと靖国通りが交わり、昭和通りの上には首都高速1号上野線が通る。
飲み屋は少ないが、車の音は一日中続く。

道路の種別は OSM の highway タグによる。
  motorway  高速道路（首都高など）
  trunk     幹線道路（環七、甲州街道など）
  primary   主要道路（靖国通り、昭和通りなど）
  secondary それに次ぐ道路

出典: OpenStreetMap contributors (ODbL)
出力: data/computed/roads.json
"""
import json
import math
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
RAW = os.path.join(ROOT, "data", "poi", "roads")
OUT = os.path.join(ROOT, "data", "computed", "roads.json")
# 1つの窓口に続けて投げると断られるので、順に切り替える。
ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

CLASSES = ("motorway", "trunk", "primary", "secondary")
# この距離までを「沿道」とみなす。道路の中心線からの距離なので、
# 幅のある道路では実際の車道の端はこれより近い。
NEAR_M = 150


def overpass(query, tries=10):
    for i in range(tries):
        endpoint = ENDPOINTS[i % len(ENDPOINTS)]
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "180", "-A", "TokyoLivingCompass/1.0",
             "-d", "data=" + query, endpoint],
            capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except Exception:  # noqa: BLE001
            print(f"    再試行 {i + 1} ({endpoint.split('/')[2]})",
                  (r.stdout or r.stderr)[:60], file=sys.stderr, flush=True)
            time.sleep(min(90, 15 * (i + 1)))
    raise SystemExit("道路データを取得できなかった")


def tiles(stations, step=0.06):
    """駅を覆う緯度経度の枠を作る。1枚が大きすぎると取得が落ちる。"""
    seen = set()
    for s in stations:
        seen.add((math.floor(s["lat"] / step) * step, math.floor(s["lon"] / step) * step))
    out = []
    for lat, lon in sorted(seen):
        out.append((round(lat - 0.01, 3), round(lon - 0.01, 3),
                    round(lat + step + 0.01, 3), round(lon + step + 0.01, 3)))
    return out


def dist_to_segment(plat, plon, a, b):
    """点と線分の距離（メートル）。緯度経度を平面に近似して計算する。"""
    k = math.cos(math.radians(plat))
    px, py = plon * k, plat
    ax, ay = a[1] * k, a[0]
    bx, by = b[1] * k, b[0]
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        t = 0.0
    else:
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy) * 111_000


def main():
    stations = json.load(open(ROSTER, encoding="utf-8"))
    os.makedirs(RAW, exist_ok=True)
    boxes = tiles(stations)
    print(f"{len(stations)}駅を {len(boxes)} 枚の枠で覆う")

    ways = []
    for i, box in enumerate(boxes, 1):
        path = os.path.join(RAW, "_".join(str(v).replace("-", "m") for v in box) + ".json")
        if os.path.exists(path):
            doc = json.load(open(path, encoding="utf-8"))
        else:
            q = (f'[out:json][timeout:180];'
                 f'way({box[0]},{box[1]},{box[2]},{box[3]})'
                 f'["highway"~"^({"|".join(CLASSES)})$"];out geom tags;')
            print(f"  [{i}/{len(boxes)}] 取得", flush=True)
            doc = overpass(q)
            json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            time.sleep(3)
        ways.extend(doc.get("elements", []))

    # 同じ道路が複数の枠に出るので、OSM の id で重複を落とす
    uniq = {w["id"]: w for w in ways if w.get("geometry")}
    print(f"道路: {len(uniq)}本")

    out = {}
    for st in stations:
        lat, lon = st["lat"], st["lon"]
        best = {c: None for c in CLASSES}
        names = {c: None for c in CLASSES}
        lanes = {c: None for c in CLASSES}
        for w in uniq.values():
            cls = w["tags"].get("highway")
            if cls not in CLASSES:
                continue
            g = w["geometry"]
            # 枠の外の道路は早めに捨てる
            if min(abs(p["lat"] - lat) for p in g) > 0.01:
                continue
            d = min(dist_to_segment(lat, lon, (g[k]["lat"], g[k]["lon"]),
                                    (g[k + 1]["lat"], g[k + 1]["lon"]))
                    for k in range(len(g) - 1)) if len(g) > 1 else 1e9
            if best[cls] is None or d < best[cls]:
                best[cls] = d
                names[cls] = w["tags"].get("name")
                try:
                    lanes[cls] = int(w["tags"].get("lanes", "")) if w["tags"].get("lanes") else None
                except ValueError:
                    lanes[cls] = None
        rec = {}
        for c in CLASSES:
            if best[c] is not None and best[c] <= 1200:
                rec[c] = {"m": round(best[c]), "name": names[c], "lanes": lanes[c]}
        # 沿道かどうか。中心線から150m以内に幹線級の道路があるか
        rec["nearMajorM"] = min(
            [v["m"] for k, v in rec.items() if k in ("motorway", "trunk", "primary")],
            default=None)
        rec["nearAnyM"] = min([v["m"] for k, v in rec.items() if k in CLASSES], default=None)
        out[st["slug"]] = rec

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "meta": {
            "source": "OpenStreetMap contributors (ODbL)",
            "method": f"highway が {'/'.join(CLASSES)} の道路について、"
                      f"駅から中心線までの最短距離を計算。{NEAR_M}m以内を沿道とみなす",
            "retrievedAt": time.strftime("%Y-%m-%d"),
        },
        "stations": out,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)
    n = sum(1 for v in out.values() if v.get("nearMajorM") is not None and v["nearMajorM"] <= NEAR_M)
    print(f"{len(out)}駅を計算した。うち{NEAR_M}m以内に幹線級の道路があるのは {n}駅")


if __name__ == "__main__":
    main()
