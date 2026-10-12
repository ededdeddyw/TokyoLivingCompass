#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
住む人の層（5つ）と休日の過ごし方（インドア派・アウトドア派）ごとに、駅の向き不向きを点にする。

出力: data/computed/lifestyle.json

なぜ要るのか。
  これまでの点は、どれも「その駅のまわりに何があるか」だけを見ていた。
  しかし休日に出かける先は、駅のまわりでなくてもよい。大崎のまわりに広い公園は少ないが、
  りんかい線に乗れば十数分で潮風公園やお台場海浜公園に着く。アウトドア派にとって、
  大崎は「近所では遊べないが、電車ですぐ遊びに行ける駅」である。
  そこで点を2つに分ける。

  暮らし   毎日のことなので、駅のまわりで済むかどうかで見る（買い物・病院・治安・通勤など）。
  楽しみ   休日のことなので、電車で行ける駅まで含めて見る。行き先までの時間で割り引く。

やっていること。
  1. 広い公園（1ha以上）の面積を、国土数値情報の都市公園データ（P13）と、
     それに入っていない海上公園・国民公園（OpenStreetMap から形を取って面積を計算）から集める。
  2. 駅から歩いて行ける範囲（1km）にある広い公園の面積を、駅ごとに足す。
  3. 鉄道の所要時間を、全458駅どうしで出す（build-commutes.py と同じ鉄道網）。
  4. 楽しみの点は、行ける駅の中で「その駅の魅力 × 時間の割引」がいちばん大きい駅で決める。
     時間の割引は、0分で1、45分で0になる直線。
  5. 暮らしの点と楽しみの点を、層ごとの重みで合わせ、23区の駅どうしの相対的な位置にする。

  python3 scripts/build-lifestyle-scores.py
