#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百貨店・ショッピングセンターと、大きな店の位置を OpenStreetMap から取る。

  python3 scripts/fetch-retail.py

「大きな繁華街」を飲食店の数だけで決めると、隣の繁華街からあふれた店を
数えてしまう。湯島と御徒町が新宿や池袋より上に来るのは、そのためである。
買い物でわざわざ来る駅を見分けるには、百貨店とショッピングセンターの数も要る。

出典: OpenStreetMap contributors (ODbL)
出力: data/computed/retail.json
"""
import json
import math
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
RAW = os.path.join(ROOT, "data", "poi", "retail")
OUT = os.path.join(ROOT, "data", "computed", "retail.json")
ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
RADIUS = 400   # 駅を出てすぐ使える範囲


def overpass(query, tries=10):
    for i in range(tries):
        ep = ENDPOINTS[i % len(ENDPOINTS)]
        r = subprocess.run(["curl", "-sS", "--max-time", "180", "-A", "TokyoLivingCompass/1.0",
                            "-d", "data=" + query, ep], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except Exception:  # noqa: BLE001
            print(f"    再試行 {i + 1} ({ep.split('/')[2]})", file=sys.stderr, flush=True)
            time.sleep(min(90, 15 * (i + 1)))
    raise SystemExit("取得できなかった")


def tiles(stations, step=0.06):
    seen = {(math.floor(s["lat"] / step) * step, math.floor(s["lon"] / step) * step)
            for s in stations}
    return [(round(la - 0.01, 3), round(lo - 0.01, 3),
             round(la + step + 0.01, 3), round(lo + step + 0.01, 3))
            for la, lo in sorted(seen)]


def main():
    stations = json.load(open(ROSTER, encoding="utf-8"))
    os.makedirs(RAW, exist_ok=True)
    boxes = tiles(stations)
    print(f"{len(stations)}駅を {len(boxes)} 枚の枠で覆う")

    els = []
    for i, box in enumerate(boxes, 1):
        path = os.path.join(RAW, "_".join(str(v).replace("-", "m") for v in box) + ".json")
        if os.path.exists(path):
            doc = json.load(open(path, encoding="utf-8"))
        else:
            q = (f'[out:json][timeout:180];('
                 f'nwr({box[0]},{box[1]},{box[2]},{box[3]})["shop"~"^(mall|department_store)$"];'
                 f'nwr({box[0]},{box[1]},{box[2]},{box[3]})["amenity"="marketplace"];'
                 f');out center tags;')
            print(f"  [{i}/{len(boxes)}] 取得", flush=True)
            doc = overpass(q)
            json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            time.sleep(3)
        els.extend(doc.get("elements", []))

    uniq = {}
    for e in els:
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lon = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat and lon:
            uniq[(e["type"], e["id"])] = (lat, lon, e.get("tags", {}))
    print(f"百貨店・商業施設・市場: {len(uniq)}件")

    out = {}
    for st in stations:
        lat, lon, found = st["lat"], st["lon"], []
        for la, lo, tags in uniq.values():
            d = math.hypot((la - lat) * 111_000,
                           (lo - lon) * 111_000 * math.cos(math.radians(lat)))
            if d <= RADIUS:
                found.append({"name": tags.get("name"), "m": round(d),
                              "kind": tags.get("shop") or tags.get("amenity")})
        found.sort(key=lambda x: x["m"])
        out[st["slug"]] = {"count": len(found), "places": found[:8]}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "meta": {"source": "OpenStreetMap contributors (ODbL)",
                 "method": f"駅から半径{RADIUS}m以内の shop=mall / department_store / "
                           f"amenity=marketplace を数える",
                 "retrievedAt": time.strftime("%Y-%m-%d")},
        "stations": out,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)
    n = sum(1 for v in out.values() if v["count"] >= 3)
    print(f"{len(out)}駅を計算した。3件以上あるのは {n}駅")


if __name__ == "__main__":
    main()
