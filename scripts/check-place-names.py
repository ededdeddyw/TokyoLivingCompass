#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本文に書いた施設名が、取得した OpenStreetMap のデータに実在するか照合する。

  python3 scripts/check-place-names.py

groceries は sourceUrl を必須にして仕組みで守っているが、本文（medical、family、
outlook など）に出てくる病院名・公園名は文章の中にあるため、機械で縛れない。
そこで、書いたあとに突き合わせる。

照合できなかった名前は「実在しない」と決まったわけではない。
OSM に載っていないだけの場合もある。**人が一件ずつ判断して、確認できないものは消す**
（CLAUDE.md ルール35）。
"""
import json
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER = os.path.join(ROOT, "data", "roster", "stations.json")
POIS = os.path.join(ROOT, "data", "computed", "pois.json")
VERIFIED = os.path.join(ROOT, "data", "reference", "verified-places.json")
CONTENT = os.path.join(ROOT, "data", "content", "ja")

# 施設を指す固有名詞の形。末尾の語で切り出す。
# ひらがなを含めない。含めると「〜を求めるなら高円寺」のように
# 直前の文まで巻き込んでしまう。
SUFFIX = ("病院", "医院", "クリニック", "診療所", "公園", "庭園", "緑地",
          "美術館", "資料館", "図書館", "神社", "明神", "大学", "小学校", "中学校",
          "博物館", "商店街")
PLACE = re.compile(r"[一-龥ァ-ヴA-Za-z0-9・ー]{2,14}(?:" + "|".join(SUFFIX) + r")")

# 施設名ではない一般語。切り出しの網に掛かるので除く。
GENERIC = {
    "総合病院", "個人クリニック", "大学病院", "国立大学", "小学校", "中学校",
    "大学", "公園", "病院", "医院", "クリニック", "診療所", "美術館", "資料館",
    "図書館", "神社", "庭園", "緑地", "附属病院", "医学部附属病院", "付属病院",
    "規模の病院", "通える病院", "できる病院", "小規模な公園", "大きな公園",
    "近くの公園", "区民公園", "以内の公園", "圏内の公園", "医科大学", "女子大学",
    "水女子大学", "小規模なクリニック", "科クリニック", "内科クリニック",
    "学校と公園", "駅周辺にクリニック", "駅前にも小規模な公園",
    # 商店街は固有名詞でない使い方が多い
    "商店街", "アーケード商店街", "駅前商店街",
}

# 本文を持つフィールド（groceries と exits は別途チェック済み）
FIELDS = ["summary", "tagline", "residents", "housingStock", "hazards", "stationNote",
          "nightWalk", "rentReason", "family", "medical", "outlook", "residentComment"]


def main():
    pois = json.load(open(POIS, encoding="utf-8"))["stations"]
    # 駅別の取得範囲の外にあるものや、取得対象の種類に入っていないものは
    # 名前で個別に問い合わせて確認し、その記録を参照する。
    verified = set(json.load(open(VERIFIED, encoding="utf-8"))["places"])
    # 「お台場海浜公園」「舎人公園」のように、駅名そのものが施設名の形をしている。
    # ロースターにある駅名は実在が確かめられているので、照合の対象から外す。
    station_names = {s["nameJa"] for s in json.load(open(ROSTER, encoding="utf-8"))}
    total, unmatched, by_record = 0, [], 0

    for p in sorted(glob.glob(os.path.join(CONTENT, "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        known = {x["name"] for x in pois.get(d["slug"], [])}
        # 表記ゆれを吸収するため、部分一致でも照合できるようにしておく
        blob = " ".join(known)

        names = set()
        for f in FIELDS:
            v = d.get(f)
            if isinstance(v, str):
                names.update(PLACE.findall(v))
        for n in d.get("faces", {}).values():
            names.update(PLACE.findall(n))
        for x in d.get("neighbours", []):
            names.update(PLACE.findall(x["note"]))

        miss = []
        for n in sorted(names):
            if n in GENERIC:
                continue
            if n in station_names or any(n in sn for sn in station_names):
                continue
            total += 1
            if n in blob or any(n in k or k in n for k in known):
                continue
            if n in verified:
                by_record += 1
                continue
            miss.append(n)
        if miss:
            unmatched.append((d["name"], miss))

    print(f"本文に出てくる施設名: {total}件")
    print(f"  うち {by_record}件は data/reference/verified-places.json の記録で確認済み")
    if not unmatched:
        print("すべて OpenStreetMap のデータと照合できました。")
        return
    n = sum(len(m) for _, m in unmatched)
    print(f"照合できなかった名前: {n}件（{len(unmatched)}駅）\n")
    for name, miss in unmatched:
        print(f"  ■ {name}")
        for m in miss:
            print(f"     {m}")
    print("\n※ OSM に載っていないだけの場合もあります。一件ずつ判断し、")
    print("   確認できないものは消してください（ルール35）。")


if __name__ == "__main__":
    main()
