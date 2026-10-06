#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅の記事と町の記事を Wikipedia 日本語版から取り、街の特色を読み取るための材料にする。

  python3 scripts/fetch-wikipedia-towns.py            # 全458駅
  python3 scripts/fetch-wikipedia-towns.py osaki ...  # 指定した駅だけ

出力: .cache/wikipedia/{slug}.json（gitignore 済み）

取るのは文章の材料だけで、家賃・所要時間・店の数のような数字は使わない。
数字は既存の出典（data/computed/）を正とする。特色をまとめ直した結果は
data/town-traits/ に置く。方針は docs/16-town-traits.md。

Wikipedia の API は、続けて呼ぶと 429 を返す。1件ごとに待ち、
断られたら間隔を空けて取り直す。User-Agent に連絡先を入れるのは
Wikimedia の利用方針による。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
OUT = os.path.join(ROOT, ".cache", "wikipedia")
WIKI = "https://ja.wikipedia.org/wiki/"
UA = "TokyoLivingCompass/0.1 (https://github.com/ededdeddyw/TokyoLivingCompass)"
WAIT = 3.0

# 特色を読み取るのに使う節。のりば・年表・利用状況などは読まない
KEEP = re.compile(r"駅周辺|概要|地理|地域|特徴|文化|商業|商店|まち|街|名所|施設|史跡|繁華")
SKIP = re.compile(r"利用状況|乗車人員|乗降人員|のりば|構造|バス|年表|隣の駅|脚注|出典|"
                  r"関連項目|外部リンク|世帯数|人口|学区|郵便|事業所|交通|参考")


def fetch_raw(title):
    """記事の wikitext を返す。無ければ None。

    API（api.php・REST）は、この環境から続けて呼ぶと 429 を返し続けた。
    記事の原文を返す action=raw は、間隔を空ければ取れる。
    """
    url = f"{WIKI}{urllib.parse.quote(title.replace(' ', '_'))}?action=raw"
    for i in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as res:
                time.sleep(WAIT)
                return res.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(WAIT)
                return None
            if e.code != 429:
                raise
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(30 * (i + 1))
    raise SystemExit("Wikipedia から応答が得られなかった")


def strip_nested(text, open_, close):
    """{{…}} や {|…|} のような入れ子の囲みを取り除く。"""
    out, depth, i = [], 0, 0
    while i < len(text):
        if text.startswith(open_, i):
            depth += 1
            i += len(open_)
        elif depth and text.startswith(close, i):
            depth -= 1
            i += len(close)
        else:
            if not depth:
                out.append(text[i])
            i += 1
    return "".join(out)


def plain(wikitext):
    """wikitext を、読み取りに使える平文に直す。"""
    t = re.sub(r"<!--.*?-->", "", wikitext, flags=re.S)
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = strip_nested(t, "{{", "}}")
    t = strip_nested(t, "{|", "|}")
    t = re.sub(r"\[\[(?:ファイル|画像|File|Image|Category|カテゴリ):[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]", "", t)
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"^[*#:;]+\s*", "", t, flags=re.M)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def page(title, hops=2):
    raw = fetch_raw(title)
    if raw is None:
        return None
    m = re.match(r"\s*#(?:REDIRECT|転送)\s*\[\[([^\]#|]+)", raw, re.I)
    if m:
        return page(m.group(1).strip(), hops - 1) if hops else None
    if re.search(r"\{\{\s*(?:aimai|曖昧さ回避|disambig|地名の曖昧さ回避)", raw, re.I):
        return None
    return {"title": title.replace("_", " "),
            "fullurl": f"{WIKI}{urllib.parse.quote(title.replace(' ', '_'))}",
            "extract": plain(raw)}


def sections(text, limit=1800):
    """読み取りに使う節だけを残す。冒頭の段落は必ず残す。"""
    parts = re.split(r"\n(={2,4} .*? ={2,4})\n", text)
    out = [parts[0].strip()[:limit]]
    for i in range(1, len(parts), 2):
        head = parts[i]
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if KEEP.search(head) and not SKIP.search(head) and body:
            out.append(f"{head}\n{body[:limit]}")
    return "\n\n".join(out)


def in_tokyo(p, ward):
    t = p.get("extract", "")[:600]
    # 栄町駅で、千葉県印旛郡栄町の記事が当たっていた。冒頭に他県の名前があれば外す
    if re.search(r"(?:千葉|埼玉|神奈川|北海道|大阪|愛知|兵庫|福岡)[県府道]?", t[:200]) and "東京都" not in t[:200]:
        return False
    return "東京都" in t or ward in t


# 同じ駅名が2つある駅は、記事名を決め打ちする
STATION_TITLE = {
    "waseda-toden": "早稲田停留場",
    "asakusa-tx": "浅草駅 (つくばエクスプレス)",
    # 「栄町停留場」は曖昧さ回避の記事で、「栄町駅」は東京都の駅ではない
    "sakaecho": "栄町停留場 (東京都)",
}


def station_page(st):
    name, ward = st["nameJa"], st["wardNameJa"]
    if st["slug"] in STATION_TITLE:
        return page(STATION_TITLE[st["slug"]])
    for title in (f"{name}駅", f"{name}駅 (東京都)", f"{name}停留場"):
        p = page(title)
        if p and in_tokyo(p, ward):
            return p
    return None


def town_page(st):
    name, ward = st["nameJa"], st["wardNameJa"]
    for title in (f"{name} ({ward})", f"{name} (東京都)", name):
        p = page(title)
        if p and in_tokyo(p, ward) and not p["title"].endswith("駅"):
            return p
    return None


def main():
    roster = json.load(open(ROSTER, encoding="utf-8"))
    only = set(sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    for n, st in enumerate(roster, 1):
        if only and st["slug"] not in only:
            continue
        path = os.path.join(OUT, f"{st['slug']}.json")
        if os.path.exists(path):
            continue
        rec = {"slug": st["slug"], "name": st["nameJa"], "ward": st["wardNameJa"],
               "retrievedAt": time.strftime("%Y-%m-%d"), "pages": []}
        for kind, fn in (("station", station_page), ("town", town_page)):
            p = fn(st)
            if p:
                rec["pages"].append({
                    "kind": kind, "title": p["title"], "url": p["fullurl"],
                    "text": sections(p.get("extract", "")),
                })
        json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[{n}/{len(roster)}] {st['nameJa']}: "
              + (", ".join(x["title"] for x in rec["pages"]) or "見つからず"), flush=True)


if __name__ == "__main__":
    main()
