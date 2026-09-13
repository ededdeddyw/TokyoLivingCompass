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
            "ビッグ・エー", "Big-A", "赤札堂", "オーケー", "ラ・ムー", "セイフー",
            "ヨークフーズ", "スーパーバリュー", "サンディ", "肉のハナマサ",
            "食品館あおば", "A･Colle", "Acolle", "アコレ"]
PREMIUM = ["成城石井", "紀ノ国屋", "明治屋", "クイーンズ伊勢丹", "福島屋", "北野エース",
           "DEAN", "プレッセ", "リンコス", "ザ・ガーデン", "三浦屋", "信濃屋",
           "Shinanoya", "Bio c", "Bio C", "ピカール", "Picard", "紀ノ國屋"]


# OSM で shop=supermarket が付いているが、食料品の買い物先として挙げるのが
# 適切でないもの。見つけ次第ここに足す。
NOT_GROCERY = ["Seria", "セリア", "ダイソー", "DAISO", "キャンドゥ", "キタムラ",
               "Be-set", "plaza", "PLAZA"]

# 同じチェーンの別店舗を並べても読み手の判断材料にならないので、
# 最寄りの1店だけ載せる。店名から所属チェーンを割り出すための一覧。
CHAINS = ["まいばすけっと", "ライフ", "サミット", "マルエツ", "東急ストア", "西友",
          "オオゼキ", "赤札堂", "文化堂", "オーケー", "業務スーパー", "成城石井",
          "ピーコックストア", "イトーヨーカドー", "コープ", "コモディイイダ",
          "ヨークマート", "ヨークフーズ", "食品館あおば", "肉のハナマサ",
          "プレッセ", "明治屋", "三徳", "Big-A", "ビッグ・エー", "アコレ",
          "クイーンズ伊勢丹", "京王ストア", "いなげや", "アキダイ", "サンディ"]


def clean_name(name):
    """OSM の店名から、併記された英語表記を落とす。"""
    import re as _re
    return _re.sub(r"\s*[（(][A-Za-z0-9 .,'&-]+[)）]\s*$", "", name).strip()


def chain_of(name):
    for c in CHAINS:
        if c in name:
            return c
    return name  # 一覧にないものは店名そのものをチェーン名とみなす


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

        # 買い物先として挙げるのが適切でないものを外し、店名を整える
        pois = [{**p, "name": clean_name(p["name"])} for p in pois]
        pois = [p for p in pois
                if not any(w.lower() in p["name"].lower() for w in NOT_GROCERY)]

        # 同じチェーンは最寄りの1店だけにする。同じ名前が3つ並んでも判断材料にならない。
        picked, chains_taken = [], set()
        for p in pois:
            c = chain_of(p["name"])
            if c in chains_taken:
                continue
            chains_taken.add(c)
            picked.append(p)
            if len(picked) >= MAX_STORES:
                break

        # 近い順に選ぶだけだと価格帯が偏る。安い店と高い店の差が生活費に効くので、
        # 半径内にあるのに選から漏れた価格帯があれば、その最寄りを1軒足す。
        tiers_shown = {tier_of(p["name"]) for p in picked}
        for want in ("discount", "premium"):
            if want in tiers_shown:
                continue
            extra = next((p for p in pois
                          if tier_of(p["name"]) == want
                          and chain_of(p["name"]) not in chains_taken), None)
            if extra:
                picked.append(extra)
        picked.sort(key=lambda p: p["distanceM"])

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
