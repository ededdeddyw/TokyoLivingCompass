#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各サイトが公開している駅ごとの家賃相場ページから、間取り別の相場を取得する。

  python3 scripts/fetch-rent.py            # 未取得の駅だけ
  python3 scripts/fetch-rent.py --refresh  # 取得済みも取り直す

取りに行くのは、物件一覧ではなく各社が自社の掲載物件を集計して公開している
統計ページである（docs/08-data-sources-rent.md §E-2）。robots.txt で
これらのページは制限されていないことを確認したうえで、1件ずつ間を空けて取得する。

出力: data/rent-survey/<slug>.json
そのあと scripts/build-rent-bands.py が1万円刻みの帯にまとめる。
"""
import argparse
import html
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY = os.path.join(ROOT, "data", "rent-survey")
SOURCES = os.path.join(SURVEY, "sources.json")

UA = "Mozilla/5.0 (compatible; TokyoLivingCompass/1.0; +station rent survey)"
PAUSE = 6.0   # 同じサイトを続けて叩かないための待ち時間

# 間取りの表記ゆれを、こちらの4区分に寄せる
LABELS = {
    "ワンルーム": "oneRoom", "1R": "oneRoom",
    "1K": "oneK",
    "1LDK": "oneLDK",
    "2LDK": "twoLDK",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read().decode("utf-8", errors="replace")


def to_lines(page):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [l.strip() for l in t.split("\n") if l.strip()]


def parse(page):
    """
    「間取りの見出し → 金額」が続けて現れる形をとらえる。
    どちらのサイトも1つめの表が駅全体の相場で、そのあとは個別の物件が並ぶ。
    したがって、各間取りについて最初に現れた値だけを採る。
    """
    lines = to_lines(page)
    out = {}
    for i, line in enumerate(lines):
        key = LABELS.get(line)
        if not key or key in out:
            continue
        for nxt in lines[i + 1:i + 3]:
            m = re.fullmatch(r"([\d.]+)\s*万円", nxt) or re.fullmatch(r"([\d.]+)", nxt)
            if m:
                man = float(m.group(1))
                # 東京23区の1部屋で 3万円未満・200万円超は集計値として不自然
                if 3.0 <= man <= 200.0:
                    out[key] = int(round(man * 10000))
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    cfg = json.load(open(SOURCES, encoding="utf-8"))
    sites, stations = cfg["sites"], cfg["stations"]
    today = time.strftime("%Y-%m-%d")

    for slug, ids in stations.items():
        path = os.path.join(SURVEY, f"{slug}.json")
        if os.path.exists(path) and not args.refresh:
            old = json.load(open(path, encoding="utf-8"))
            if all(o.get("verified") for o in old.get("observations", [])):
                print(f"  {slug}: 取得済み")
                continue

        observations = []
        for site, ident in ids.items():
            url = sites[site]["urlTemplate"].format(id=ident)
            try:
                rent = parse(fetch(url))
            except Exception as err:  # noqa: BLE001
                print(f"  × {slug} / {site}: {err}")
                time.sleep(PAUSE)
                continue
            if not rent:
                print(f"  × {slug} / {site}: 相場が読み取れなかった")
                time.sleep(PAUSE)
                continue
            observations.append({
                "source": site,
                "url": url,
                "retrievedAt": today,
                "basis": sites[site]["basis"],
                "statistic": sites[site]["statistic"],
                # 出典ページを直接読んで取った値なので確認済みとする
                "verified": True,
                "coverage": sites[site]["coverage"],
                "rent": {k: rent.get(k) for k in
                         ("oneRoom", "oneK", "oneLDK", "twoLDK")},
            })
            got = "、".join(f"{k}{v/10000:.1f}万" for k, v in rent.items())
            print(f"  {slug:20} {site:14} {got}")
            time.sleep(PAUSE)

        if not observations:
            print(f"  ! {slug}: 1件も取れなかった")
            continue
        json.dump({"slug": slug, "observations": observations},
                  open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(path, "a", encoding="utf-8").write("\n")

    print("\n取得を終えた。scripts/build-rent-bands.py で帯にまとめる。")


if __name__ == "__main__":
    main()
