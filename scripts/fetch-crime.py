#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅のまわりの犯罪の認知件数を、警視庁の町丁別データから出す。

出力: data/computed/crime.json

なぜ要るのか。
  新大久保のファミリー適性が全458駅中75点に出ていた。駅から1,500m以内に
  小中学校が40校あり、保育園と幼稚園が16園あり、地形も平坦だからである。
  数字はどれも正しいが、そこが歓楽街であることをまったく拾えていない。
  店の数も乗降客数も、歓楽街かどうかを区別できなかった
  （docs/03-scoring.md §4.5）。

  警視庁は、町丁ごとの犯罪の認知件数を毎年公表している。
  駅から800m以内の町丁で、粗暴犯（暴行・傷害・脅迫・恐喝）の
  1町丁あたりの件数を出すと、新大久保は36.2件、荻窪は2.5件になる。
  14倍の開きがあり、歓楽街と住宅地をはっきり分ける。

  認知件数は、そこに住む人が被害に遭う確率そのものではない。
  繁華街では、そこで働く人・遊びに来た人が巻き込まれた件も同じ町丁に数える。
  それでも「駅前がどういう場所か」を測る物差しとしては、
  OpenStreetMap の店の数よりはるかに安定している。

やっていること。
  1. 警視庁の町丁別認知件数（CSV）を取る
  2. 国土交通省の位置参照情報から、町丁目ごとの緯度経度を取る
  3. 町丁名を突き合わせ、駅から800m以内の町丁の件数を合計する

  python3 scripts/fetch-crime.py
"""
import csv
import io
import json
import math
import os
import re
import unicodedata
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "data", "poi")
OUT = os.path.join(ROOT, "data", "computed", "crime.json")

# 令和7年（2025年）の確定値。年が変わったら YEAR を上げる。
YEAR = "R7"
CRIME_URL = ("https://www.keishicho.metro.tokyo.lg.jp/about_mpd/jokyo_tokei/"
             f"jokyo/ninchikensu.files/{YEAR}.csv")
CRIME_PAGE = ("https://www.keishicho.metro.tokyo.lg.jp/about_mpd/jokyo_tokei/"
              "jokyo/ninchikensu.html")
# 大字・町丁目レベル位置参照情報（令和6年度版）
ISJ_URL = "https://nlftp.mlit.go.jp/isj/dls/data/19.0b/13000-19.0b.zip"
ISJ_PAGE = "https://nlftp.mlit.go.jp/isj/"

RADIUS_M = 800

# 使う分類。CSV の見出しと同じ名前で引く。
COLUMNS = {
    "total": "総合計",
    "violent": "粗暴犯計",
    "felony": "凶悪犯計",
    "burglary": "侵入窃盗計",
}

KANJI_DIGITS = "〇一二三四五六七八九"


def log(msg):
    print(msg, flush=True)


def fetch(url, filename):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        return path
    os.makedirs(CACHE_DIR, exist_ok=True)
    log(f"ダウンロード: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "TokyoLivingCompass/1.0"})
    with urllib.request.urlopen(req, timeout=300) as res, open(path, "wb") as f:
        while chunk := res.read(1 << 20):
            f.write(chunk)
    return path


def kanji_to_number(text):
    """「飯田橋一丁目」の漢数字を算用数字に直す。位置参照情報は漢数字で書く。"""
    m = re.search(r"([〇一二三四五六七八九十]+)丁目$", text)
    if not m:
        return text
    k = m.group(1)
    if "十" in k:
        head, _, tail = k.partition("十")
        value = (KANJI_DIGITS.index(head) if head else 1) * 10
        value += KANJI_DIGITS.index(tail) if tail else 0
    elif len(k) == 1:
        value = KANJI_DIGITS.index(k)
    else:
        value = int("".join(str(KANJI_DIGITS.index(c)) for c in k))
    return text[:m.start()] + str(value) + "丁目"


def normalize(name):
    """町丁名の表記ゆれを吸収する。警視庁は全角数字、位置参照情報は漢数字。"""
    name = unicodedata.normalize("NFKC", name)
    name = kanji_to_number(name)
    name = re.sub(r"(\d+)丁目$", r"\1", name)
    return name.replace("ケ", "ヶ").replace("が", "ヶ")


def load_centroids():
    """町丁目ごとの代表点（緯度経度）を読む。"""
    path = fetch(ISJ_URL, "isj-13000.zip")
    with zipfile.ZipFile(path) as z:
        csv_name = next(n for n in z.namelist() if n.endswith(".csv"))
        rows = list(csv.reader(io.StringIO(z.read(csv_name).decode("cp932"))))
    centroids = {}
    for row in rows[1:]:
        ward, name, lat, lon = row[3], row[5], row[6], row[7]
        centroids[ward + normalize(name)] = (float(lat), float(lon))
    log(f"町丁目の代表点: {len(centroids):,} 件")
    return centroids


def load_crime(centroids):
    """町丁ごとの認知件数を読み、代表点と突き合わせる。"""
    path = fetch(CRIME_URL, f"keishicho-{YEAR}.csv")
    with open(path, encoding="cp932") as f:
        rows = list(csv.reader(f))
    header = {h: i for i, h in enumerate(rows[0])}
    for label in COLUMNS.values():
        if label not in header:
            raise SystemExit(f"警視庁のCSVに「{label}」の列がありません")

    places = []
    unmatched = []
    for row in rows[1:]:
        m = re.match(r"^(.+?[区市町村])(.+)$", row[0])
        if not m:
            continue
        key = m.group(1) + normalize(m.group(2))
        if key not in centroids:
            unmatched.append(row[0])
            continue
        lat, lon = centroids[key]
        counts = {k: int(row[header[label]] or 0) for k, label in COLUMNS.items()}
        places.append((lat, lon, counts))
    log(f"町丁: {len(rows) - 1:,} 件、代表点と突き合わせられた: {len(places):,} 件")
    if unmatched:
        log(f"  突き合わせられなかった町丁: {len(unmatched)} 件"
            f"（例: {'、'.join(unmatched[:5])}）")
    return places


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

    places = load_crime(load_centroids())

    out = {}
    for st in stations:
        lat, lon = st["lat"], st["lon"]
        m_per_lon = 111_320.0 * math.cos(math.radians(lat))
        totals = {k: 0 for k in COLUMNS}
        found = 0
        for plat, plon, counts in places:
            dy = (plat - lat) * 111_132.0
            dx = (plon - lon) * m_per_lon
            if dy * dy + dx * dx > RADIUS_M * RADIUS_M:
                continue
            found += 1
            for k in COLUMNS:
                totals[k] += counts[k]
        if found == 0:
            continue
        out[st["slug"]] = {
            "places": found,
            "counts": totals,
            # 町丁の数は駅によって違うので、1町丁あたりに直してから比べる
            "perPlace": {k: round(v / found, 2) for k, v in totals.items()},
        }

    log(f"駅: {len(out)} / {len(stations)}")
    payload = {
        "meta": {
            "source": f"警視庁 市区町丁別 犯罪認知件数（{YEAR}）",
            "sourceUrl": CRIME_PAGE,
            "centroidSource": "国土交通省 大字・町丁目レベル位置参照情報（令和6年度版）",
            "centroidSourceUrl": ISJ_PAGE,
            "radiusM": RADIUS_M,
            "note": "駅から800m以内に代表点がある町丁の認知件数を合計し、1町丁あたりに直した",
        },
        "stations": out,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log(f"書き出した: {OUT}")


if __name__ == "__main__":
    main()
