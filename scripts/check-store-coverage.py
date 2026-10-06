#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
店の登録が足りていない駅を見つける。

  python3 scripts/check-store-coverage.py

OpenStreetMap に登録された店の数は、その土地の地図を作った人の多さに左右される。
武蔵小山は1日43,946人が使う駅だが、300m以内の飲食店・酒場・カフェは19軒しか
登録されていない。全長約800mのアーケード商店街がある駅の数としては少なすぎる。

そこで、乗降客数が同じくらいの駅と店の数を比べ、大きく下回る駅を並べる。
自動で数を補うことはしない。**「店が少ない」と本文に書く前に、
この一覧に入っていないかを確かめるために使う。**

乗換だけに使われる駅（小竹向原など）や、工業地帯の駅は、
実際に店が少ないので一覧に出てくる。機械では区別できないため、人が見て判断する。
"""
import argparse
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEERS = 12          # 前後この数の駅を「同じくらいの規模」とみなす
MIN_DAILY = 15000   # これ未満の駅は、店が数軒あるかないかで倍率が跳ねる
LOW_RATIO = 0.45    # 同じ規模の中央値に対して、これを下回ったら「明らかに少ない」
WATCH_RATIO = 0.75  # ここまでは「やや少ない」として、人が見る対象にする


def load(rel):
    return json.load(open(os.path.join(ROOT, "data", rel), encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="1駅だけ調べる")
    args = ap.parse_args()
    roster = load("roster/stations.json")
    name = {s["slug"]: s["nameJa"] for s in roster}
    pax = load("computed/passengers.json")["stations"]
    pois = load("computed/pois.json")["stations"]
    shops = {s: sum(1 for p in v
                    if p["category"] in ("restaurant", "bar", "cafe") and p["distanceM"] <= 300)
             for s, v in pois.items()}
    rows = sorted((pax[s]["daily"], shops.get(s, 0), s) for s in pax if s in shops)

    hits = []
    for i, (daily, n, slug) in enumerate(rows):
        if daily < MIN_DAILY:
            continue
        lo = max(0, i - PEERS)
        peers = [r[1] for j, r in enumerate(rows[lo:i + PEERS + 1], lo) if j != i]
        median = statistics.median(peers)
        if median >= 5 and n < median * WATCH_RATIO:
            hits.append((n / median, n, median, daily, slug))

    hits.sort()
    low = [h for h in hits if h[0] < LOW_RATIO]
    watch = [h for h in hits if h[0] >= LOW_RATIO]

    def show(title, group, limit=None):
        print(f"\n■ {title}: {len(group)}駅")
        for ratio, n, median, daily, slug in (group[:limit] if limit else group):
            print(f"  {name[slug]:14} {daily:>9,}人/日  300m以内 {n:>4}軒"
                  f"（同じ規模の中央値 {median:>5.0f}軒、{ratio * 100:>3.0f}%）")
        if limit and len(group) > limit:
            print(f"  ほか{len(group) - limit}駅")

    if args.slug:
        one = [h for h in hits if h[4] == args.slug]
        i = [j for j, r in enumerate(rows) if r[2] == args.slug]
        if not i:
            raise SystemExit(f"{args.slug} は乗降客数のデータに無い")
        j = i[0]
        daily, n, _ = rows[j]
        lo = max(0, j - PEERS)
        peers = [r[1] for k, r in enumerate(rows[lo:j + PEERS + 1], lo) if k != j]
        median = statistics.median(peers)
        print(f"{name[args.slug]}: {daily:,}人/日  300m以内 {n}軒"
              f"（同じ規模の中央値 {median:.0f}軒、{n / max(median, 1) * 100:.0f}%）")
        print("→ " + ("登録が足りていない可能性が高い" if one else "同じ規模の駅と大きくは違わない"))
        return

    print("店の登録が、乗降客数から見て少ない駅")
    print("（自動では直さない。本文に「店が少ない」と書く前に、ここを見る）")
    show("明らかに少ない（中央値の45%未満）", low, 25)
    show("やや少ない（45%以上75%未満）", watch, 25)


if __name__ == "__main__":
    main()
