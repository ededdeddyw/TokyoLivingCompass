#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅の周りにある建物の「延べ階数」を数える。

  python3 scripts/fetch-buildings.py

飲食店の数だけで繁華街の規模を測ると、新宿・池袋・渋谷が実態よりずっと低く出る。
原因は2つある。

  1. 駅の範囲が広い。新宿は駅から150m以内の飲食店が7軒しかないが、
     そこは駅の構内である。店は300m以上外側から始まる。
  2. 雑居ビルのテナントが OpenStreetMap に入っていない。取得済みの飲食店ノードで
     階の情報を持つものは1件しかなく、実質すべて路面店である。
     歌舞伎町の範囲には建物が595件あり、階数の登録がある208件の中央値は6階だった。
     2階から8階の飲食店は、まるごと数から抜け落ちている。

そこで、建物の階数を足し合わせて商業の厚みを測る。
建物の用途（commercial / retail / office など）で絞り、階数の登録がないものは
その範囲の中央値で補う。

出典: OpenStreetMap contributors (ODbL)
出力: data/computed/buildings.json
"""
import json
import math
import os
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
CACHE = os.path.join(ROOT, "data", "poi", "buildings")
OUT = os.path.join(ROOT, "data", "computed", "buildings.json")
ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
RADIUS = 500          # 駅を出て歩く範囲
COMMERCIAL = {"commercial", "retail", "office", "mixed", "hotel", "supermarket",
              "department_store", "kiosk", "shop"}


def fetch(query, tmp, tries=10):
    """Overpass から取得し、一時ファイルに落としてから読む。応答が大きいため。"""
    for i in range(tries):
        ep = ENDPOINTS[i % len(ENDPOINTS)]
        subprocess.run(["curl", "-sS", "--max-time", "300", "-A", "TokyoLivingCompass/1.0",
                        "-o", tmp, "-d", "data=" + query, ep], capture_output=True, text=True)
        try:
            with open(tmp, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:  # noqa: BLE001
            print(f"    再試行 {i + 1} ({ep.split('/')[2]})", file=sys.stderr, flush=True)
            time.sleep(min(90, 15 * (i + 1)))
    raise SystemExit("建物データを取得できなかった")


def reduce_tile(doc):
    """Overpass の応答から、緯度・経度・階数・商業かどうかだけを残す。"""
    levels = []
    rows = []
    for e in doc.get("elements", []):
        t = e.get("tags", {})
        raw = str(t.get("building:levels", ""))
        lv = int(raw) if raw.isdigit() else None
        if lv is not None:
            levels.append(min(lv, 60))
        c = e.get("center") or {}
        la, lo = c.get("lat"), c.get("lon")
        if la is None:
            continue
        biz = t.get("building") in COMMERCIAL or any(k in t for k in ("shop", "amenity", "office"))
        if not biz:
            continue
        rows.append([round(la, 5), round(lo, 5), lv])
    return {"median": statistics.median(levels) if levels else 3,
            "withLevels": len(levels), "rows": rows}


def tiles(stations, step=0.05):
    seen = {(math.floor(s["lat"] / step) * step, math.floor(s["lon"] / step) * step)
            for s in stations}
    return [(round(la - 0.008, 3), round(lo - 0.008, 3),
             round(la + step + 0.008, 3), round(lo + step + 0.008, 3))
            for la, lo in sorted(seen)]


def main():
    stations = json.load(open(ROSTER, encoding="utf-8"))
    os.makedirs(CACHE, exist_ok=True)
    boxes = tiles(stations)
    print(f"{len(stations)}駅を {len(boxes)} 枚の枠で覆う", flush=True)

    total = {s["slug"]: 0 for s in stations}
    count = {s["slug"]: 0 for s in stations}
    tmp = os.path.join(CACHE, "_tmp.json")

    for i, box in enumerate(boxes, 1):
        name = "_".join(str(v).replace("-", "m") for v in box)
        path = os.path.join(CACHE, name + ".small.json")
        old = os.path.join(CACHE, name + ".json")
        if os.path.exists(path):
            tile = json.load(open(path, encoding="utf-8"))
        else:
            if os.path.exists(old):
                doc = json.load(open(old, encoding="utf-8"))
            else:
                q = (f'[out:json][timeout:300];'
                     f'way({box[0]},{box[1]},{box[2]},{box[3]})["building"];'
                     f'out tags center;')
                print(f"  [{i}/{len(boxes)}] 取得", flush=True)
                doc = fetch(q, tmp)
                time.sleep(3)
            tile = reduce_tile(doc)
            del doc
            json.dump(tile, open(path, "w", encoding="utf-8"))
            if os.path.exists(old):
                os.remove(old)

        near = [s for s in stations
                if box[0] - 0.006 <= s["lat"] <= box[2] + 0.006
                and box[1] - 0.007 <= s["lon"] <= box[3] + 0.007]
        med = tile["median"]
        for la, lo, lv in tile["rows"]:
            level = med if lv is None else lv
            for s in near:
                d = math.hypot((la - s["lat"]) * 111_000,
                               (lo - s["lon"]) * 111_000 * math.cos(math.radians(s["lat"])))
                if d <= RADIUS:
                    total[s["slug"]] += level
                    count[s["slug"]] += 1
        del tile
    if os.path.exists(tmp):
        os.remove(tmp)

    out = {s: {"floors": round(total[s]), "buildings": count[s]} for s in total}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "meta": {"source": "OpenStreetMap contributors (ODbL)",
                 "method": f"駅から半径{RADIUS}m以内の商業・事務所・店舗の建物について、"
                           f"building:levels を足し合わせた。登録がない建物は、"
                           f"その範囲の中央値で補っている",
                 "retrievedAt": time.strftime("%Y-%m-%d")},
        "stations": out,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)
    top = sorted(out.items(), key=lambda kv: -kv[1]["floors"])[:10]
    by = {s["slug"]: s["nameJa"] for s in stations}
    print("延べ階数 上位10: " + "、".join(f"{by[s]}{v['floors']}" for s, v in top), flush=True)


if __name__ == "__main__":
    main()
