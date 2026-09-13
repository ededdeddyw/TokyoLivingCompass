#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家賃相場ページの駅コードを集め、data/rent-survey/sources.json に書き出す。

  python3 scripts/build-rent-sources.py

LIFULL HOME'S と Yahoo!不動産は、どちらも路線ごとの相場一覧ページを公開しており、
そこに駅名と駅コードの組が載っている。458駅ぶんの駅コードを人が1つずつ調べる
代わりに、この一覧ページから読み取る。

アットホームは駅コードを使わず、駅名のローマ字をそのまま URL に置いている
（中目黒なら nakameguro-st）。ロースターが持つローマ字から組み立てられるので、
このサイトについてはページを取りに行かない。

読むのは路線の一覧ページだけで、物件一覧は巡回しない
（docs/08-data-sources-rent.md §E）。取得したコードは sources.json に残すので、
このスクリプトを毎回動かす必要はない。

  python3 scripts/build-rent-sources.py        # 未取得のサイトだけ集める
  python3 scripts/build-rent-sources.py --refresh
"""
import argparse
import html
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
SURVEY = os.path.join(ROOT, "data", "rent-survey")
SOURCES = os.path.join(SURVEY, "sources.json")
CACHE = os.path.join(ROOT, ".cache", "rent-codes")

UA = "Mozilla/5.0 (compatible; TokyoLivingCompass/1.0; +station rent survey)"
PAUSE = 12.0        # 相手のサーバーに続けて負担をかけないための待ち時間
MIN_BYTES = 5000    # これより短い応答は、中身が返っていないものとして取り直す

HOMES_INDEX = "https://www.homes.co.jp/chintai/tokyo/line/price/"
HOMES_LINE = "https://www.homes.co.jp/chintai/tokyo/{line}/price/"
HOMES_LINE_RE = re.compile(r"/chintai/tokyo/([a-z0-9-]+-line)/price/")
HOMES_PAIR_RE = re.compile(r'/chintai/tokyo/([a-z0-9_]+_\d{5})-st/price/">([^<]{1,20})</a>')

YAHOO_LINE = "https://realestate.yahoo.co.jp/rent/price/03/13/r/{line}/"
YAHOO_SEED = "2321"   # 東急東横線。ここから他の路線へたどる
YAHOO_LINE_RE = re.compile(r'/rent/price/03/13/r/(\d+)/["\'>]')
YAHOO_PAIR_RE = re.compile(r'/rent/price/03/13/r/(\d+)/(\d+)/"?>([^<]{1,20})</a>')


def norm(name):
    """駅名の表記ゆれを吸収する。「鐘ヶ淵」と「鐘ケ淵」、「押上〈スカイツリー前〉」と「押上」。"""
    return re.sub(r"[〈（(].*?[〉）)]", "", name).replace("ヶ", "ケ").replace("ヵ", "カ")


def get(url, tries=5):
    """短い応答（中身が返っていない）と接続の失敗を、間を空けて取り直す。"""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9]+", "_", url)[-120:] + ".html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=70) as res:
                body = res.read().decode("utf-8", "replace")
            if len(body) >= MIN_BYTES:
                open(path, "w", encoding="utf-8").write(body)
                return body
            print(f"    短い応答（{len(body)}バイト）。{20 * (attempt + 1)}秒待って取り直す")
        except Exception as err:  # noqa: BLE001 — サイトごとに落ち方が違う
            print(f"    {err}。{20 * (attempt + 1)}秒待って取り直す")
        time.sleep(20 * (attempt + 1))
    return ""


def collect_homes():
    """LIFULL HOME'S の路線ページから、駅名と駅コードの組を集める。"""
    index = get(HOMES_INDEX)
    lines = sorted(set(HOMES_LINE_RE.findall(index)))
    print(f"LIFULL HOME'S: 路線ページ {len(lines)}件")
    codes = {}
    for i, line in enumerate(lines, 1):
        page = get(HOMES_LINE.format(line=line))
        if not page:
            print(f"  [{i}/{len(lines)}] {line} 取得できなかった")
            continue
        new = 0
        for code, name in HOMES_PAIR_RE.findall(page):
            name = html.unescape(name).strip()
            if name and name not in codes:
                codes[name] = code
                new += 1
        print(f"  [{i}/{len(lines)}] {line} 新規{new}件 累計{len(codes)}件")
        time.sleep(PAUSE)
    return codes


def collect_yahoo():
    """Yahoo!不動産の路線ページから、駅名と駅コードの組を集める。"""
    seen, queue, codes = set(), [YAHOO_SEED], {}
    while queue:
        line = queue.pop(0)
        if line in seen:
            continue
        seen.add(line)
        page = get(YAHOO_LINE.format(line=line))
        if not page:
            print(f"  路線{line} 取得できなかった")
            continue
        for found in YAHOO_LINE_RE.findall(page):
            if found not in seen and found not in queue:
                queue.append(found)
        new = 0
        for line_cd, station_cd, name in YAHOO_PAIR_RE.findall(page):
            name = html.unescape(name).strip()
            if name and name not in codes:
                codes[name] = f"{line_cd}/{station_cd}"
                new += 1
        print(f"  路線{line} 新規{new}件 累計{len(codes)}件 残り{len(queue)}路線")
        time.sleep(PAUSE / 4)
    print(f"Yahoo!不動産: 路線 {len(seen)}件から駅名 {len(codes)}件")
    return codes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="取得済みのページも取り直す")
    ap.add_argument("--site", choices=["homes", "yahoo", "both"], default="both",
                    help="駅コードを取りに行くサイト。アットホームは常に組み立てる")
    args = ap.parse_args()
    if args.refresh and os.path.isdir(CACHE):
        for f in os.listdir(CACHE):
            os.remove(os.path.join(CACHE, f))

    cfg = json.load(open(SOURCES, encoding="utf-8"))
    stations = cfg["stations"]
    roster = json.load(open(ROSTER, encoding="utf-8"))

    collected = {}
    if args.site in ("homes", "both"):
        collected["LIFULL HOME'S"] = collect_homes()
    if args.site in ("yahoo", "both"):
        collected["Yahoo!不動産"] = collect_yahoo()

    added = 0
    for st in roster:
        # アットホームはローマ字から URL を組み立てられる
        athome = st["nameRomaji"].lower().replace("-", "")
        entry = stations.setdefault(st["slug"], {})
        if entry.get("アットホーム") != athome:
            entry["アットホーム"] = athome
            added += 1
        for site, codes in collected.items():
            if not codes:
                continue
            by_norm = {norm(k): v for k, v in codes.items()}
            code = codes.get(st["nameJa"]) or by_norm.get(norm(st["nameJa"]))
            if not code:
                continue
            entry = stations.setdefault(st["slug"], {})
            if entry.get(site) != code:
                entry[site] = code
                added += 1

    cfg["stations"] = dict(sorted(stations.items()))
    with open(SOURCES, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")

    both = sum(1 for v in cfg["stations"].values() if len(v) >= 2)
    print(f"\n駅コードを{added}件書き加えた。"
          f"2社そろった駅: {both} / ロースター{len(roster)}駅")
    print("→ data/rent-survey/sources.json")


if __name__ == "__main__":
    main()