"""
import importlib.util
import json
import math
import os
import struct
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POI_DIR = os.path.join(ROOT, "data", "poi")
P13_URL = "https://nlftp.mlit.go.jp/ksj/gml/data/P13/P13-11/P13-11_13_GML.zip"
P13_ZIP = os.path.join(POI_DIR, "p13-13.zip")
# 都市公園データに入っていない、海上公園と国民公園。OpenStreetMap から形を取った。
EXTRA_PARKS = os.path.join(POI_DIR, "parks-extra-osm.json")
OUT = os.path.join(ROOT, "data", "computed", "lifestyle.json")

BIG_PARK_M2 = 10_000      # 「広い公園」とみなす面積（1ha）
WALK_M = 1_000            # 歩いて行ける範囲
REACH_ZERO_MIN = 45       # この時間で、行き先の魅力が0になる

_spec = importlib.util.spec_from_file_location(
    "build_commutes", os.path.join(ROOT, "scripts", "build-commutes.py"))
commutes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(commutes)


def distance_m(a, b):
    lat = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[1] - b[1]) * 111320 * math.cos(lat), (a[0] - b[0]) * 110540)


def ring_area(pts):
    if len(pts) < 3:
        return 0.0
    lat0 = math.radians(sum(p["lat"] for p in pts) / len(pts))
    xs = [p["lon"] * 111320 * math.cos(lat0) for p in pts]
    ys = [p["lat"] * 110540 for p in pts]
    return abs(sum(xs[i] * ys[i + 1] - xs[i + 1] * ys[i] for i in range(len(pts) - 1))) / 2


def stitch(ways):
    """リレーションの外周を、つながった輪にまとめる。"""
    key = lambda p: (round(p["lat"], 7), round(p["lon"], 7))  # noqa: E731
    segs = [list(w) for w in ways if len(w) > 1]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while key(ring[0]) != key(ring[-1]) and changed:
            changed = False
            for i, s in enumerate(segs):
                if key(s[0]) == key(ring[-1]):
                    ring += s[1:]
                elif key(s[-1]) == key(ring[-1]):
                    ring += s[::-1][1:]
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        rings.append(ring)
    return rings


def load_p13():
    """国土数値情報 都市公園（東京都）。名前・面積（㎡）・代表点を返す。"""
    if not os.path.exists(P13_ZIP):
        os.makedirs(POI_DIR, exist_ok=True)
        with urllib.request.urlopen(P13_URL, timeout=120) as res, open(P13_ZIP, "wb") as f:
            f.write(res.read())
    z = zipfile.ZipFile(P13_ZIP)
    dbf = z.read(next(n for n in z.namelist() if n.endswith(".dbf")))
    shp = z.read(next(n for n in z.namelist() if n.endswith(".shp")))
    count = struct.unpack("<I", dbf[4:8])[0]
    head_len, rec_len = struct.unpack("<HH", dbf[8:12])
    fields, i = [], 32
    while dbf[i] != 0x0D:
        fields.append((dbf[i:i + 11].split(b"\0")[0].decode(), dbf[i + 16]))
        i += 32
    rows = []
    for r in range(count):
        off, row = head_len + r * rec_len + 1, {}
        for name, length in fields:
            row[name] = dbf[off:off + length].decode("cp932", "replace").strip()
            off += length
        rows.append(row)
    points, pos = [], 100
    while pos < len(shp):
        _num, clen = struct.unpack(">II", shp[pos:pos + 8])
        x, y = struct.unpack("<dd", shp[pos + 12:pos + 28])
        points.append((y, x))
        pos += 8 + clen * 2
    # P13_003: 公園名、P13_008: 供用済面積（㎡）
    return [{"name": r["P13_003"], "area": float(r["P13_008"] or 0), "at": p}
            for r, p in zip(rows, points)]


def load_extra():
    """海上公園・国民公園。形から面積を出し、代表点は外周の点の平均にする。"""
    data = json.load(open(EXTRA_PARKS, encoding="utf-8"))
    parks = {}
    for e in data["elements"]:
        name = e["tags"].get("name")
        if e["type"] == "way":
            g = e.get("geometry", [])
            area = ring_area(g) if g and g[0] == g[-1] else 0.0
            pts = g
        else:
            outer = [m["geometry"] for m in e["members"]
                     if m.get("role") == "outer" and m.get("geometry")]
            inner = [m["geometry"] for m in e["members"]
                     if m.get("role") == "inner" and m.get("geometry")]
            area = (sum(ring_area(r) for r in stitch(outer))
                    - sum(ring_area(r) for r in stitch(inner)))
            pts = [p for r in outer for p in r]
        cur = parks.setdefault(name, {"name": name, "area": 0.0, "lats": [], "lons": []})
        cur["area"] += area
        cur["lats"] += [p["lat"] for p in pts]
        cur["lons"] += [p["lon"] for p in pts]
    return [{"name": p["name"], "area": p["area"],
             "at": (sum(p["lats"]) / len(p["lats"]), sum(p["lons"]) / len(p["lons"]))}
            for p in parks.values() if p["lats"]]


def percentile(values):
    ranked = sorted(values.values())
    n = len(ranked)
    return {k: 100 * sum(1 for r in ranked if r < v) / max(1, n - 1) for k, v in values.items()}


# 層ごとの「暮らし」の重み。どれも駅のまわりで済ませることなので、駅の点をそのまま使う。
# 通勤（都心アクセス・乗換利便性）と家賃は、ここに入れない。どの層にとっても大きな材料だが、
# 入れると「暮らしやすさ」の差が通勤と家賃の差に埋もれる。別に持っておき、
# サイトで公開するときに合わせる（docs/18-persona-days.md §6.6）。
LIFE_WEIGHTS = {
    "single": {"singleLife": 0.4, "safety": 0.35, "shopping": 0.25},
    "dinks": {"safety": 0.3, "food": 0.25, "shopping": 0.25, "healthcare": 0.2},
    "family": {"family": 0.35, "safety": 0.2, "shopping": 0.15, "healthcare": 0.1,
               "disaster": 0.1, "quietness": 0.1},
    "senior": {"healthcare": 0.3, "shopping": 0.2, "quietness": 0.15, "safety": 0.15,
               "disaster": 0.1, "flat": 0.1},
}
# 暮らしと楽しみの比。子育て世帯とシニアは、毎日のことの比重が大きい。
PLAY_SHARE = {"single": 0.4, "dinks": 0.4, "family": 0.3, "senior": 0.3}
FLAT = {"flat": 100, "some": 55, "hilly": 15}


def main():
    roster = json.load(open(os.path.join(ROOT, "data", "roster", "stations.json"), encoding="utf-8"))
    scores = json.load(open(os.path.join(ROOT, "data", "computed", "scores.json"), encoding="utf-8"))
    terrain = json.load(open(os.path.join(ROOT, "data", "computed", "terrain.json"), encoding="utf-8"))
    terrain = terrain.get("stations", terrain)

    # 1〜2. 広い公園と、駅から歩いて行ける範囲の面積
    parks = [p for p in load_p13() + load_extra() if p["area"] >= BIG_PARK_M2]
    green, green_names = {}, {}
    for st in roster:
        here = (st["lat"], st["lon"])
        # 同じ公園が、区画ごと・形の取り方ごとに複数登録されていることがある。
        # 名前ごとにいちばん大きいものだけを数える。
        by_name = {}
        for p in parks:
            if distance_m(here, p["at"]) <= WALK_M:
                by_name[p["name"]] = max(by_name.get(p["name"], 0), p["area"])
        total = sum(by_name.values())
        green[st["slug"]] = math.log1p(total / 10_000)   # ha の対数。広さの差を頭打ちにする
        green_names[st["slug"]] = sorted(by_name, key=by_name.get, reverse=True)[:3]
    outdoor_local = percentile(green)

    # 屋内で楽しめる場所の多さ。外食・カフェ・買い物の店の多さで見る。
    indoor_local = {}
    for st in roster:
        sc = scores.get(st["slug"], {})
        vals = [sc[a] for a in ("food", "cafe", "shopping") if a in sc]
        indoor_local[st["slug"]] = sum(vals) / len(vals) if vals else 0

    # 3. 全駅どうしの所要時間
    edges, _coords, names, station_lines = commutes.build_graph()
    by_group = {}
    for st in roster:
        by_group.setdefault(st["groupCode"], []).append(st["slug"])
    times = {}
    for st in roster:
        if st["groupCode"] not in names:
            continue
        res = commutes.dijkstra(edges, station_lines, st["groupCode"])
        times[st["slug"]] = {slug: (0 if slug == st["slug"] else res[g][0])
                             for g, slugs in by_group.items() if g in res for slug in slugs}

    # 4. 楽しみの点。行ける駅ごとに「魅力 × 時間の割引」を出し、上位の駅を行き先として残す。
    #    同じ公園を目当てにした隣どうしの駅が並ばないよう、主な公園が同じ駅は1つにまとめる。
    def reach(local, slug, key=None):
        cands = []
        for other, minutes in times.get(slug, {}).items():
            cands.append((local.get(other, 0) * max(0.0, 1 - minutes / REACH_ZERO_MIN), other, minutes))
        cands.sort(reverse=True)
        picked, seen = [], set()
        for value, other, minutes in cands:
            k = key(other) if key else other
            if k in seen:
                continue
            seen.add(k)
            picked.append((value, other, minutes))
            if len(picked) == 3:
                break
        return picked

    out = {}
    raw = {}
    for st in roster:
        slug = st["slug"]
        sc = dict(scores.get(slug, {}))
        sc["flat"] = FLAT.get((terrain.get(slug) or {}).get("slope"), 55)
        out_dest = reach(outdoor_local, slug,
                         key=lambda o: (green_names[o] or [o])[0])
        in_dest = reach(indoor_local, slug)
        play = {
            # アウトドア派: 近所に広い公園があるか（毎日の散歩や運動）と、電車で広い公園へ
            # 行きやすいか（休日）を半々で見る。ジムは駅の近くにあるかで見る。
            "outdoor": (0.45 * outdoor_local[slug] + 0.45 * out_dest[0][0]
                        + 0.1 * sc.get("fitness", 0)),
            # インドア派: 家で静かに過ごせるか（駅の点）と、屋内で楽しめる街へ行きやすいか。
            "indoor": 0.4 * sc.get("quietness", 50) + 0.6 * in_dest[0][0],
        }
        out[slug] = {
            # 公開するときに合わせる材料。いまの点には入れていない
            "commute": sc.get("commute"),
            "transitConvenience": sc.get("transitConvenience"),
            "rentLow": sc.get("rentLow"),
            "greenHa": round(math.expm1(green[slug]), 1),
            "greenParks": green_names[slug],
            "outdoorDest": [{"to": o, "minutes": round(mi), "parks": green_names[o]}
                            for _v, o, mi in out_dest],
            "indoorDest": [{"to": o, "minutes": round(mi)} for _v, o, mi in in_dest],
            "segments": {},
        }
        for persona, weights in LIFE_WEIGHTS.items():
            usable = {a: w for a, w in weights.items() if a in sc}
            life = sum(sc[a] * w for a, w in usable.items()) / sum(usable.values())
            for style, p in play.items():
                key = f"{persona}-{style}"
                raw.setdefault(key, {})[slug] = (1 - PLAY_SHARE[persona]) * life + PLAY_SHARE[persona] * p
                out[slug]["segments"][key] = {"life": round(life), "play": round(p)}

    # 5. 区分ごとに、駅どうしの相対的な位置にする
    for key, values in raw.items():
        pct = percentile(values)
        for slug, v in pct.items():
            out[slug]["segments"][key]["score"] = round(v)

    meta = {
        "note": "暮らし（駅のまわりで済むか）と楽しみ（電車で行ける駅まで含めて見る）を、"
                "層ごとの重みで合わせた点。通勤と家賃はまだ入れていない。楽しみは、行き先の魅力を所要時間で割り引く（45分で0）。"
                "方針は docs/18-persona-days.md。",
        "parkSources": [
            {"name": "国土数値情報 都市公園データ（P13、平成23年度）", "url": P13_URL},
            {"name": "OpenStreetMap（海上公園・国民公園の形）", "url": "https://www.openstreetmap.org/"},
        ],
    }
    json.dump({"meta": meta, "stations": out}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    open(OUT, "a", encoding="utf-8").write("\n")
    print(f"広い公園: {len(parks)}か所 / 駅: {len(out)} → {OUT}")


if __name__ == "__main__":
    main()
