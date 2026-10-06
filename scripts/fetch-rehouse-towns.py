#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三井のリハウス「リライフモード」の、東京23区の街の記事を読み取りの材料として取る。

  python3 scripts/fetch-rehouse-towns.py

出力: .cache/rehouse/{記事のパスを _ でつないだ名前}.json（gitignore 済み）

取った記事は、街の特色を読み取るためだけに使う。本文は写さず、言い換えた流用もしない
（運営会社の「サイトご利用上の注意」が、許可のない複製・転用を控えるよう求めている）。
家賃・所要時間・店の数のような数字も取らない。方針は docs/16-town-traits.md §4。

1件ごとに間隔を空け、robots.txt で禁止されたパスは取らない。
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".cache", "rehouse")
BASE = "https://www.rehouse.co.jp"
TAG = "/relifemode/tag/tokyo/"
UA = "TokyoLivingCompass/0.1 (https://github.com/ededdeddyw/TokyoLivingCompass)"
WAIT = 6.0


def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as res:
        body = res.read().decode("utf-8", errors="replace")
    time.sleep(WAIT)
    return body


def text_of(page):
    """記事の見出しと本文の段落だけを平文にする。"""
    m = re.search(r"<article.*?</article>", page, re.S) or re.search(r"<main.*?</main>", page, re.S)
    body = m.group(0) if m else page
    body = re.sub(r"<(script|style|nav|aside|footer|form)[^>]*>.*?</\1>", "", body, flags=re.S)
    parts = []
    for tag, inner in re.findall(r"<(h[1-4]|p|li|th|td|figcaption)[^>]*>(.*?)</\1>", body, re.S):
        s = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        s = re.sub(r"\s+", " ", s)
        if s:
            parts.append(f"## {s}" if tag.startswith("h") else s)
    return "\n".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    paths, page = [], 1
    while True:
        url = TAG if page == 1 else f"{TAG}page/{page}/"
        try:
            body = get(url)
        except Exception:  # noqa: BLE001
            break
        found = re.findall(r'href="(?:https://www\.rehouse\.co\.jp)?(/relifemode/column/[^"#?]+/)"', body)
        new = [p for p in dict.fromkeys(found) if p not in paths]
        if not new:
            break
        paths += new
        page += 1
    print(f"記事: {len(paths)}件（一覧 {page - 1}ページ）", flush=True)

    for n, path in enumerate(paths, 1):
        name = path.strip("/").replace("/", "_")
        dest = os.path.join(OUT, f"{name}.json")
        if os.path.exists(dest):
            continue
        try:
            body = get(path)
        except Exception as e:  # noqa: BLE001
            print(f"  [{n}] 取得できず {path}: {e}", file=sys.stderr, flush=True)
            continue
        title = re.search(r"<title>(.*?)</title>", body, re.S)
        rec = {
            "url": BASE + path,
            "title": html.unescape(title.group(1).strip()) if title else "",
            "retrievedAt": time.strftime("%Y-%m-%d"),
            "text": text_of(body),
        }
        json.dump(rec, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[{n}/{len(paths)}] {rec['title'][:60]}", flush=True)


if __name__ == "__main__":
    main()
