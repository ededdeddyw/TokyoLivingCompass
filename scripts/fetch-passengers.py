#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅ごとの1日あたり乗降客数を、国土数値情報から取る。

  python3 scripts/fetch-passengers.py

OpenStreetMap から数えた店の数は、地図を作った人の多さに左右される。
駅から500m以内の商業の建物の棟数は、中央値で台東区205棟に対して板橋区9棟と、
20倍以上の開きがある（docs/03-scoring.md §4.4）。
区をまたいで絶対数を比べられないため、街の規模を測る物差しが足りていなかった。

乗降客数は、鉄道事業者が報告した数を国が集計したもので、全国で同じ基準である。
新宿は1日約220万人、御徒町は約10万人で、22倍の開きがある。

出典: 国土数値情報「駅別乗降客数データ」（国土交通省）S12-22
      https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v3_1.html
出力: data/computed/passengers.json
"""
import json
import math
import os
import subprocess
import unicodedata
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
CACHE = os.path.join(ROOT, "data", "poi", "S12-22_GML.zip")
OUT = os.path.join(ROOT, "data", "computed", "passengers.json")
URL = "https://nlftp.mlit.go.jp/ksj/gml/data/S12/S12-22/S12-22_GML.zip"
MEMBER = "UTF-8/S12-22_NumberOfPassengers.geojson"

# geojson の列名は、スキーマの要素名から3つずれている。
# S12_001 が駅名、S12_002 が事業者、S12_003 が路線で、そのあとに
# 年ごとの4列（重複・有無・備考・乗降客数）が2011年から並ぶ。
YEARS = {2018: "S12_037", 2019: "S12_041", 2020: "S12_045", 2021: "S12_049"}
MATCH_M = 1200         # 同じ駅名なら、この距離までは同じ駅とみなす
# 駅名が違う行は採らない。新宿西口駅は新宿駅から300mしか離れていないため、
# 距離だけで拾うと新宿の220万人をそのまま受け取ってしまう。


def download():
    if os.path.exists(CACHE):
        return
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    print("国土数値情報から取得している")
    r = subprocess.run(["curl", "-sS", "--max-time", "300", "-o", CACHE, URL],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(CACHE):
        raise SystemExit(f"取得できなかった: {r.stderr.strip()}")


def centroid(geom):
    """線や点から代表の1点を出す。"""
    pts = []

    def walk(c):
        if not c:
            return
        if isinstance(c[0], (int, float)):
            pts.append((c[1], c[0]))
        else:
            for x in c:
                walk(x)
    walk(geom.get("coordinates"))
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def metres(a, b):
    return math.hypot((a[0] - b[0]) * 111_000,
                      (a[1] - b[1]) * 111_000 * math.cos(math.radians(a[0])))


def normalise(name):
    """駅名を突き合わせる形にそろえる。

    国土数値情報には、常用の字体ではない漢字が混ざっている。笹塚の「塚」は
    互換漢字（U+FA10）で入っており、そのままでは一致しない。
    〈原宿〉のような副名称は外し、本体と副名称の両方を候補にする。
    """
    n = unicodedata.normalize("NFKC", name or "").replace("ケ", "ヶ").replace(" ", "")
    out = {n}
    if "〈" in n and "〉" in n:
        head, rest = n.split("〈", 1)
        out.add(head)
        out.add(rest.rstrip("〉"))
    return out


def main():
    download()
    stations = json.load(open(ROSTER, encoding="utf-8"))
    with zipfile.ZipFile(CACHE) as z:
        doc = json.loads(z.read(MEMBER).decode("utf-8"))

    rows = []
    for f in doc["features"]:
        p = f["properties"]
        c = centroid(f.get("geometry") or {})
        if c is None:
            continue
        rows.append((c, normalise(p.get("S12_001")), p.get("S12_002"),
                     p.get("S12_003"), {y: p.get(k) for y, k in YEARS.items()}))

    out = {}
    for st in stations:
        here = (st["lat"], st["lon"])
        name = normalise(st["nameJa"])
        # 同じ駅名は全国にある。松浦鉄道にも神田駅があるので、距離でも絞る。
        hits = [r for r in rows if (r[1] & name) and metres(here, r[0]) <= MATCH_M]
        if not hits:
            continue
        # 同じ事業者・路線の行が複数あることがある。多いほうを採る。
        best = {}
        for _, _, company, route, vals in hits:
            key = (company, route)
            for year, v in vals.items():
                if v is None:
                    continue
                cur = best.setdefault(key, {})
                cur[year] = max(cur.get(year, 0), int(v))
        by_year = {}
        for vals in best.values():
            for year, v in vals.items():
                by_year[year] = by_year.get(year, 0) + v
        latest = max((y for y, v in by_year.items() if v > 0), default=None)
        if latest is None:
            continue
        out[st["slug"]] = {
            "daily": by_year[latest],
            "year": latest,
            "byYear": {str(y): v for y, v in sorted(by_year.items())},
            "operators": sorted({c for c, _ in best}),
        }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "meta": {
            "source": "国土数値情報「駅別乗降客数データ」（国土交通省）S12-22",
            "sourceUrl": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v3_1.html",
            "unit": "1日あたりの乗降客数（人）",
            "note": "同じ駅に乗り入れる事業者・路線ごとの値を足した。"
                    "事業者が駅全体をまとめて報告している場合、重複する行は0で入っている",
        },
        "stations": out,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)

    by = {s["slug"]: s["nameJa"] for s in stations}
    miss = [by[s["slug"]] for s in stations if s["slug"] not in out]
    top = sorted(out.items(), key=lambda kv: -kv[1]["daily"])[:10]
    print(f"{len(out)}/{len(stations)}駅に乗降客数を割り当てた")
    print("上位10: " + "、".join(f"{by[s]}{v['daily']:,}" for s, v in top))
    if miss:
        print(f"割り当てられなかった{len(miss)}駅: " + "、".join(miss[:30]))


if __name__ == "__main__":
    main()
