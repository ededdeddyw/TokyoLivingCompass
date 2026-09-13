#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本文に書いた「何時まで営業している」を、OpenStreetMap の営業時間と突き合わせる。

  python3 scripts/check-opening-hours.py

夜に外食できるかどうかは、住む場所を選ぶうえで効く。だが「23時ごろまで営業している」
と書いても、それが何軒の話なのかが分からなければ判断材料にならない。
OSM の opening_hours が入っている店を数え、閉店時刻の分布を出す。

OSM に営業時間が入っている店は一部にすぎないので、これは下限である。
「少なくとも何軒はこの時刻まで開いている」としか言えない点に注意する。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POIS = os.path.join(ROOT, "data", "computed", "pois.json")

NIGHT_CATEGORIES = ("restaurant", "bar", "cafe")


def closing_hour(spec):
    """
    opening_hours から、その店の最も遅い閉店時刻を取り出す。
    「10:00-22:00」「17:00-02:00」「Mo-Sa 11:00-23:30」などの形を想定する。
    24時をまたぐ場合は 24 以上として扱う（02:00 なら 26）。
    """
    if not spec or spec.strip() in ("24/7",):
        return 24 if spec else None
    latest = None
    for m in re.finditer(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", spec):
        oh, om, ch, cm = (int(x) for x in m.groups())
        end = ch + cm / 60
        if end <= oh:          # 日をまたぐ
            end += 24
        latest = end if latest is None else max(latest, end)
    return latest


def main():
    pois = json.load(open(POIS, encoding="utf-8"))["stations"]
    rows = []
    for slug, lst in pois.items():
        night = [p for p in lst if p["category"] in NIGHT_CATEGORIES]
        withhours = [(p, closing_hour(p.get("openingHours")))
                     for p in night if closing_hour(p.get("openingHours"))]
        rows.append({
            "slug": slug,
            "total": len(night),
            "known": len(withhours),
            "to22": sum(1 for _, h in withhours if h >= 22),
            "to23": sum(1 for _, h in withhours if h >= 23),
            "to24": sum(1 for _, h in withhours if h >= 24),
        })

    rows.sort(key=lambda r: -r["to23"])
    print(f"{'駅':22}{'夜の店':>8}{'時刻あり':>8}{'22時〜':>8}{'23時〜':>8}{'24時〜':>8}")
    for r in rows[:20]:
        print(f'{r["slug"]:22}{r["total"]:>8}{r["known"]:>8}'
              f'{r["to22"]:>8}{r["to23"]:>8}{r["to24"]:>8}')
    known = sum(r["known"] for r in rows)
    total = sum(r["total"] for r in rows)
    print(f"\n営業時間が入っている店: {known} / {total}件"
          f"（{known * 100 // max(total, 1)}%）")
    print("OSM に入っている店だけの数なので、実際はこれより多い。"
          "本文には「少なくとも何軒」と書けるだけで、断定はできない。")


if __name__ == "__main__":
    main()
