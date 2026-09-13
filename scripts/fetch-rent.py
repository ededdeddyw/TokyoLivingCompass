#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各サイトが公開している駅ごとの家賃相場ページから、間取り別の相場を取得する。

  python3 scripts/fetch-rent.py                      # 未取得の駅だけ
  python3 scripts/fetch-rent.py --refresh            # 取得済みも取り直す
  python3 scripts/fetch-rent.py --site Yahoo!不動産   # 1社だけ取る

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
MIN_BYTES = 5000   # これより短い応答は、中身が返っていないものとして扱う
TRIES = 6          # 1ページを取り直す回数

# ページを取りに行く間隔は、サイトごとに変えながら進める。
# 200 を返しながら中身が空の応答は「速すぎる」という合図とみなし、
# そのサイトの間隔を広げる。うまく取れているあいだは少しずつ縮める。
# こうすると、相手が受け入れられる速さに自然と落ち着く。
PACE_START = 8.0    # 最初の間隔（秒）
PACE_MIN = 5.0      # これより速くはしない
PACE_MAX = 90.0     # これより遅くはしない
PACE_UP = 2.0       # 空の応答が返ったときに間隔を何倍にするか
PACE_DOWN = 0.9     # うまく取れたときに間隔を何倍にするか
COOLDOWN = 60.0     # 空の応答が続いたときに、いったん待つ時間

# 間取りの表記ゆれを、こちらの4区分に寄せる
LABELS = {
    "ワンルーム": "oneRoom", "1R": "oneRoom",
    "1K": "oneK",
    "1LDK": "oneLDK",
    "2LDK": "twoLDK",
}


pace = {}       # サイトごとの、次に取りに行くまでの間隔（秒）
last_hit = {}   # サイトごとの、最後に取りに行った時刻


def fetch(url, site):
    """
    1ページ取る。取りに行く間隔はサイトごとに持ち、応答を見て調整する。

    続けて取りに行くと、200 を返しながら中身が空の応答が返ってくることがある。
    これは「速すぎる」という合図とみなし、そのサイトの間隔を広げて待ち直す。
    うまく取れているあいだは間隔を少しずつ縮め、相手が受け入れられる速さを探る。
    """
    pace.setdefault(site, PACE_START)
    last = ""
    for attempt in range(TRIES):
        wait = pace[site] - (time.time() - last_hit.get(site, 0))
        if wait > 0:
            time.sleep(wait)
        last_hit[site] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=70) as res:
                body = res.read().decode("utf-8", errors="replace")
            if len(body) >= MIN_BYTES:
                pace[site] = max(PACE_MIN, pace[site] * PACE_DOWN)
                return body
            last = f"応答が{len(body)}バイトしかない"
        except Exception as err:  # noqa: BLE001 — サイトごとに落ち方が違う
            last = str(err)
        pace[site] = min(PACE_MAX, pace[site] * PACE_UP)
        print(f"    {site}: {last}。間隔を{pace[site]:.0f}秒に広げて取り直す"
              f"（{attempt + 1}回目）")
        if attempt >= 2:
            print(f"    {site}: {COOLDOWN:.0f}秒待つ")
            time.sleep(COOLDOWN)
    raise RuntimeError(last)


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
    ap.add_argument("--site", action="append", default=[],
                    help="このサイトだけ取る。何度でも指定できる")
    args = ap.parse_args()

    cfg = json.load(open(SOURCES, encoding="utf-8"))
    sites, stations = cfg["sites"], cfg["stations"]
    today = time.strftime("%Y-%m-%d")

    for slug, ids in stations.items():
        path = os.path.join(SURVEY, f"{slug}.json")
        old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        if old and not args.refresh:
            done = {o["source"] for o in old.get("observations", []) if o.get("verified")}
            want = set(args.site) & set(ids) if args.site else set(ids)
            if want <= done:
                print(f"  {slug}: 取得済み")
                continue

        observations = list(old.get("observations", [])) if os.path.exists(path) else []
        if args.site:
            # 指定のないサイトは、すでに取れている分をそのまま残す
            observations = [o for o in observations if o["source"] not in args.site]
        else:
            observations = []
        for site, ident in ids.items():
            if args.site and site not in args.site:
                continue
            url = sites[site]["urlTemplate"].format(id=ident)
            try:
                rent = parse(fetch(url, site))
            except Exception as err:  # noqa: BLE001
                print(f"  × {slug} / {site}: {err}")
                continue
            if not rent:
                print(f"  × {slug} / {site}: 相場が読み取れなかった")
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
            print(f"  {slug:20} {site:14} {got}（間隔{pace[site]:.0f}秒）")

        if not observations:
            print(f"  ! {slug}: 1件も取れなかった")
            continue
        json.dump({"slug": slug, "observations": observations},
                  open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(path, "a", encoding="utf-8").write("\n")

    print("\n取得を終えた。scripts/build-rent-bands.py で帯にまとめる。")


if __name__ == "__main__":
    main()
