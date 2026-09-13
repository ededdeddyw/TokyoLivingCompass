#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/computed/terrain.json の判定を、駅コンテンツの terrain.slope に反映する。

  python3 scripts/apply-terrain.py --dry-run
  python3 scripts/apply-terrain.py

slope は測った値で置き換える。note（坂について人が書いた文）は自動では直さない。
測定と食い違う言い回しを見つけて一覧に出すので、人が読んで書き直す。
「起伏が大きい」と書いた駅が測ると「坂がある」だった、という取り違えを拾うため。
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERRAIN = os.path.join(ROOT, "data", "computed", "terrain.json")
CONTENT = os.path.join(ROOT, "data", "content", "ja")

LABEL = {"flat": "ほぼ平坦", "some": "坂がある", "hilly": "起伏が大きい"}

# note の中で、その傾斜を主張している言い回し。測定と食い違えば指摘する。
CLAIMS = {
    "hilly": ["起伏が大きい", "急な坂", "坂が多く", "勾配がきつ", "坂はきつ", "坂が続く"],
    "flat": ["平坦", "起伏がほとんど", "大きな起伏はない", "坂を意識せず"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = json.load(open(TERRAIN, encoding="utf-8"))["stations"]
    changed, mismatches = 0, []

    for fname in sorted(os.listdir(CONTENT)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CONTENT, fname)
        c = json.load(open(path, encoding="utf-8"))
        m = data.get(c["slug"])
        if not m or "terrain" not in c:
            continue

        measured, written = m["slope"], c["terrain"]["slope"]
        note = c["terrain"].get("note", "")

        # note が別の傾斜を主張していないか。
        # ただし「沿いは平坦だが、一本入ると上り坂になる」のように逆接を伴う文は、
        # 場所による違いを書いたものなので矛盾ではない。
        for slope, words in CLAIMS.items():
            if slope == measured:
                continue
            for w in words:
                if w in note and not any(
                    c in next((s for s in re.split(r"(?<=。)", note) if w in s), "")
                    for c in ("だが", "が、", "ものの", "一方", "ただし")
                ):
                    mismatches.append(
                        (c["name"], measured, m["spreadM"], w,
                         next(s for s in re.split(r"(?<=。)", note) if w in s).strip()))
                    break

        if measured != written:
            changed += 1
            print(f"■ {c['name']}: {LABEL[written]} → {LABEL[measured]}"
                  f"（標高差 {m['spreadM']}m、駅 {m['stationElevationM']}m）")
            if not args.dry_run:
                c["terrain"]["slope"] = measured
                json.dump(c, open(path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                open(path, "a", encoding="utf-8").write("\n")

    print(f"\nslope を{'直す駅' if args.dry_run else '直した駅'}: {changed}件")
    if mismatches:
        print(f"\n本文が測定と食い違う箇所（人が読んで書き直す）: {len(mismatches)}件")
        for name, measured, spread, word, sentence in mismatches:
            print(f"  ■ {name}  測定は「{LABEL[measured]}」（差{spread}m）なのに「{word}」と書いている")
            print(f"     {sentence}")


if __name__ == "__main__":
    main()
