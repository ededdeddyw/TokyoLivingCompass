#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅のまわりの用途地域を、国土数値情報 A29「用途地域」から出す。

出力: data/computed/zoning.json

なぜ要るのか。
  店の数（OpenStreetMap）は、区によって登録の細かさが20倍以上違う
  （docs/03-scoring.md §4.4）。乗降客数で補おうとしたが、乗降客数は
  駅を通り抜ける人の数であって、駅前がどういう街かを表さない。
  荻窪は1日21万人が乗り降りするが駅のすぐ外は住宅地で、
  新大久保は7万人だが駅前は商業地域である。この2駅を、
  店の数と乗降客数だけでは区別できなかった。

  用途地域は都市計画法にもとづいて区が定めたもので、
  地図を作った人の多さに左右されない。駅から500m以内の面積のうち
  商業地域が何割か、低層住居専用地域が何割かを出せば、
  その駅前がどういう街として計画されているかが分かる。

やっていること。
  1. 国土数値情報から東京都の A29 をダウンロードする（約45MB）
  2. 23区ぶんのシェープファイルを読む（標準ライブラリだけで読む）
  3. 駅ごとに半径500mの円の中に25m間隔の格子点を置き、
     各点がどの用途地域に入るかを数えて面積の割合に直す

  python3 scripts/fetch-zoning.py
