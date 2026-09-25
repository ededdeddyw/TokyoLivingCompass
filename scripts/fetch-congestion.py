#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路線ごとの朝の混雑率を、国土交通省の調査結果から取る。

  python3 scripts/fetch-congestion.py

「東西線は朝が混む」と書いても、どれくらい混むのかが読み手に伝わらない。
国土交通省は毎年度、通勤通学の時間帯の混雑率を区間ごとに公表している。
これを路線ごとに持てば、「東西線の最混雑区間は木場から門前仲町で160%」と書ける。

混雑率の目安は国土交通省の定義による。
  100% … 座席が埋まり、立っている人がつり革や手すりをつかめる
  150% … 肩が触れ合うが、新聞を広げて読める
  180% … 折りたたむなど無理をすれば新聞を読める
  200% … 体が触れ合い、相当な圧迫感がある

出典: 国土交通省「都市鉄道の混雑率調査結果」（令和7年度実績、令和8年7月28日公表）
      https://www.mlit.go.jp/report/press/tetsudo04_hh_000139.html
出力: data/computed/congestion.json
"""
import collections
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "poi", "congestion")
OUT = os.path.join(ROOT, "data", "computed", "congestion.json")
PRESS = "https://www.mlit.go.jp/report/press/tetsudo04_hh_000139.html"
YEAR = "2025"       # 令和7年度実績
# 資料2 は三大都市圏の主要区間、資料3 は全国の路線ごとの最混雑区間。
PDFS = {
    "主要区間": "https://www.mlit.go.jp/report/press/content/002015141.pdf",
    "最混雑区間": "https://www.mlit.go.jp/report/press/content/002015142.pdf",
}

# 表の列は x 座標で分かれている。駅名は列の幅に合わせて字間を広げて置かれるため、
# 字と字の間より、列と列の間のほうが狭い。桁ではなく座標で切る。
X_OPERATOR, X_LINE, X_SECTION = 105.0, 178.0, 300.0
X_TIME, X_CAPACITY, X_RIDERS, X_RATE = 355.0, 450.0, 495.0, 540.0

# 区間から路線を決める表。
#
# PDF の「線名」の列は、複数の行にまたがるセルが縦方向の中央に置かれている。
# そのため行ごとに読むと1行ずれ、東西線の区間に「丸ノ内」という線名が付く。
# 線名の文字は使わず、区間から路線を決める。同じ2駅に複数の路線が通る区間は、
# 公表資料の並び順を人が読んで、この表に書いた。
SECTION_LINES = {
    # JR
    ("上野", "御徒町"): "11302",            # 山手線（外回り）
    ("新大久保", "新宿"): "11302",           # 山手線（内回り）
    ("中野", "新宿"): "11312",              # 中央線（快速）
    ("代々木", "千駄ヶ谷"): "11313",          # 中央・総武線（緩行）
    ("新小岩", "錦糸町"): "11314",           # 総武本線（快速）
    ("錦糸町", "両国"): "11313",            # 中央・総武線（緩行）
    ("三河島", "日暮里"): "11320",           # 常磐線（快速）
    ("亀有", "綾瀬"): "11320",              # 常磐線（緩行）
    ("大井町", "品川"): "11332",            # 京浜東北線
    ("川口", "赤羽"): "11332",              # 京浜東北線
    ("板橋", "池袋"): "11321",              # 埼京線
    ("葛西臨海公園", "新木場"): "11326",       # 京葉線
    ("川崎", "品川"): "11301",              # 東海道本線
    ("武蔵小杉", "西大井"): "11308",          # 横須賀線
    ("宮原", "大宮"): "11323",              # 高崎線
    ("土呂", "大宮"): "11319",              # 宇都宮線
    # 東京メトロ
    ("三ノ輪", "入谷"): "28003",            # 日比谷線
    ("赤坂見附", "溜池山王"): "28001",        # 銀座線
    ("新大塚", "茗荷谷"): "28002",           # 丸ノ内線
    ("四ツ谷", "赤坂見附"): "28002",          # 丸ノ内線
    ("木場", "門前仲町"): "28004",           # 東西線
    ("高田馬場", "早稲田"): "28004",          # 東西線
    ("町屋", "西日暮里"): "28005",           # 千代田線
    ("東池袋", "護国寺"): "28006",           # 有楽町線
    ("渋谷", "表参道"): "28008",            # 半蔵門線
    ("駒込", "本駒込"): "28009",            # 南北線
    ("要町", "池袋"): "28010",              # 副都心線
    # 都営
    ("本所吾妻橋", "浅草"): "99302",          # 浅草線
    ("西巣鴨", "巣鴨"): "99303",             # 三田線
    ("西大島", "住吉"): "99304",             # 新宿線
    ("中井", "東中野"): "99301",             # 大江戸線
    # 私鉄
    ("小菅", "北千住"): "21002",             # 東武伊勢崎線
    ("北池袋", "池袋"): "21001",             # 東武東上線
    ("椎名町", "池袋"): "22001",             # 西武池袋線
    ("下落合", "高田馬場"): "22007",          # 西武新宿線
    ("京成曳舟", "押上"): "23002",           # 京成押上線
    ("大神宮下", "京成船橋"): "23001",        # 京成本線
    ("下高井戸", "明大前"): "24001",          # 京王線
    ("池ノ上", "駒場東大前"): "24006",        # 京王井の頭線
    ("世田谷代田", "下北沢"): "25001",        # 小田急線
    ("祐天寺", "中目黒"): "26001",           # 東急東横線
    ("池尻大橋", "渋谷"): "26003",           # 東急田園都市線
    ("戸部", "横浜"): "27001",              # 京急本線
    ("川口元郷", "赤羽岩淵"): "99307",        # 埼玉高速鉄道線
}


def station_key(name):
    """駅名を突き合わせる形にそろえる。〈スカイツリー前〉のような副名称は外す。"""
    n = (name or "").replace("ケ", "ヶ").strip()
    return n.split("〈")[0] if "〈" in n else n


def download():
    os.makedirs(CACHE, exist_ok=True)
    paths = {}
    for label, url in PDFS.items():
        path = os.path.join(CACHE, os.path.basename(url))
        if not os.path.exists(path):
            r = subprocess.run(["curl", "-sS", "--max-time", "180", "-o", path, url],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(path):
                raise SystemExit(f"取得できなかった: {label} {r.stderr.strip()}")
        paths[label] = path
    return paths


def rows_of(path, names):
    """PDF の表から、区間と混雑率の行を取り出す。

    表の列を座標で切ろうとすると、ページごとに事業者名の欄の幅が違うため、
    線名の文字が駅名の側に混ざる。「赤土小学校前」が「小学校前」になっていた。
    そこで列を切らず、矢印の前後の文字列から、駅名として知られている
    いちばん長い部分を取る。
    """
    import pypdf
    out, skipped = [], []
    for page in pypdf.PdfReader(path).pages:
        cells = []

        def visit(text, cm, tm, font, size):
            t = text.strip()
            if t:
                cells.append((round(tm[5], 1), round(tm[4], 1), t))

        page.extract_text(visitor_text=visit)
        bands = []
        for y, x, t in sorted(cells, key=lambda c: (-c[0], c[1])):
            if bands and abs(bands[-1][0] - y) <= 1.5:
                bands[-1][1].append((x, t))
            else:
                bands.append([y, [(x, t)]])
        for _, row in bands:
            row.sort()
            time_x = next((x for x, t in row if re.match(r"^\d{1,2}:\d{2}[～~]", t)), None)
            if time_x is None:
                continue
            head = "".join(t for x, t in row if x < time_x)
            if "→" not in head:
                continue
            pre, _, post = head.partition("→")
            a = longest_suffix(pre, names)
            b = longest_prefix(post, names)
            digits = [t for x, t in row if x > time_x and t.isdigit()]
            if not (a and b and digits):
                skipped.append(head)
                continue
            window = next(t for x, t in row if x == time_x)
            nums = [t for x, t in row if x > time_x and ("," in t or t.isdigit() or "." in t)]
            out.append({
                "from": a, "to": b, "window": window, "rate": int(digits[-1]),
                "capacity": nums[-3] if len(nums) >= 3 else None,
                "riders": nums[-2] if len(nums) >= 2 else None,
            })
    return out, skipped


def longest_suffix(text, names):
    t = station_key(text)
    for i in range(len(t)):
        if t[i:] in names:
            return t[i:]
    return None


def longest_prefix(text, names):
    t = station_key(text)
    for i in range(len(t), 0, -1):
        if t[:i] in names:
            return t[:i]
    return None


def main():
    paths = download()
    roster = json.load(open(os.path.join(ROOT, "data/roster/stations.json"), encoding="utf-8"))
    lines = json.load(open(os.path.join(ROOT, "data/reference/lines.json"), encoding="utf-8"))
    line_name = {l["id"]: l["nameJa"] for l in lines}
    by_name = collections.defaultdict(list)
    slug_of = {}
    for s in roster:
        key = station_key(s["nameJa"])
        by_name[key].append(s)
        slug_of.setdefault(key, s["slug"])

    names = set(by_name) | {n for pair in SECTION_LINES for n in pair}
    best, ambiguous, skipped = {}, [], []
    for label, path in paths.items():
        rows, miss = rows_of(path, names)
        skipped += miss
        for r in rows:
            if r["rate"] is None:
                continue
            a, b = r["from"], r["to"]
            fixed = SECTION_LINES.get((a, b))
            if fixed:
                common = {fixed}
            else:
                if a not in by_name or b not in by_name:
                    continue
                here = set().union(*[set(s["lineIds"]) for s in by_name[a]])
                there = set().union(*[set(s["lineIds"]) for s in by_name[b]])
                common = here & there
                if len(common) != 1:
                    ambiguous.append((a, b, r["rate"], sorted(common)))
                    continue
            for lid in common:
                if lid not in best or best[lid]["rate"] < r["rate"]:
                    best[lid] = {
                        "rate": r["rate"], "fromStation": a, "toStation": b,
                        "fromSlug": slug_of.get(a), "toSlug": slug_of.get(b),
                        "window": r["window"], "capacity": r["capacity"],
                        "riders": r["riders"], "table": label,
                    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "meta": {
            "source": "国土交通省「都市鉄道の混雑率調査結果」（令和7年度実績）",
            "sourceUrl": PRESS,
            "fiscalYear": YEAR,
            "unit": "最混雑時間帯1時間の平均混雑率（％）",
            "note": "路線ごとに、公表されている区間のうち最も混雑率が高い区間を採った。"
                    "住む駅がその区間に入っていなければ、実際に乗る区間はこれより緩い",
        },
        "lines": best,
        "withoutData": sorted(line_name[l["id"]] for l in lines if l["id"] not in best),
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)

    print(f"{len(best)}/{len(lines)}路線に混雑率を割り当てた")
    for lid, v in sorted(best.items(), key=lambda kv: -kv[1]["rate"])[:12]:
        print(f"  {line_name.get(lid, lid):24}{v['rate']:>4}%  "
              f"{v['fromStation']}→{v['toStation']}  {v['window']}")
    if ambiguous:
        print(f"\n路線を決められなかった区間: {len(ambiguous)}")
        for a, b, rate, cands in ambiguous:
            print(f"  {a}→{b} {rate}% 候補: "
                  + ("、".join(line_name.get(c, c) for c in cands) or "なし"))
    miss = [line_name[l["id"]] for l in lines if l["id"] not in best]
    if miss:
        print(f"\n混雑率が付かなかった路線 {len(miss)}: " + "、".join(miss))
        print("  調査の対象に入っていない小規模な路線、複数の路線の線路を走る運行系統、"
              "PDF の中で駅名が2行に折り返されていて読み取れない路線がある。"
              "値を作らず、空のままにしている。")


if __name__ == "__main__":
    main()
