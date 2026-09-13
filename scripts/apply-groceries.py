#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/computed/pois.json のスーパーを、駅コンテンツの groceries に反映する。

  python3 scripts/apply-groceries.py --dry-run   # 差分だけ見る
  python3 scripts/apply-groceries.py             # 書き込む

店名・座標・徒歩分数は OpenStreetMap から取る。書き手の記憶で店名を書かないための
仕組みである（CLAUDE.md ルール35）。価格帯（tier）だけはチェーン名からの判断なので、
下の対応表に根拠を残す。表にないチェーンは standard として扱う。

すでに書いてある note（その店について人が書いた一文）は、店名が一致すれば引き継ぐ。
"""
import argparse
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POIS = os.path.join(ROOT, "data", "computed", "pois.json")
CONTENT = os.path.join(ROOT, "data", "content", "ja")

MAX_STORES = 5      # 1駅に載せる上限。多すぎると読み手が選べない

# 価格帯の判断。安い順に買い回れるかどうかが生活費に効くため、この3段階で示す。
DISCOUNT = ["オオゼキ", "業務スーパー", "ロピア", "西友", "ドン・キホーテ", "アコレ",
            "ビッグ・エー", "赤札堂", "OK", "オーケー", "ラ・ムー", "セイフー",
            "ヨークフーズ", "スーパーバリュー", "サンディ"]
PREMIUM = ["成城石井", "紀ノ国屋", "明治屋", "クイーンズ伊勢丹", "福島屋", "北野エース",
           "DEAN", "プレッセ", "スーパーマーケットクイーンズ", "リンコス", "ザ・ガーデン"]


def tier_of(name):
    for w in PREMIUM:
        if w in name:
            return "premium"
    for w in DISCOUNT:
        if w in name:
            return "discount"
    return "standard"


def osm_url(poi):
    return f"https://www.openstreetmap.org/{poi['osmType']}/{poi['osmId']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = json.load(open(POIS, encoding="utf-8"))
    retrieved = data["meta"]["retrievedAt"]
    per_station = data["stations"]

    changed = 0
    for fname in sorted(os.listdir(CONTENT)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CONTENT, fname)
        content = json.load(open(path, encoding="utf-8"))
        slug = content["slug"]
        pois = [p for p in per_station.get(slug, []) if p["category"] == "supermarket"]
        if not pois:
            print(f"  {content['name']}: 半径内にスーパーが見つからない")
            continue

        # 同じ店が node と way で重複することがあるので、名前と距離が近いものはまとめる
        picked, seen = [], []
        for p in pois:
            if any(p["name"] == q["name"] and abs(p["distanceM"] - q["distanceM"]) < 120
                   for q in seen):
                continue
            seen.append(p)
            picked.append(p)
            if len(picked) >= MAX_STORES:
                break

        old_notes = {g["name"]: g.get("note") for g in content.get("groceries", [])}
        groceries = []
        for p in picked:
            entry = {
                "name": p["name"],
                "tier": tier_of(p["name"]),
                "walkMinutes": p["walkMinutes"],
                "sourceUrl": osm_url(p),
                "verifiedAt": retrieved,
            }
            note = old_notes.get(p["name"])
            if note:
                entry["note"] = note
            groceries.append(entry)

        before = json.dumps(content.get("groceries", []), ensure_ascii=False, sort_keys=True)
        after = json.dumps(groceries, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        changed += 1
        print(f"■ {content['name']}: {len(content.get('groceries', []))} → {len(groceries)}店")
        for g in groceries:
            print(f"    {g['name']:26} {g['tier']:9} 徒歩{g['walkMinutes']}分")
        if not args.dry_run:
            content["groceries"] = groceries
            json.dump(content, open(path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            open(path, "a", encoding="utf-8").write("\n")

    print(f"\n{changed}駅を{'確認した（書き込んでいない）' if args.dry_run else '書き換えた'}")


if __name__ == "__main__":
    main()
