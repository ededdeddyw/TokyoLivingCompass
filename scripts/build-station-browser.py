#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スマートフォンで全駅のデータを見て回るための1枚のページを組み立てる。

  python3 scripts/build-station-browser.py <出力先.html>

data/ にある出典つきのデータだけを埋め込む。書き手の記憶による記述は入れない。
雛形は scripts/templates/station-browser.html にある。
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
TEMPLATE = os.path.join(ROOT, "scripts", "templates", "station-browser.html")

AXES = ["commute", "transitConvenience", "shopping", "healthcare", "nature",
        "food", "cafe", "nightlife", "fitness"]
DEPTH_FIELDS = ["tagline", "summary", "faces", "terrain", "hazards", "groceries",
                "medical", "nightWalk", "residents", "housingStock", "stationNote",
                "rentRange", "rentReason", "neighbours", "outlook", "residentComment"]


def load(p):
    return json.load(open(os.path.join(D, p), encoding="utf-8"))


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "stations.html")

    roster = load("roster/stations.json")
    lines = {l["id"]: l["nameJa"] for l in load("reference/lines.json")}
    com = load("computed/commutes.json")
    sc = load("computed/scores.json")
    ter = load("computed/terrain.json")["stations"]
    haz = load("computed/hazard.json")["stations"]
    bands = load("computed/rent-bands.json")
    pois = load("computed/pois.json")["stations"]

    rows, deep = [], 0
    for st in roster:
        slug = st["slug"]
        t = ter.get(slug, {})
        flood = haz.get(slug, {}).get("flood", {})
        band = bands.get(slug)
        content_path = os.path.join(D, "content", "ja", f"{slug}.json")
        full = False
        if os.path.exists(content_path):
            c = json.load(open(content_path, encoding="utf-8"))
            full = all(c.get(f) for f in DEPTH_FIELDS)
        deep += full
        markets = [[p["name"], p["walkMinutes"]]
                   for p in pois.get(slug, []) if p["category"] == "supermarket"][:3]
        rows.append({
            "s": slug, "n": st["nameJa"], "w": st["wardNameJa"],
            "l": [lines[i] for i in st["lineIds"] if i in lines],
            "c": {e["to"]: e["minutes"] for e in com.get(slug, [])},
            "sc": {k: v for k, v in (sc.get(slug) or {}).items() if k in AXES},
            "e": t.get("stationElevationM"), "sp": t.get("spreadM"), "sl": t.get("slope"),
            "hz": flood.get("atStation"), "hn": flood.get("aroundCount", 0),
            "r": ({k: [v["low"], v["high"], v["wideSpread"]]
                   for k, v in band["bands"].items()} if band else None),
            "sm": markets, "d": full,
        })

    html = open(TEMPLATE, encoding="utf-8").read()
    html = (html
            .replace("__STATIONS__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
            .replace("__TOTAL__", str(len(rows)))
            .replace("__RENT__", str(sum(1 for r in rows if r["r"])))
            .replace("__DEEP__", str(deep))
            .replace("__TODAY__", time.strftime("%Y-%m-%d")))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{len(rows)}駅 / 家賃の帯 {sum(1 for r in rows if r['r'])}駅 / "
          f"16層 {deep}駅 → {out_path}（{len(html) // 1024}KB）")


if __name__ == "__main__":
    main()
