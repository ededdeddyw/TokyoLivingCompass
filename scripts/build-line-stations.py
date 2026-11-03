#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅グループの中で、名前の違う駅から乗る路線を書き出す。

  python3 scripts/build-line-stations.py

出力: data/computed/line-stations.json
  {slug: {lineId: {"nameJa": "新富町", "nameRomaji": "Shintomicho", "walkMinutes": 5}}}

駅データ.jp（ekidata）は、歩いて乗り換えられる駅を1つの駅グループにまとめている
（docs/09-station-roster.md §5 の2）。築地のグループには新富町（有楽町線）が、
有楽町のグループには日比谷（日比谷線・千代田線・三田線）が入る。
「どの街に住むか」を決める用途では同じ場所として扱ってよいが、
築地のページに有楽町線とだけ書くと、築地駅に有楽町線が止まるように読める。
そこで、表示名と違う名前の駅から乗る路線について、その駅名と、歩いて何分かを持つ。

歩く分数は、表示名の駅の座標（その名前の駅がある路線の座標の平均）から、
その路線の駅の座標までの直線距離で出す。道のりは直線の1.3倍、分速80mとする
（scripts/fetch-pois.py と同じ見込み）。

ekidata のキャッシュ（.cache/roster/）は scripts/build-roster.py が作る。
"""
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "roster")
OUT = os.path.join(ROOT, "data", "computed", "line-stations.json")

# 名前は違うが、同じ駅の別の呼び方であるもの。注記を付けると、かえって別の駅に読める。
# 京王新線の新宿駅は、ekidata では「新線新宿」と書かれている（駅の名前としては新宿駅）。
SAME_STATION = {"新線新宿"}


def norm(name):
    """表記ゆれをそろえる。市ケ谷と市ヶ谷、押上〈スカイツリー前〉と押上（スカイツリー前）"""
    n = (name or "").replace("ケ", "ヶ").strip()
    for open_, close in (("〈", "〉"), ("（", "）"), ("(", ")")):
        if open_ in n:
            n = n.split(open_)[0]
    return n


def km(a, b):
    dlat = (a[0] - b[0]) * 111.0
    dlon = (a[1] - b[1]) * 111.0 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dlat, dlon)


def load_split_words():
    """ローマ字の区切り方は scripts/build-roster.py と同じにする"""
    spec = importlib.util.spec_from_file_location(
        "build_roster", os.path.join(ROOT, "scripts", "build-roster.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.split_words


def main():
    split_words = load_split_words()
    roster = json.load(open(os.path.join(ROOT, "data", "roster", "stations.json"), encoding="utf-8"))
    odpt = json.load(open(os.path.join(CACHE, "odpt_stations.json"), encoding="utf-8"))
    romaji_by_id = {}
    for g in odpt:
        for s in g["stations"]:
            if s.get("code"):
                romaji_by_id[str(s["ekidata_id"])] = s["code"].split(".")[-1]

    lines = {}
    for name in os.listdir(CACHE):
        if name.startswith("line_") and name.endswith(".json"):
            data = json.load(open(os.path.join(CACHE, name), encoding="utf-8"))
            lines[name[5:-5]] = data["station_l"]

    out = {}
    for st in roster:
        g = str(st["groupCode"])
        main_name = norm(st["nameJa"])
        members = {}
        for lid in st["lineIds"]:
            hit = [s for s in lines.get(lid, []) if str(s["station_g_cd"]) == g]
            if hit:
                members[lid] = hit
        # 表示名の駅の座標。その名前の駅がある路線の座標の平均
        home = [(s["lat"], s["lon"]) for hit in members.values() for s in hit
                if norm(s["station_name"]) == main_name]
        if not home:
            continue
        home_pt = (sum(p[0] for p in home) / len(home), sum(p[1] for p in home) / len(home))
        for lid, hit in members.items():
            if any(norm(s["station_name"]) == main_name for s in hit):
                continue
            # 同じ路線に別名の駅が2つあることがある（東京モノレールの羽田空港第1・第2ターミナル）。
            # 近い順に並べてつなぐ。分数は近いほうで出す。
            hit = sorted(hit, key=lambda x: km(home_pt, (x["lat"], x["lon"])))
            if hit[0]["station_name"] in SAME_STATION:
                continue
            minutes = max(1, round(km(home_pt, (hit[0]["lat"], hit[0]["lon"])) * 1000 * 1.3 / 80))
            romajis = []
            for x in hit:
                raw = romaji_by_id.get(str(x["station_cd"]), "")
                if raw:
                    romajis.append("-".join(w[:1].upper() + w[1:].lower() for w in split_words(raw)))
            out.setdefault(st["slug"], {})[lid] = {
                "nameJa": "・".join(x["station_name"] for x in hit),
                **({"nameRomaji": " / ".join(romajis)} if len(romajis) == len(hit) else {}),
                "walkMinutes": minutes,
            }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    for slug, v in sorted(out.items()):
        print(slug, {lid: (x["nameJa"], x["walkMinutes"], x.get("nameRomaji")) for lid, x in v.items()})
    print(f"{len(out)}駅 → {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
