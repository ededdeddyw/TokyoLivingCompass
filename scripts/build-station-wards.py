#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅のまわりにかかる区を出す。区の境にある駅では、2つ以上の区になる。

出力: data/computed/station-wards.json  {slug: ["13109", "13110"]}（駅の所在地の区が先頭）

なぜ要るのか。
  駅ページに、保育園の空き状況・学区・ハザードマップの区のページへのリンクを置く。
  目黒駅は品川区にあるが、駅の西側は目黒区である。住む部屋がどちらの区になるかで、
  申し込む保育園も、見るべきハザードマップも変わる。所在地の区だけを出すと、
  半分の読み手を違う区のページへ案内することになる。

やっていること。
  国土交通省の位置参照情報（町丁目ごとの代表点）を読み、駅から500m以内に
  代表点がある町丁目の区を集める。代表点で見るので、境界がすぐそばにあっても
  向こう側の町丁目の代表点が500mより遠ければ拾わない。

  python3 scripts/build-station-wards.py
"""
import csv
import importlib.util
import io
import json
import math
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
OUT = os.path.join(ROOT, "data", "computed", "station-wards.json")
RADIUS_M = 500

# 位置参照情報の取得は fetch-crime.py と同じものを使う（同じ場所にキャッシュする）
_spec = importlib.util.spec_from_file_location(
    "fetch_crime", os.path.join(ROOT, "scripts", "fetch-crime.py"))
fetch_crime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch_crime)


def distance_m(a, b):
    lat = math.radians((a[0] + b[0]) / 2)
    dx = (a[1] - b[1]) * 111320 * math.cos(lat)
    dy = (a[0] - b[0]) * 110540
    return math.hypot(dx, dy)


def main():
    path = fetch_crime.fetch(fetch_crime.ISJ_URL, "isj-13000.zip")
    with zipfile.ZipFile(path) as z:
        csv_name = next(n for n in z.namelist() if n.endswith(".csv"))
        rows = list(csv.reader(io.StringIO(z.read(csv_name).decode("cp932"))))
    # 列: 都道府県コード, 都道府県名, 市区町村コード, 市区町村名, 大字町丁目コード, 大字町丁目名, 緯度, 経度, …
    points = [(row[2], (float(row[6]), float(row[7]))) for row in rows[1:]
              if row[2].startswith("131")]
    roster = json.load(open(ROSTER, encoding="utf-8"))
    out = {}
    for st in roster:
        here = (st["lat"], st["lon"])
        near = {}
        for code, p in points:
            d = distance_m(here, p)
            if d <= RADIUS_M and d < near.get(code, math.inf):
                near[code] = d
        others = sorted((c for c in near if c != st["wardCode"]), key=near.get)
        out[st["slug"]] = [st["wardCode"], *others]
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    open(OUT, "a", encoding="utf-8").write("\n")
    multi = sum(1 for v in out.values() if len(v) > 1)
    print(f"{len(out)}駅のうち、2つ以上の区にかかる駅: {multi} → {OUT}")


if __name__ == "__main__":
    main()
