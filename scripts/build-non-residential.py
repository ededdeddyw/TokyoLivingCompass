#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
まわりに住宅がほとんどない駅を見分ける。

  python3 scripts/build-non-residential.py

出力: data/computed/non-residential.json  {slug: {"basis": ..., "schools": n, "supermarkets": n, "nearby": [slug, ...]}}

空港・展示場・倉庫街・官庁街の駅も、23区の駅として全458駅に入っている。
ページは残すが、「住む駅」として勧める一覧（暮らし方別の一覧、勤務先から探す）では
後ろに回すか外し、駅ページの冒頭で、住む場所として見るなら近くのどの駅かを示す。

見分け方は地図データ（OpenStreetMap、scripts/fetch-pois.py）で、
駅から800m（歩いて13分ほど）以内に
  - 学校・幼稚園・保育園が1か所以下、かつ
  - スーパーが1軒以下
の駅とする。住む人がいれば、子どもの通う施設と毎日の買い物の店がどちらかは近くにある。
地図データだけでは拾えない駅（橋の向こうの住宅地の施設が800mに入ってしまう駅）は、
出典のある事実をもとに MANUAL に足す。
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POIS = os.path.join(ROOT, "data", "computed", "pois.json")
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
OUT = os.path.join(ROOT, "data", "computed", "non-residential.json")

RADIUS_M = 800
MAX_SCHOOLS = 1
MAX_SUPERMARKETS = 1

# 地図データでは見分けられない駅。理由は出典の記事に書かれている事実。
MANUAL = {
    # 昭和島は工場と倉庫の島で、住民登録のある人がいない（Wikipedia「昭和島」）。
    # 800m以内に対岸の大森東の学校が入るため、地図データの条件をすり抜ける。
    "showajima": "manual",
    # 整備場駅の出入口は羽田空港の整備地区の中にあり、まわりは航空会社の施設である
    # （Wikipedia「整備場駅」）。800m以内に海老取川の対岸の東糀谷の施設が入る。
    "seibijo": "manual",
}


def km(a, b):
    dlat = (a["lat"] - b["lat"]) * 111.0
    dlon = (a["lon"] - b["lon"]) * 111.0 * math.cos(math.radians((a["lat"] + b["lat"]) / 2))
    return math.hypot(dlat, dlon)


def main():
    pois = json.load(open(POIS, encoding="utf-8"))["stations"]
    roster = json.load(open(ROSTER, encoding="utf-8"))
    by_slug = {s["slug"]: s for s in roster}

    counts = {}
    for slug, items in pois.items():
        near = [x for x in items if x["distanceM"] <= RADIUS_M]
        counts[slug] = (
            sum(1 for x in near if x["category"] in ("school", "kindergarten", "childcare")),
            sum(1 for x in near if x["category"] == "supermarket"),
        )

    flagged = {}
    for slug, (schools, shops) in counts.items():
        if slug in MANUAL:
            flagged[slug] = "manual"
        elif schools <= MAX_SCHOOLS and shops <= MAX_SUPERMARKETS:
            flagged[slug] = "pois"
    for slug in MANUAL:
        flagged.setdefault(slug, "manual")

    out = {}
    for slug, basis in sorted(flagged.items()):
        here = by_slug[slug]
        # 住む場所として見るなら、ここから近い、住宅のある駅
        nearby = sorted((km(here, o), o["slug"]) for o in roster
                        if o["slug"] != slug and o["slug"] not in flagged)[:2]
        schools, shops = counts.get(slug, (0, 0))
        out[slug] = {"basis": basis, "schools": schools, "supermarkets": shops,
                     "nearby": [s for _, s in nearby]}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"住宅がほとんどない駅: {len(out)} → {os.path.relpath(OUT, ROOT)}")
    for slug, v in out.items():
        print(f"  {by_slug[slug]['nameJa']}（{v['basis']}）学校等{v['schools']} スーパー{v['supermarkets']}"
              f" → {', '.join(by_slug[n]['nameJa'] for n in v['nearby'])}")


if __name__ == "__main__":
    main()
