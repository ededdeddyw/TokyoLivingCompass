#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地図データ（OpenStreetMap）の登録が、まわりの駅より大きく少ない駅を見つける。

  python3 scripts/build-coverage-gaps.py

出力: data/computed/coverage-gaps.json  {slug: {category: {"count": n, "peerMedian": m}}}

OpenStreetMap に登録された施設の数は、その土地の地図を作った人の多さに左右される。
護国寺は、まわり2km以内の駅のクリニックの数が中央値で8.5件なのに、0件だった。
2026-11-01 に Overpass で問い合わせ直しても0件で、データを取り直しても埋まらない。

そこで、まわりの駅と比べて大きく少ない駅を記録し、
  - 本文では「少ない」「見当たらない」と言い切らず、登録が少ないことを書く
  - その数から出す点（医療・買い物・外食）は、測れていないものとして出さない
ようにする。実際に少ない駅（団地や工業地帯）も混ざりうるが、機械では区別できない。
少ないと言い切って外れるより、測れていないと書くほうが読み手を誤らせない（ルール13・29）。

まわりの駅: 直線で2km以内にある駅（住宅がほとんどない駅は除く）。
大きく少ない: 自分の数が、まわりの駅の中央値の4分の1以下で、中央値が5以上。

飲食店は、もう1つの見方でも拾う。まわりの駅と比べるだけでは、まわりも同じように登録が少ない
地域（板橋区・目黒区・世田谷区の住宅地など）を拾えなかった。大山は商店街が2つあるのに、
駅から800m以内の飲食店は16軒しか登録されていない。
そこで、駅から半径500mの商業系の用途地域（商業地域・近隣商業地域）の割合と、1日の乗降客数から、
23区の駅全体の傾向として何軒くらいあるかを見込む（対数をとった回帰）。登録がその半分以下で、
見込みとの差が10軒以上ある駅も、登録が少ない駅とする。
用途地域も乗降客数も、地図データとは別の出典なので、地図データの登録の多さに左右されない。
"""
import json
import math
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEER_KM = 2.0
RATIO = 0.25
MIN_PEER_MEDIAN = 5
RADIUS_M = 800
# 点の出し方と対応させる: clinic → healthcare、supermarket → shopping、restaurant → food
CATEGORIES = ("clinic", "supermarket", "restaurant")
EXPECTED_RATIO = 0.5
EXPECTED_MIN_SHORT = 10
# 登録が少ないのではなく、実際に施設が少ないと出典で確かめられる駅。ここに挙げた駅は対象にしない。
REALLY_FEW = {
    # 駅のまわりの大半を舎人公園（都立の大きな公園）が占める（Wikipedia「舎人公園駅」）
    "toneri-koen",
}


def load(rel):
    return json.load(open(os.path.join(ROOT, "data", rel), encoding="utf-8"))


def km(a, b):
    dlat = (a["lat"] - b["lat"]) * 111.0
    dlon = (a["lon"] - b["lon"]) * 111.0 * math.cos(math.radians((a["lat"] + b["lat"]) / 2))
    return math.hypot(dlat, dlon)


def solve(a, b):
    """連立一次方程式 a x = b をガウスの消去法で解く（標準ライブラリだけで動かすため）"""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[piv] = m[piv], m[i]
        for r in range(n):
            if r != i:
                f = m[r][i] / m[i][i]
                m[r] = [x - f * y for x, y in zip(m[r], m[i])]
    return [m[i][n] / m[i][i] for i in range(n)]


def expected_restaurants(counts, roster, nonres):
    """用途地域と乗降客数から見込んだ、駅から800m以内の飲食店の数。{slug: (登録数, 見込み)}"""
    zoning = load("computed/zoning.json")
    zoning = zoning.get("stations", zoning)
    passengers = load("computed/passengers.json")["stations"]
    rows = []
    for slug, c in counts.items():
        if slug in nonres or slug not in roster or slug not in zoning or slug not in passengers:
            continue
        years = passengers[slug].get("byYear") or {}
        # 2021年はコロナ禍で落ちているので、取れている年のうち最大の値を使う
        pax = max(years.values()) if years else 0
        if pax <= 0:
            continue
        g = zoning[slug]["groups"]
        com = g.get("commercial", 0) + g.get("nearCommercial", 0)
        rows.append((slug, [1.0, math.log(pax), com], math.log(c.get("restaurant", 0) + 1)))
    xtx = [[sum(x[i] * x[j] for _, x, _ in rows) for j in range(3)] for i in range(3)]
    xty = [sum(x[i] * y for _, x, y in rows) for i in range(3)]
    beta = solve(xtx, xty)
    return {slug: (counts[slug].get("restaurant", 0),
                   math.exp(sum(b * v for b, v in zip(beta, x))) - 1)
            for slug, x, _ in rows}


def main():
    pois = load("computed/pois.json")["stations"]
    roster = {s["slug"]: s for s in load("roster/stations.json")}
    nonres = load("computed/non-residential.json")

    counts = {}
    for slug, items in pois.items():
        c = {}
        for x in items:
            if x["distanceM"] <= RADIUS_M:
                c[x["category"]] = c.get(x["category"], 0) + 1
        counts[slug] = c

    out = {}
    for slug in sorted(counts):
        if slug in nonres or slug in REALLY_FEW or slug not in roster:
            continue
        peers = [o for o in counts if o != slug and o not in nonres and o in roster
                 and km(roster[slug], roster[o]) <= PEER_KM]
        if len(peers) < 3:
            continue
        for cat in CATEGORIES:
            med = statistics.median(counts[o].get(cat, 0) for o in peers)
            own = counts[slug].get(cat, 0)
            if med >= MIN_PEER_MEDIAN and own <= RATIO * med:
                out.setdefault(slug, {})[cat] = {"count": own, "peerMedian": med}

    for slug, (own, expected) in expected_restaurants(counts, roster, nonres).items():
        if slug in REALLY_FEW or "restaurant" in out.get(slug, {}):
            continue
        if own <= EXPECTED_RATIO * expected and expected - own >= EXPECTED_MIN_SHORT:
            out.setdefault(slug, {})["restaurant"] = {"count": own, "expected": round(expected)}

    path = os.path.join(ROOT, "data", "computed", "coverage-gaps.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for cat in CATEGORIES:
        hit = [s for s, v in out.items() if cat in v]
        print(f"{cat}: {len(hit)}駅")
    print(f"→ {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
