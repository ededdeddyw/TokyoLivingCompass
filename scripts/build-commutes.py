#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全駅から主要オフィス駅までの所要時間を、鉄道network上の最短経路として計算する。

出力: data/computed/commutes.json

これは時刻表に基づく値ではなく、駅間距離と路線種別から推定した所要時間である。
方法と限界は docs/10-commute-estimation.md を参照。

  python3 scripts/build-commutes.py
"""
import collections
import heapq
import json
import math
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "roster")
EKIDATA_API = "https://raw.githubusercontent.com/ny-a/ekidata/gh-pages/api"

# ロースターの対象路線に加えて、経路として実際に使われる路線も入れる。
# これを入れないと「その駅からは行けない」経路が生まれ、所要時間が過大になる。
GRAPH_LINES = [
    # 都営
    "99301", "99302", "99303", "99304", "99305", "99342",
    # 東京メトロ
    "28001", "28002", "28003", "28004", "28005", "28006", "28008", "28009", "28010",
    # JR（ロースター対象外だが経路に必要なものを含む）
    "11302", "11312", "11313", "11332", "11321", "11320", "11314",
    "11301", "11308", "11326", "11333", "11343",
    # 私鉄等
    "21001", "21002", "21005", "21006",
    "22001", "22003", "22004", "22007",
    "23001", "23002", "23003",
    "24001", "24006", "24007",
    "25001",
    "26001", "26002", "26003", "26004", "26005", "26006", "26007",
    "27001", "27002",
    "99307", "99309", "99311", "99336", "99337", "99340",
]

# 路線種別ごとの表定速度(km/h)。停車時間は別に加算する。
# 実際の所要時間に合うよう、既知の区間で当たりを取って決めた値。
DEFAULT_SPEED = 35.0
LINE_SPEED = {
    "11302": 33.0,   # 山手線
    "11312": 45.0,   # 中央線快速
    "11313": 32.0,   # 中央総武線各停
    "11332": 38.0,   # 京浜東北線
    "11321": 45.0,   # 埼京線
    "11320": 40.0,   # 常磐線
    "11314": 45.0,   # 総武本線
    "11301": 50.0,   # 東海道本線
    "11308": 50.0,   # 横須賀線
    "11326": 45.0,   # 京葉線
    "11333": 50.0,   # 湘南新宿ライン
    "11343": 50.0,   # 上野東京ライン
    "99305": 13.0,   # 都電荒川線
    "99342": 25.0,   # 日暮里・舎人ライナー
    "99311": 25.0,   # ゆりかもめ
    "99309": 55.0,   # つくばエクスプレス
    "99336": 40.0,   # 東京モノレール
    "26007": 15.0,   # 東急世田谷線
    # 優等列車のある幹線。各停のみの駅は実際よりやや速く出る。
    "26001": 38.0,   # 東急東横線
    "26003": 38.0,   # 東急田園都市線
    "24001": 38.0,   # 京王線
    "25001": 38.0,   # 小田急線
    "27001": 40.0,   # 京急本線
    "21001": 38.0,   # 東武東上線
    "21002": 38.0,   # 東武伊勢崎線
    "22001": 38.0,   # 西武池袋線
    "22007": 38.0,   # 西武新宿線
}

DWELL_MIN = 0.4        # 1駅あたりの停車時間
TRANSFER_MIN = 5.0     # 乗り換え1回あたり（徒歩＋待ち）
# 最初の待ち時間は含めない。世間で言う「新宿まで5分」は乗車時間を指すため、
# それに揃えないと利用者の持っている感覚とずれる。
BOARD_MIN = 0.0

# 勤務先起点検索のオフィス駅。src/lib/schema.ts の OFFICE_HUBS と対応する。
OFFICE_HUBS = {
    "shinjuku": "新宿",
    "shibuya": "渋谷",
    "tokyo": "東京",
    "shinagawa": "品川",
    "otemachi": "大手町",
    "toranomon": "虎ノ門",
    "roppongi": "六本木",
}


def fetch(url, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print(f"  download {name}", file=sys.stderr)
        with urllib.request.urlopen(url, timeout=120) as res, open(path, "wb") as f:
            f.write(res.read())
    return path


def km(a, b):
    """2点間の距離(km)。線路の曲がりを見込んで直線距離を1.15倍する。"""
    lat1, lon1 = a
    lat2, lon2 = b
    dlat = (lat2 - lat1) * 111.0
    dlon = (lon2 - lon1) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dlat, dlon) * 1.15


def build_graph():
    """
    ノードは (駅グループ, 路線) の組。同じ駅の別路線どうしを乗換辺でつなぐ。
    こうしないと「乗換回数」を数えられない。
    """
    edges = collections.defaultdict(list)   # node -> [(node, minutes, is_transfer)]
    coords, names = {}, {}
    station_lines = collections.defaultdict(set)

    for line_cd in GRAPH_LINES:
        data = json.load(
            open(fetch(f"{EKIDATA_API}/l/{line_cd}.json", f"line_{line_cd}.json"),
                 encoding="utf-8")
        )
        speed = LINE_SPEED.get(line_cd, DEFAULT_SPEED)
        seq = data["station_l"]
        for s in seq:
            g = str(s["station_g_cd"])
            coords.setdefault(g, (s["lat"], s["lon"]))
            names.setdefault(g, s["station_name"])
            station_lines[g].add(line_cd)

        for a, b in zip(seq, seq[1:]):
            ga, gb = str(a["station_g_cd"]), str(b["station_g_cd"])
            if ga == gb:
                continue
            minutes = km(coords[ga], coords[gb]) / speed * 60 + DWELL_MIN
            edges[(ga, line_cd)].append(((gb, line_cd), minutes, False))
            edges[(gb, line_cd)].append(((ga, line_cd), minutes, False))

    # 同一駅内の乗り換え
    for g, lines in station_lines.items():
        for la in lines:
            for lb in lines:
                if la != lb:
                    edges[(g, la)].append(((g, lb), TRANSFER_MIN, True))

    return edges, coords, names, station_lines


def dijkstra(edges, station_lines, origin_group):
    """
    オフィス駅から全駅への最短所要時間。
    所要時間だけを最小化すると乗換だらけの経路になるので、乗換にも時間を課している。
    """
    best = {}
    heap = []
    for line in station_lines[origin_group]:
        node = (origin_group, line)
        best[node] = (BOARD_MIN, 0)
        heapq.heappush(heap, (BOARD_MIN, 0, node))

    while heap:
        cost, transfers, node = heapq.heappop(heap)
        if best.get(node, (math.inf,))[0] < cost:
            continue
        for nxt, minutes, is_transfer in edges[node]:
            nc = cost + minutes
            nt = transfers + (1 if is_transfer else 0)
            cur = best.get(nxt)
            if cur is None or nc < cur[0] - 1e-9:
                best[nxt] = (nc, nt)
                heapq.heappush(heap, (nc, nt, nxt))

    # 駅単位に畳む。同じ駅でも到達に使う路線で結果が違うため、最短のものを採る。
    per_station = {}
    for (g, _line), (cost, transfers) in best.items():
        cur = per_station.get(g)
        if cur is None or cost < cur[0]:
            per_station[g] = (cost, transfers)
    return per_station


def main():
    print("鉄道networkを構築中...", file=sys.stderr)
    edges, coords, names, station_lines = build_graph()
    print(f"  駅 {len(coords)} / ノード {len(edges)}", file=sys.stderr)

    roster = json.load(
        open(os.path.join(ROOT, "data", "roster", "stations.json"), encoding="utf-8")
    )
    # 駅名は出典によって表記が違う（有楽町/日比谷、押上の括弧の種類など）。
    # 結合は必ず駅グループコードで行う。
    group_by_name = {}
    for g, n in names.items():
        group_by_name.setdefault(n, g)

    hub_groups = {}
    for hub, name in OFFICE_HUBS.items():
        g = group_by_name.get(name)
        if g is None:
            raise SystemExit(f"オフィス駅が見つかりません: {name}")
        hub_groups[hub] = g

    print("最短経路を計算中...", file=sys.stderr)
    results = {hub: dijkstra(edges, station_lines, g) for hub, g in hub_groups.items()}

    out, missing = {}, []
    for station in roster:
        g = station["groupCode"]
        if g not in names:
            missing.append(station["nameJa"])
            continue
        commutes = []
        for hub in OFFICE_HUBS:
            found = results[hub].get(g)
            if not found:
                continue
            minutes, transfers = found
            commutes.append({
                "to": hub,
                "minutes": max(1, round(minutes)),
                "transfers": transfers,
            })
        if len(commutes) == len(OFFICE_HUBS):
            out[station["slug"]] = commutes
        else:
            missing.append(station["nameJa"])

    os.makedirs(os.path.join(ROOT, "data", "computed"), exist_ok=True)
    path = os.path.join(ROOT, "data", "computed", "commutes.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\n所要時間を計算できた駅: {len(out)} / {len(roster)}")
    if missing:
        print(f"計算できなかった駅 ({len(missing)}): {', '.join(missing[:20])}")


if __name__ == "__main__":
    main()