"""
import json
import math
import os
import struct
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "poi", "A29-19_13_GML.zip")
OUT = os.path.join(ROOT, "data", "computed", "zoning.json")
URL = "https://nlftp.mlit.go.jp/ksj/gml/data/A29/A29-19/A29-19_13_GML.zip"
PAGE = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A29-v2_1.html"

RADIUS_M = 500
GRID_M = 25

# 都市計画法の用途地域。A29_004 の値。
ZONE_NAMES = {
    1: "第一種低層住居専用地域",
    2: "第二種低層住居専用地域",
    3: "第一種中高層住居専用地域",
    4: "第二種中高層住居専用地域",
    5: "第一種住居地域",
    6: "第二種住居地域",
    7: "準住居地域",
    8: "近隣商業地域",
    9: "商業地域",
    10: "準工業地域",
    11: "工業地域",
    12: "工業専用地域",
    21: "田園住居地域",
}

# 13の区分をそのまま持つと使う側が扱いきれないので、4つにまとめた値も出す。
GROUPS = {
    "commercial": (9,),            # 商業地域。繁華街・オフィス街になる
    "nearCommercial": (8,),        # 近隣商業地域。商店街になる
    "lowRise": (1, 2, 3, 21),      # 低層・中高層の住居専用地域。住宅地になる
    "residential": (4, 5, 6, 7),   # そのほかの住居系
    "industrial": (10, 11, 12),    # 工業系
}


def log(msg):
    print(msg, flush=True)


def download():
    if os.path.exists(CACHE):
        return
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    log(f"ダウンロード: {URL}")
    with urllib.request.urlopen(URL, timeout=900) as res, open(CACHE, "wb") as f:
        while chunk := res.read(1 << 20):
            f.write(chunk)
    log(f"保存: {CACHE}（{os.path.getsize(CACHE):,} バイト）")


def read_dbf(data):
    """シェープファイルに付く属性表（.dbf）を読む。文字コードは CP932。"""
    count, header_len, record_len = struct.unpack_from("<IHH", data, 4)
    fields = []
    off = 32
    while data[off] != 0x0D:
        name = data[off:off + 11].split(b"\0")[0].decode("cp932")
        fields.append((name, data[off + 16]))
        off += 32
    rows = []
    for i in range(count):
        rec = data[header_len + i * record_len: header_len + (i + 1) * record_len]
        pos = 1
        row = {}
        for name, length in fields:
            row[name] = rec[pos:pos + length].decode("cp932").strip()
            pos += length
        rows.append(row)
    return rows


def read_shp_polygons(data):
    """ポリゴン（シェープタイプ5）だけを読み、環の並びとして返す。"""
    polygons = []
    pos = 100
    end = len(data)
    while pos < end:
        _, content_words = struct.unpack_from(">II", data, pos)
        body = pos + 8
        shape_type = struct.unpack_from("<i", data, body)[0]
        if shape_type == 5:
            xmin, ymin, xmax, ymax = struct.unpack_from("<4d", data, body + 4)
            part_count, point_count = struct.unpack_from("<2i", data, body + 36)
            parts = struct.unpack_from(f"<{part_count}i", data, body + 44)
            coords_at = body + 44 + part_count * 4
            coords = struct.unpack_from(f"<{point_count * 2}d", data, coords_at)
            rings = []
            for i, start in enumerate(parts):
                stop = parts[i + 1] if i + 1 < part_count else point_count
                rings.append([(coords[j * 2], coords[j * 2 + 1])
                              for j in range(start, stop)])
            polygons.append({"box": (xmin, ymin, xmax, ymax), "rings": rings})
        else:
            polygons.append(None)
        pos = body + content_words * 2
    return polygons


def in_rings(x, y, rings):
    """環の交差回数で内外を判定する。穴の環も同じ数え方で正しく抜ける。"""
    inside = False
    for ring in rings:
        n = len(ring)
        j = n - 1
        for i in range(n):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > y) != (yj > y):
                if x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
            j = i
    return inside


def load_zones():
    """23区ぶんのポリゴンと用途地域コードを読む。"""
    download()
    zones = []
    with zipfile.ZipFile(CACHE) as z:
        # 区ごとのファイルは杉並区と豊島区が入っていない。23区の用途地域は
        # 東京都が決めるもので、都の決定ぶんをまとめた 13000 が23区全体を覆う。
        shp_names = [n for n in z.namelist() if n.endswith("_13000.shp")]
        if not shp_names:
            raise SystemExit("A29 の 13000 のシェープファイルが見つかりません")
        for shp_name in shp_names:
            polygons = read_shp_polygons(z.read(shp_name))
            rows = read_dbf(z.read(shp_name[:-4] + ".dbf"))
            if len(polygons) != len(rows):
                raise SystemExit(f"{shp_name}: 図形と属性の数が合いません")
            for poly, row in zip(polygons, rows):
                if poly is None:
                    continue
                try:
                    zone = int(row["A29_004"])
                except ValueError:
                    continue
                zones.append({
                    "box": poly["box"],
                    "rings": poly["rings"],
                    "zone": zone,
                    "far": int(row["A29_007"]) if row["A29_007"] else None,
                })
    log(f"用途地域の区画: {len(zones):,} 件")
    return zones


def build_index(zones, cell=0.004):
    """外接矩形をもとにした格子の索引。1件ずつ総当たりすると終わらない。"""
    index = {}
    for i, z in enumerate(zones):
        xmin, ymin, xmax, ymax = z["box"]
        for gx in range(int(xmin / cell), int(xmax / cell) + 1):
            for gy in range(int(ymin / cell), int(ymax / cell) + 1):
                index.setdefault((gx, gy), []).append(i)
    return index, cell


def main():
    roster_dir = os.path.join(ROOT, "data", "roster")
    stations = []
    for name in sorted(os.listdir(roster_dir)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(roster_dir, name), encoding="utf-8") as f:
            data = json.load(f)
        rows = data if isinstance(data, list) else data.get("stations", [])
        for s in rows:
            if isinstance(s, dict) and "slug" in s and "lat" in s:
                stations.append(s)
    log(f"駅: {len(stations)} 件")

    zones = load_zones()
    index, cell = build_index(zones)

    out = {}
    for n, st in enumerate(stations, 1):
        lat, lon = st["lat"], st["lon"]
        # 東京の緯度では、経度1度あたりの距離が緯度より短い。
        m_per_lat = 111_132.0
        m_per_lon = 111_320.0 * math.cos(math.radians(lat))
        steps = int(RADIUS_M / GRID_M)

        counts = {}
        far_sum = 0.0
        far_n = 0
        total = 0
        for i in range(-steps, steps + 1):
            for j in range(-steps, steps + 1):
                dx, dy = i * GRID_M, j * GRID_M
                if dx * dx + dy * dy > RADIUS_M * RADIUS_M:
                    continue
                total += 1
                x = lon + dx / m_per_lon
                y = lat + dy / m_per_lat
                hit = None
                for k in index.get((int(x / cell), int(y / cell)), ()):
                    z = zones[k]
                    xmin, ymin, xmax, ymax = z["box"]
                    if not (xmin <= x <= xmax and ymin <= y <= ymax):
                        continue
                    if in_rings(x, y, z["rings"]):
                        hit = z
                        break
                if hit is None:
                    continue
                counts[hit["zone"]] = counts.get(hit["zone"], 0) + 1
                if hit["far"]:
                    far_sum += hit["far"]
                    far_n += 1

        covered = sum(counts.values())
        shares = {ZONE_NAMES.get(z, str(z)): round(c / total, 4)
                  for z, c in sorted(counts.items())}
        groups = {g: round(sum(counts.get(z, 0) for z in codes) / total, 4)
                  for g, codes in GROUPS.items()}
        out[st["slug"]] = {
            "shares": shares,
            "groups": groups,
            # 用途地域の指定が無い面（線路・河川・公園など）を除いた割合
            "covered": round(covered / total, 4),
            # 容積率の平均。商業地域ほど大きい
            "far": round(far_sum / far_n) if far_n else None,
        }
        if n % 50 == 0:
            log(f"  {n}/{len(stations)}")

    payload = {
        "meta": {
            "source": "国土数値情報 A29 用途地域（平成31年）",
            "sourceUrl": PAGE,
            "radiusM": RADIUS_M,
            "gridM": GRID_M,
            "note": "半径500mの円を25m間隔の格子点で埋め、各点の用途地域を数えた面積の割合",
        },
        "stations": out,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log(f"書き出した: {OUT}")


if __name__ == "__main__":
    main()
