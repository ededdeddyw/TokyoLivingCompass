#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
積み上げた家賃の履歴から、駅プロフィールの rentHistory を作る。

  python3 scripts/apply-rent-history.py

各サイトは過去の相場を公開していないため、推移は取得のたびに貯めるしかない。
2時点そろった駅だけ rentHistory を持たせる。1時点しかない駅は推移にならない。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "rent-survey", "history.json")
BANDS = os.path.join(ROOT, "data", "computed", "rent-bands.json")
STATIONS = os.path.join(ROOT, "data", "stations")


def main():
    if not os.path.exists(HIST):
        raise SystemExit("履歴がありません。先に build-rent-bands.py を実行してください")
    hist = json.load(open(HIST, encoding="utf-8"))
    bands = json.load(open(BANDS, encoding="utf-8"))

    made = 0
    for slug, per_date in sorted(hist.items()):
        dates = sorted(per_date)
        if len(dates) < 2:
            continue
        path = os.path.join(STATIONS, f"{slug}.json")
        if not os.path.exists(path):
            continue
        prof = json.load(open(path, encoding="utf-8"))
        b = bands.get(slug)
        prof["rentHistory"] = {
            "points": [{"year": int(d[:4]), "rent": per_date[d]} for d in dates],
            "source": {
                "name": "、".join(s["name"] for s in b["sources"]) + "（当社調べ）",
                "basis": "asking",
                "statistic": "mean",
                "retrievedAt": dates[-1],
                "method": "multi-site-average",
            },
        }
        json.dump(prof, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(path, "a", encoding="utf-8").write("\n")
        made += 1

    total = len(hist)
    dates = sorted({d for v in hist.values() for d in v})
    print(f"履歴の時点: {len(dates)}件（{'、'.join(dates)}）")
    if made:
        print(f"{made}/{total}駅に推移を持たせた")
    else:
        print(f"2時点そろった駅がまだないため、推移は作らなかった（{total}駅ぶん記録済み）")
        print("次回この取得を実行したときから、推移が出せるようになる。")


if __name__ == "__main__":
    main()
