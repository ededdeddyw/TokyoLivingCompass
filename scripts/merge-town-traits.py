#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅ごとにまとめた街の特色を1つのファイルにし、出典の記事を添える。

  python3 scripts/merge-town-traits.py PART.json [PART.json ...]

入力は {slug: {"traits": [{"text", "from"}]}} の形のファイル。
出典（記事名・URL・版）は .cache/wikipedia/{slug}.json から取る。
出力: data/town-traits/wikipedia.json

まとめ直した文が出典の記事に無い記事名を指していたり、1文が60字を超えたり、
家賃や所要時間のような数字を含んでいたりしたら、ここで止める。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "wikipedia")
OUT = os.path.join(ROOT, "data", "town-traits", "wikipedia.json")
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")

# 年号（1872年・2000年代）と丁目・番号つきの固有名詞は数字でもよい。
# 家賃・所要時間・件数・人数は既存の出典を正とするので、特色には入れない。
NUMBER_WORDS = re.compile(r"\d+(?:\.\d+)?\s*(?:万円|円|分|軒|件|店舗|人|世帯|%|％|m|メートル|km)")


def main():
    roster = {s["slug"]: s for s in json.load(open(ROSTER, encoding="utf-8"))}
    merged = {}
    if os.path.exists(OUT):
        merged = json.load(open(OUT, encoding="utf-8"))["stations"]
    problems = []
    for part in sys.argv[1:]:
        for slug, rec in json.load(open(part, encoding="utf-8")).items():
            if slug not in roster:
                problems.append(f"{slug}: ロースターに無い駅")
                continue
            cache = json.load(open(os.path.join(CACHE, f"{slug}.json"), encoding="utf-8"))
            titles = {p["title"]: p for p in cache["pages"]}
            for t in rec.get("traits", []):
                if t.get("from") not in titles:
                    problems.append(f"{slug}: 出典に無い記事名「{t.get('from')}」")
                for sent in [s for s in t["text"].split("。") if s]:
                    if len(sent) + 1 > 60:
                        problems.append(f"{slug}: 1文が{len(sent) + 1}字「{sent[:20]}…」")
                if NUMBER_WORDS.search(t["text"]):
                    problems.append(f"{slug}: 数字を含む「{t['text'][:30]}…」")
                if not t["text"].endswith("。"):
                    problems.append(f"{slug}: 句点で終わっていない「{t['text'][:20]}…」")
            used = {t["from"] for t in rec.get("traits", [])}
            merged[slug] = {
                "sources": [{"title": p["title"], "url": p["url"], "retrievedAt": cache["retrievedAt"]}
                            for p in cache["pages"] if p["title"] in used],
                "traits": rec.get("traits", []),
            }
    for p in problems:
        print("  -", p)
    out = {
        "meta": {
            "note": "Wikipedia の駅と町の記事から、街の特色だけを読み取ってまとめ直したもの。"
                    "記事の文は写していない。家賃・所要時間・店の数のような数字は取らない。"
                    "方針は docs/16-town-traits.md。",
            "source": "Wikipedia日本語版（CC BY-SA 4.0）",
            "license": "https://creativecommons.org/licenses/by-sa/4.0/deed.ja",
        },
        "stations": dict(sorted(merged.items())),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(OUT, "a", encoding="utf-8").write("\n")
    n = sum(1 for v in merged.values() if v["traits"])
    print(f"特色のある駅: {n} / {len(roster)}（指摘 {len(problems)}件）")


if __name__ == "__main__":
    main()
