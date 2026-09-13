#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複数サイトの平均から求めた家賃を、駅プロフィールに反映する。

  python3 scripts/apply-rent.py --dry-run
  python3 scripts/apply-rent.py

これまで data/stations/*.json の rent は推定値（dataQuality: "seed"）で、
公開できない値だった。出典のある平均値に差し替え、"reviewed" に上げる。

駅ページには帯（12万〜13万円）を出すが、逆引き検索や rentValue の計算には
1つの数値が要る。そこで帯のもとになった平均値をこちらに入れる。
帯と平均は同じ観測値から出しているので食い違わない。
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANDS = os.path.join(ROOT, "data", "computed", "rent-bands.json")
STATIONS = os.path.join(ROOT, "data", "stations")
RENT_TYPES = ["oneRoom", "oneK", "oneLDK", "twoLDK"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bands = json.load(open(BANDS, encoding="utf-8"))
    created = updated = skipped = 0

    for slug, b in sorted(bands.items()):
        rent = {t: b["bands"][t]["mean"] for t in RENT_TYPES if t in b["bands"]}
        if len(rent) < len(RENT_TYPES):
            print(f"  {slug}: 4つの間取りが揃っていないため反映しない（{len(rent)}件）")
            skipped += 1
            # 前回は4つ揃っていて、今回そろわなくなった駅がある（東雲など）。
            # 古い値を残すと、帯と駅プロフィールで違う数字を出すことになる。
            path = os.path.join(STATIONS, f"{slug}.json")
            if os.path.exists(path):
                prof = json.load(open(path, encoding="utf-8"))
                if prof.pop("rent", None) is not None and not args.dry_run:
                    json.dump(prof, open(path, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=2)
                    open(path, "a", encoding="utf-8").write("\n")
                    print(f"    古い家賃を消した")
            continue

        path = os.path.join(STATIONS, f"{slug}.json")
        if os.path.exists(path):
            prof = json.load(open(path, encoding="utf-8"))
            created_now = False
        else:
            prof = {"slug": slug, "scores": {}, "similarStations": []}
            created_now = True

        prof["rent"] = rent
        prof["sources"] = {
            **prof.get("sources", {}),
            "rent": {
                "name": "、".join(s["name"] for s in b["sources"]) + "（当社調べ）",
                "basis": "asking",
                "statistic": "mean",
                "retrievedAt": b["retrievedAt"],
                "method": "multi-site-average",
            },
        }
        # 出典が付いたので、推定値ではなくなった
        prof["dataQuality"] = "reviewed" if b["verified"] else "seed"
        prof["lastReviewedAt"] = b["retrievedAt"]

        label = "新規" if created_now else "更新"
        vals = "、".join(f"{v/10000:.1f}万" for v in rent.values())
        print(f"  {label} {slug:20} {vals}")
        if not args.dry_run:
            json.dump(prof, open(path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            open(path, "a", encoding="utf-8").write("\n")
        created += created_now
        updated += not created_now

    print(f"\n新規 {created}駅 / 更新 {updated}駅 / 見送り {skipped}駅")


if __name__ == "__main__":
    main()
