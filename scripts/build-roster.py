#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掲載候補の全駅（ロースター）を再生成する。

出力:
  data/reference/lines.json   路線マスタ
  data/roster/stations.json   対象路線の23区内の全駅

出典と方針は docs/09-station-roster.md を参照。
標準ライブラリのみで動く。

  python3 scripts/build-roster.py
"""
import collections
import csv
import io
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "roster")

EKIDATA_API = "https://raw.githubusercontent.com/ny-a/ekidata/gh-pages/api"
ODPT_STATIONS = (
    "https://raw.githubusercontent.com/piuccio/open-data-jp-railway-stations"
    "/master/stations.json"
)
ADDRESSES = (
    "https://raw.githubusercontent.com/geolonia/japanese-addresses"
    "/master/data/latest.csv"
)

# 対象路線。ここが「どの駅を洗うか」の定義そのもの。
# 都営4線 + 都電荒川線 + 日暮里舎人 / 東京メトロ9線 / JR山手・中央快速・中央総武 /
# 23区を通る私鉄各線。
TARGET_LINES = [
    "99301", "99302", "99303", "99304", "99305", "99342",
    "28001", "28002", "28003", "28004", "28005", "28006", "28008", "28009", "28010",
    "11302", "11312", "11313",
    "21001", "21002", "21005", "21006",
    "22001", "22003", "22004", "22007",
    "23001", "23002", "23003",
    "24001", "24006", "24007",
    "25001",
    "26001", "26002", "26003", "26004", "26005", "26006", "26007",
    "27001", "27002",
    "99307", "99309", "99311", "99336", "99337", "99340",
]

# 路線の英語名と事業者区分。ekidata は日本語名しか持たないため手で対応させる。
LINE_EN = {
    "11301": ("JR Tokaido Line", "jr"),
    "11302": ("JR Yamanote Line", "jr"),
    "11308": ("JR Yokosuka Line", "jr"),
    "11311": ("JR Chuo Main Line", "jr"),
    "11312": ("JR Chuo Rapid Line", "jr"),
    "11313": ("JR Chuo-Sobu Line (Local)", "jr"),
    "11314": ("JR Sobu Main Line", "jr"),
    "11319": ("JR Utsunomiya Line", "jr"),
    "11320": ("JR Joban Line", "jr"),
    "11321": ("JR Saikyo Line", "jr"),
    "11323": ("JR Takasaki Line", "jr"),
    "11326": ("JR Keiyo Line", "jr"),
    "11328": ("Narita Express", "jr"),
    "11332": ("JR Keihin-Tohoku Line", "jr"),
    "11333": ("JR Shonan-Shinjuku Line", "jr"),
    "11343": ("JR Ueno-Tokyo Line", "jr"),
    "21001": ("Tobu Tojo Line", "private"),
    "21002": ("Tobu Skytree Line", "private"),
    "21005": ("Tobu Kameido Line", "private"),
    "21006": ("Tobu Daishi Line", "private"),
    "22001": ("Seibu Ikebukuro Line", "private"),
    "22003": ("Seibu Yurakucho Line", "private"),
    "22004": ("Seibu Toshima Line", "private"),
    "22007": ("Seibu Shinjuku Line", "private"),
    "23001": ("Keisei Main Line", "private"),
    "23002": ("Keisei Oshiage Line", "private"),
    "23003": ("Keisei Kanamachi Line", "private"),
    "23006": ("Narita Sky Access Line", "private"),
    "24001": ("Keio Line", "private"),
    "24006": ("Keio Inokashira Line", "private"),
    "24007": ("Keio New Line", "private"),
    "25001": ("Odakyu Odawara Line", "private"),
    "26001": ("Tokyu Toyoko Line", "private"),
    "26002": ("Tokyu Meguro Line", "private"),
    "26003": ("Tokyu Den-en-toshi Line", "private"),
    "26004": ("Tokyu Oimachi Line", "private"),
    "26005": ("Tokyu Ikegami Line", "private"),
    "26006": ("Tokyu Tamagawa Line", "private"),
    "26007": ("Tokyu Setagaya Line", "private"),
    "27001": ("Keikyu Main Line", "private"),
    "27002": ("Keikyu Airport Line", "private"),
    "28001": ("Tokyo Metro Ginza Line", "tokyo-metro"),
    "28002": ("Tokyo Metro Marunouchi Line", "tokyo-metro"),
    "28003": ("Tokyo Metro Hibiya Line", "tokyo-metro"),
    "28004": ("Tokyo Metro Tozai Line", "tokyo-metro"),
    "28005": ("Tokyo Metro Chiyoda Line", "tokyo-metro"),
    "28006": ("Tokyo Metro Yurakucho Line", "tokyo-metro"),
    "28008": ("Tokyo Metro Hanzomon Line", "tokyo-metro"),
    "28009": ("Tokyo Metro Namboku Line", "tokyo-metro"),
    "28010": ("Tokyo Metro Fukutoshin Line", "tokyo-metro"),
    "99301": ("Toei Oedo Line", "toei"),
    "99302": ("Toei Asakusa Line", "toei"),
    "99303": ("Toei Mita Line", "toei"),
    "99304": ("Toei Shinjuku Line", "toei"),
    "99305": ("Tokyo Sakura Tram (Toden Arakawa Line)", "toei"),
    "99307": ("Saitama Railway Line", "private"),
    "99309": ("Tsukuba Express", "private"),
    "99311": ("Yurikamome", "private"),
    "99336": ("Tokyo Monorail", "private"),
    "99337": ("Rinkai Line", "private"),
    "99340": ("Hokuso Line", "private"),
    "99342": ("Nippori-Toneri Liner", "toei"),
}

# ODPT の駅コードが無くローマ字が引けない駅。東急各線と一部の新駅・支線。
ROMAJI_FIX = {
    "高輪ゲートウェイ": "Takanawa-Gateway", "代官山": "Daikanyama", "祐天寺": "Yutenji",
    "学芸大学": "Gakugei-daigaku", "都立大学": "Toritsu-daigaku", "自由が丘": "Jiyugaoka",
    "田園調布": "Den-en-chofu", "多摩川": "Tamagawa", "不動前": "Fudo-mae",
    "武蔵小山": "Musashi-koyama", "西小山": "Nishi-koyama", "洗足": "Senzoku",
    "大岡山": "Ookayama", "奥沢": "Okusawa", "池尻大橋": "Ikejiri-ohashi",
    "三軒茶屋": "Sangen-jaya", "駒沢大学": "Komazawa-daigaku", "桜新町": "Sakura-shimmachi",
    "用賀": "Yoga", "二子玉川": "Futako-tamagawa", "下神明": "Shimo-shimmei",
    "戸越公園": "Togoshi-koen", "荏原町": "Ebara-machi", "旗の台": "Hatanodai",
    "北千束": "Kita-senzoku", "緑が丘": "Midorigaoka", "九品仏": "Kuhombutsu",
    "尾山台": "Oyamadai", "等々力": "Todoroki", "上野毛": "Kaminoge",
    "大崎広小路": "Osaki-hirokoji", "荏原中延": "Ebara-nakanobu", "長原": "Nagahara",
    "洗足池": "Senzoku-ike", "石川台": "Ishikawadai", "雪が谷大塚": "Yukigaya-otsuka",
    "御嶽山": "Ontakesan", "久が原": "Kugahara", "千鳥町": "Chidoricho", "池上": "Ikegami",
    "蓮沼": "Hasunuma", "沼部": "Numabe", "鵜の木": "Unoki", "下丸子": "Shimomaruko",
    "武蔵新田": "Musashi-nitta", "矢口渡": "Yaguchi-no-watashi", "西太子堂": "Nishi-taishido",
    "若林": "Wakabayashi", "松陰神社前": "Shoin-jinja-mae", "世田谷": "Setagaya",
    "上町": "Kamimachi", "宮の坂": "Miyanosaka", "松原": "Matsubara",
    "青井": "Aoi", "六町": "Rokucho", "大井競馬場前": "Oi-keibajo-mae",
    "流通センター": "Ryutsu-center", "昭和島": "Showajima", "整備場": "Seibijo",
    "新整備場": "Shin-seibijo",
}

# 詳細プロフィールの slug に合わせる（作成済みの URL を変えないため）。
SLUG_OVERRIDE = {"西馬込": "nishimagome", "中目黒": "nakameguro"}

# 同名の別駅。ekidata の駅グループコードで区別する。
SLUG_BY_GROUP = {"9930530": "waseda-toden", "9930903": "asakusa-tx"}

# 区境に建つ駅。最近傍の町丁だけでは決まらないので、駅の所在地表記に合わせる。
WARD_OVERRIDE = {
    "目黒": ("13109", "品川区", "shinagawa"),
    "御茶ノ水": ("13101", "千代田区", "chiyoda"),
    "水道橋": ("13101", "千代田区", "chiyoda"),
    "市ケ谷": ("13101", "千代田区", "chiyoda"),
    "飯田橋": ("13101", "千代田区", "chiyoda"),
    "自由が丘": ("13110", "目黒区", "meguro"),
    "新大塚": ("13105", "文京区", "bunkyo"),
}

# ekidata は隣接・連絡する駅を1つの駅グループにまとめている（有楽町と日比谷など）。
# 「どの街に住むか」を決める用途では同じ場所として扱ってよいが、表示名は
# 通りの良い方に寄せる。
NAME_OVERRIDE = {"2100110": "成増"}


def fetch(url, name):
    """取得結果は .cache に置く。再実行のたびに数十MBを落とさないため。"""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print(f"  download {name}", file=sys.stderr)
        with urllib.request.urlopen(url, timeout=120) as res, open(path, "wb") as f:
            f.write(res.read())
    return path


def split_words(romaji):
    """ODPT のローマ字は Naka-meguro と NakaMeguro が混在するので語に割る。"""
    t = romaji.replace("ō", "o").replace("ū", "u").replace("'", "")
    t = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", t)
    return [w for w in re.split(r"[^A-Za-z0-9]+", t) if w]


def build_ward_index():
    """
    町丁の代表点から最寄りの市区町村を引く索引。

    区の境界ポリゴンを使う方法は、入手できる簡略化データだと江東区・江戸川区の
    形が崩れていて使えなかった。町丁点の最近傍なら、隣接する市部と取り違えない。
    """
    path = fetch(ADDRESSES, "addresses.csv")
    buckets = collections.defaultdict(list)
    prefs = {"東京都", "埼玉県", "千葉県", "神奈川県"}
    with io.open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["都道府県名"] not in prefs:
                continue
            try:
                lat, lon = float(row["緯度"]), float(row["経度"])
            except (ValueError, TypeError):
                continue
            buckets[round(lat, 2)].append(
                (lon, lat, row["市区町村コード"], row["市区町村名"], row["市区町村名ローマ字"])
            )
    return buckets


def nearest_municipality(buckets, lon, lat):
    best = None
    for i in range(-3, 4):
        for p in buckets.get(round(round(lat, 2) + i * 0.01, 2), ()):
            dx, dy = (p[0] - lon) * 91.0, (p[1] - lat) * 111.0
            d = dx * dx + dy * dy
            if best is None or d < best[0]:
                best = (d, p[2], p[3], p[4])
    return best


def main():
    print("出典データを取得中...", file=sys.stderr)
    line_master = json.load(
        open(fetch(f"{EKIDATA_API}/p/13.json", "tokyo_lines.json"), encoding="utf-8")
    )["line"]
    line_names = {str(l["line_cd"]): l["line_name"] for l in line_master}

    odpt = json.load(open(fetch(ODPT_STATIONS, "odpt_stations.json"), encoding="utf-8"))
    by_group = {g["group_code"]: g for g in odpt}
    # ekidata の駅グループは連絡駅をまとめている（三越前と新日本橋など）ので、
    # グループの先頭から機械的に取るとローマ字が別の駅のものになる。
    # 駅名が一致するものを優先して引く。
    romaji_by_id = {}
    romaji_by_name = {}
    for g in odpt:
        for s in g["stations"]:
            if not s.get("code"):
                continue
            tail = s["code"].split(".")[-1]
            romaji_by_id[s["ekidata_id"]] = tail
            romaji_by_name.setdefault(s["name_kanji"], tail)

    stations, membership = {}, collections.defaultdict(set)
    for line_cd in TARGET_LINES:
        data = json.load(
            open(fetch(f"{EKIDATA_API}/l/{line_cd}.json", f"line_{line_cd}.json"),
                 encoding="utf-8")
        )
        for s in data["station_l"]:
            gcd = str(s["station_g_cd"])
            # 同じ駅でも路線ごとに座標が少しずれる。どの路線を先に読んだかで
            # 区の判定が揺れるため、全路線の平均を代表点にする。
            stations.setdefault(gcd, {"name": s["station_name"], "points": []})
            stations[gcd]["points"].append((s["lat"], s["lon"]))
            membership[gcd].add(line_cd)

    buckets = build_ward_index()

    rows, outside, seen = [], 0, collections.Counter()
    used_romaji_fix, used_ward_override = set(), set()
    used_slug_override, used_name_override = set(), set()
    for gcd, entry in sorted(stations.items()):
        group = by_group.get(gcd)
        # 駅グループの代表名は全国データ側を正とする。路線ファイルから拾うと、
        # どの路線を先に読んだかで名前が変わり、ローマ字とずれる。
        name = NAME_OVERRIDE.get(gcd) or (group["name_kanji"] if group else entry["name"])
        if gcd in NAME_OVERRIDE:
            used_name_override.add(gcd)
        pts = entry["points"]
        lat = round(sum(p[0] for p in pts) / len(pts), 6)
        lon = round(sum(p[1] for p in pts) / len(pts), 6)

        override = WARD_OVERRIDE.get(name)
        if override:
            used_ward_override.add(name)
            code, ward_ja, ward_roma = override[0], override[1], override[2]
        else:
            found = nearest_municipality(buckets, lon, lat)
            if not found:
                outside += 1
                continue
            _, code, ward_ja, ward_roma = found
            ward_roma = ward_roma.lower().replace(" ", "-").replace("-ku", "")
        if not (code.startswith("131") and 13101 <= int(code) <= 13123):
            outside += 1  # 23区外は対象外
            continue

        # 全国データにある全路線と、対象路線での所属を合わせる。
        # 開業が新しい駅は全国データのスナップショットに載っていないことがある。
        ids = set(membership[gcd])
        if group:
            ids |= {i for i in group["ekidata_line_ids"] if i in line_names}

        raw = romaji_by_name.get(name, "")
        if not raw and group:
            for s in group["stations"]:
                if romaji_by_id.get(s["ekidata_id"]):
                    raw = romaji_by_id[s["ekidata_id"]]
                    break
        if not raw and name in ROMAJI_FIX:
            raw = ROMAJI_FIX[name]
            used_romaji_fix.add(name)
        if not raw:
            raise SystemExit(f"ローマ字が引けません: {name} ({gcd})。ROMAJI_FIX に追加してください。")

        words = split_words(raw)
        if name in SLUG_OVERRIDE:
            used_slug_override.add(name)
        slug = (SLUG_BY_GROUP.get(gcd) or SLUG_OVERRIDE.get(name)
                or "-".join(w.lower() for w in words))
        seen[slug] += 1
        if seen[slug] > 1:
            raise SystemExit(f"slug が重複しました: {slug} ({name} / {gcd})。"
                             " SLUG_BY_GROUP で区別してください。")

        rows.append({
            "slug": slug,
            "nameJa": name,
            "nameRomaji": "-".join(w[:1].upper() + w[1:].lower() for w in words),
            "ward": ward_roma,
            "wardCode": code,
            "wardNameJa": ward_ja,
            "lat": lat,
            "lon": lon,
            "lineIds": sorted(ids),
        })

    # 効いていない上書き設定は、駅名の表記ゆれで黙って無視されている疑いがある。
    for label, table, used in (
        ("ROMAJI_FIX", ROMAJI_FIX, used_romaji_fix),
        ("WARD_OVERRIDE", WARD_OVERRIDE, used_ward_override),
        ("SLUG_OVERRIDE", SLUG_OVERRIDE, used_slug_override),
        ("NAME_OVERRIDE", NAME_OVERRIDE, used_name_override),
        ("SLUG_BY_GROUP", SLUG_BY_GROUP, set(SLUG_BY_GROUP) & set(stations)),
    ):
        unused = sorted(set(table) - set(used))
        if unused:
            raise SystemExit(
                f"{label} の以下のキーが一度も使われませんでした（表記ゆれの可能性）: {unused}"
            )

    rows.sort(key=lambda r: (r["wardCode"], r["nameJa"]))

    used = sorted({i for r in rows for i in r["lineIds"]})
    lines_out = [
        {"id": i, "nameJa": line_names[i], "nameEn": LINE_EN[i][0], "operator": LINE_EN[i][1]}
        for i in used
    ]

    os.makedirs(os.path.join(ROOT, "data", "reference"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "data", "roster"), exist_ok=True)
    for path, payload in (
        (os.path.join(ROOT, "data", "reference", "lines.json"), lines_out),
        (os.path.join(ROOT, "data", "roster", "stations.json"), rows),
    ):
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")

    wards = collections.Counter(r["wardNameJa"] for r in rows)
    print(f"\n路線 {len(lines_out)} / 23区内の駅 {len(rows)} / 対象外として除外 {outside}")
    print(f"区: {len(wards)}")
    for k, v in sorted(wards.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
