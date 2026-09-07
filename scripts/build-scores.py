#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
機械で出せるスコア軸を全駅ぶん計算する。

出力: data/computed/scores.json

いま計算しているのは2軸だけ。
  commute            主要オフィス街への到達しやすさ
  transitConvenience 路線数と事業者の多様性

残る14軸は施設数・犯罪統計・公園面積といった一次データか、人の判断が要る。
どの軸を何で埋めるかは docs/03-scoring.md §4、進め方は docs/11-all-stations-plan.md。

  python3 scripts/build-scores.py
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clamp(v):
    return max(0, min(100, int(round(v))))


def commute_score(minutes_by_hub):
    """
    7つのオフィス駅への所要時間の平均から出す。
    1箇所に速いだけの駅より、どこへでも出やすい駅を高く評価する。

    直線だと平均50分あたりで0に張り付き、郊外側の駅を区別できなくなる。
    8分を100として、そこから24分ごとに半減する曲線にした。
      平均 8分=100 / 20分=71 / 32分=50 / 44分=35 / 56分=25
    """
    mean = sum(minutes_by_hub) / len(minutes_by_hub)
    return clamp(100 * (0.5 ** ((mean - 8) / 24)))


# 路線数から決まる基礎点。4路線を超えると効用が頭打ちになるので上げ幅を絞る。
LINES_BASE = {0: 0, 1: 32, 2: 52, 3: 68, 4: 80, 5: 88}


def transit_score(line_count, operator_count):
    base = LINES_BASE.get(line_count, 93 if line_count >= 6 else 0)
    # 事業者がまたがるほど行き先の幅が広い（直通・振替の選択肢が増える）。
    return clamp(base + min(10, max(0, operator_count - 1) * 5))


def main():
    roster = json.load(
        open(os.path.join(ROOT, "data", "roster", "stations.json"), encoding="utf-8")
    )
    commutes = json.load(
        open(os.path.join(ROOT, "data", "computed", "commutes.json"), encoding="utf-8")
    )
    lines = {
        l["id"]: l
        for l in json.load(
            open(os.path.join(ROOT, "data", "reference", "lines.json"), encoding="utf-8")
        )
    }

    out = {}
    for station in roster:
        scores = {}

        entries = commutes.get(station["slug"])
        if entries:
            scores["commute"] = commute_score([e["minutes"] for e in entries])

        ids = station["lineIds"]
        operators = {lines[i]["operator"] for i in ids if i in lines}
        scores["transitConvenience"] = transit_score(len(ids), len(operators))

        if scores:
            out[station["slug"]] = scores

    path = os.path.join(ROOT, "data", "computed", "scores.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    by_name = {s["slug"]: s["nameJa"] for s in roster}
    ranked = sorted(out.items(), key=lambda kv: -kv[1].get("commute", 0))
    print(f"スコアを計算した駅: {len(out)} / {len(roster)}")
    print("\n通勤スコア 上位10")
    for slug, sc in ranked[:10]:
        print(f"  {by_name[slug]:<12} commute={sc.get('commute')} transit={sc['transitConvenience']}")
    print("\n通勤スコア 下位10")
    for slug, sc in ranked[-10:]:
        print(f"  {by_name[slug]:<12} commute={sc.get('commute')} transit={sc['transitConvenience']}")

    dist = collections.Counter(v["transitConvenience"] // 10 * 10 for v in out.values())
    print("\n乗換利便性の分布")
    for k in sorted(dist):
        print(f"  {k:>3}台: {dist[k]}駅")


if __name__ == "__main__":
    main()
