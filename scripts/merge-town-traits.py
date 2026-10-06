#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅ごとにまとめた街の特色を、出典ごとに1つのファイルにし、出典の記事を添える。

  python3 scripts/merge-town-traits.py --source wikipedia PART.json [PART.json ...]
  python3 scripts/merge-town-traits.py --source rehouse PART.json [PART.json ...]

入力は {slug: {"traits": [{"text", "from"}], "sources"?: [{"title", "url"}]}} の形のファイル。
  wikipedia  出典（記事名・URL）は .cache/wikipedia/{slug}.json から取る。
  rehouse    出典は入力の sources をそのまま使い、URL が .cache/rehouse/ にある記事かを確かめる。
出力: data/town-traits/{source}.json

まとめ直した文が出典に無い記事名を指していたり、1文が60字を超えたり、
家賃や所要時間のような数字を含んでいたりしたら、ここで止める。
方針は docs/16-town-traits.md。
"""
import argparse
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")

# 年号（1872年・2000年代）と丁目・番号つきの固有名詞は数字でもよい。
# 家賃・所要時間・件数・人数は既存の出典を正とするので、特色には入れない。
NUMBER_WORDS = re.compile(r"\d+(?:\.\d+)?\s*(?:万円|円|分|軒|件|店舗|人|世帯|%|％|m|メートル|km)")

META = {
    "wikipedia": {
        "label": "Wikipedia",
        "licenseName": "CC BY-SA 4.0",
        "license": "https://creativecommons.org/licenses/by-sa/4.0/deed.ja",
        "source": "Wikipedia日本語版（CC BY-SA 4.0）",
        "note": "Wikipedia の駅と町の記事から、街の特色だけを読み取ってまとめ直したもの。"
                "記事の文は写していない。家賃・所要時間・店の数のような数字は取らない。"
                "方針は docs/16-town-traits.md。",
    },
    "rehouse": {
        "label": "三井のリハウス",
        "source": "三井のリハウス「リライフモード」の街の記事",
        "note": "記事から、住んでいる人の目線の特色だけを読み取ってまとめ直したもの。"
                "記事の文は写さず、言い換えた流用もしない。筆者の感想は事実に置き換えるか書かない。"
                "家賃・所要時間・店の数のような数字は取らない。方針は docs/16-town-traits.md §4。",
    },
}


def wikipedia_sources(slug, used):
    cache = json.load(open(os.path.join(ROOT, ".cache", "wikipedia", f"{slug}.json"),
                           encoding="utf-8"))
    titles = {p["title"] for p in cache["pages"]}
    sources = [{"title": p["title"], "url": p["url"], "retrievedAt": cache["retrievedAt"]}
               for p in cache["pages"] if p["title"] in used]
    return titles, sources


def rehouse_sources(rec, used, known):
    sources = []
    for s in rec.get("sources", []):
        if s["title"] in used:
            sources.append({"title": s["title"], "url": s["url"],
                            "retrievedAt": known.get(s["url"], "")})
    return {s["title"] for s in rec.get("sources", []) if s["url"] in known}, sources


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, choices=sorted(META))
    ap.add_argument("parts", nargs="+")
    args = ap.parse_args()

    out_path = os.path.join(ROOT, "data", "town-traits", f"{args.source}.json")
    roster = {s["slug"]: s for s in json.load(open(ROSTER, encoding="utf-8"))}
    known = {}
    if args.source == "rehouse":
        for f in glob.glob(os.path.join(ROOT, ".cache", "rehouse", "*.json")):
            r = json.load(open(f, encoding="utf-8"))
            known[r["url"]] = r["retrievedAt"]

    merged = {}
    if os.path.exists(out_path):
        merged = json.load(open(out_path, encoding="utf-8"))["stations"]
    problems = []
    for part in args.parts:
        for slug, rec in json.load(open(part, encoding="utf-8")).items():
            if slug.startswith("_"):
                continue
            if slug not in roster:
                problems.append(f"{slug}: ロースターに無い駅")
                continue
            traits = rec.get("traits", [])
            used = {t["from"] for t in traits}
            if args.source == "wikipedia":
                titles, sources = wikipedia_sources(slug, used)
            else:
                titles, sources = rehouse_sources(rec, used, known)
            for t in traits:
                if t.get("from") not in titles:
                    problems.append(f"{slug}: 出典に無い記事名「{t.get('from')}」")
                for sent in [s for s in t["text"].split("。") if s]:
                    if len(sent) + 1 > 60:
                        problems.append(f"{slug}: 1文が{len(sent) + 1}字「{sent[:20]}…」")
                if NUMBER_WORDS.search(t["text"]):
                    problems.append(f"{slug}: 数字を含む「{t['text'][:30]}…」")
                if not t["text"].endswith("。"):
                    problems.append(f"{slug}: 句点で終わっていない「{t['text'][:20]}…」")
            merged[slug] = {"sources": sources, "traits": traits}
    for p in problems:
        print("  -", p)
    out = {"meta": META[args.source], "stations": dict(sorted(merged.items()))}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(out_path, "a", encoding="utf-8").write("\n")
    n = sum(1 for v in merged.values() if v["traits"])
    print(f"特色のある駅: {n} / {len(roster)}（指摘 {len(problems)}件）→ {out_path}")


if __name__ == "__main__":
    main()
