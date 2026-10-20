#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅から歩いて行ける範囲（1km）にかかる、広い公園（1ha以上）の面積を出す。

出力: data/computed/green.json  {slug: {"greenHa": 12.1, "parks": ["林試の森公園", …]}}

なぜ要るのか。
  「公園・自然」の点を、公園の数だけで出していた。小さな公園の多い住宅街が高く出て、
  葛西臨海公園駅は2点、新宿御苑前駅は35点と低く出ていた。公園の広さを入れるため、
  国土数値情報の都市公園データ（P13）と、それに入っていない海上公園・国民公園
  （OpenStreetMap から形を取って面積を計算）から、広い公園の面積を集める。

  build-scores.py（「公園・自然」の点）と build-lifestyle-scores.py（アウトドア派の点）が、
  どちらもこのファイルを読む。広さの数え方を1か所にまとめるため、別のスクリプトにした。

  python3 scripts/build-green.py
"""
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "computed", "green.json")

# 公園データの読み込みは build-lifestyle-scores.py にある関数を使う
_spec = importlib.util.spec_from_file_location(
    "lifestyle", os.path.join(ROOT, "scripts", "build-lifestyle-scores.py"))
lifestyle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lifestyle)


def main():
    roster = json.load(open(os.path.join(ROOT, "data", "roster", "stations.json"), encoding="utf-8"))
    p13 = lifestyle.load_p13()
    parks = [p for p in p13 + lifestyle.load_extra() if p["area"] >= lifestyle.BIG_PARK_M2]
    # 「中央公園」のように、ほかの区にも同じ名前の公園があるものは「北区の中央公園」と書く。
    # 名前だけでは、読み手がどの公園なのか分からない。
    wards_by_name = {}
    for p in p13:
        wards_by_name.setdefault(p["name"], set()).add(p["ward"])
    for p in parks:
        if len(wards_by_name.get(p["name"], ())) > 1 and p.get("ward"):
            p["name"] = f"{p['ward']}の{p['name']}"
    out = {}
    for st in roster:
        here = (st["lat"], st["lon"])
        # 同じ公園が、区画ごと・形の取り方ごとに複数登録されていることがある。
        # 名前ごとにいちばん大きいものだけを数える。
        by_name = {}
        for p in parks:
            # 代表点は公園の中ほどにあるので、広い公園ほど端が駅に近い。
            # 駒沢オリンピック公園（約41ha）は、中心まで測ると駒沢大学駅から1kmを超える。
            # 公園を円とみなし、その半径を引いた距離で測る。
            edge = lifestyle.distance_m(here, p["at"]) - math.sqrt(p["area"] / math.pi)
            if edge <= lifestyle.WALK_M:
                by_name[p["name"]] = max(by_name.get(p["name"], 0), p["area"])
        out[st["slug"]] = {
            "greenHa": round(sum(by_name.values()) / 10_000, 1),
            "parks": sorted(by_name, key=by_name.get, reverse=True)[:3],
        }
    meta = {
        "note": "駅から1km以内に端がかかる（公園を円とみなして半径を引いた距離で測る）、1ha以上の公園の面積の合計。同じ名前の公園は1つとして数える。",
        "sources": [
            {"name": "国土数値情報 都市公園データ（P13、平成23年度）", "url": lifestyle.P13_URL},
            {"name": "OpenStreetMap（海上公園・国民公園の形）", "url": "https://www.openstreetmap.org/"},
        ],
    }
    json.dump({"meta": meta, "stations": out}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    open(OUT, "a", encoding="utf-8").write("\n")
    print(f"広い公園: {len(parks)}か所 / 駅: {len(out)} → {OUT}")


if __name__ == "__main__":
    main()
