#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複数サイトの家賃相場を平均し、1万円刻みの帯（band）に丸める。

  python3 scripts/build-rent-bands.py

入力: data/rent-survey/<slug>.json
      サイトごとに、いつ・どのページで見た数字なのかを記録した観測値。
出力: data/computed/rent-bands.json

相場を1点の数字で示すと、実際には出典ごとに数万円ちがう値を1つに見せてしまう。
帯で示したうえで、出典ごとの最小と最大も持たせ、開きが大きいときは駅ページで注記する。
「弊社調べ」と名乗るからには、元の観測値をリポジトリに残して後から検算できる形にする。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY_DIR = os.path.join(ROOT, "data", "rent-survey")
OUT_FILE = os.path.join(ROOT, "data", "computed", "rent-bands.json")

RENT_TYPES = ["oneRoom", "oneK", "oneLDK", "twoLDK"]
STEP = 10000            # 帯の刻み（1万円）
WIDE_SPREAD = 30000     # これ以上ひらいたら「出典によって差が大きい」とみなす


def band(values):
    """観測値の平均を、1万円刻みの帯に丸める。"""
    mean = sum(values) / len(values)
    low = int(mean // STEP) * STEP
    return {
        "low": low,
        "high": low + STEP,
        "mean": int(round(mean)),
        "sourceMin": min(values),
        "sourceMax": max(values),
        "sourceCount": len(values),
        "wideSpread": max(values) - min(values) >= WIDE_SPREAD,
    }


def main():
    if not os.path.isdir(SURVEY_DIR):
        raise SystemExit(f"{SURVEY_DIR} がありません")

    out = {}
    for fname in sorted(os.listdir(SURVEY_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(SURVEY_DIR, fname)
        survey = json.load(open(path, encoding="utf-8"))
        slug = survey["slug"]
        if slug != fname[:-5]:
            raise SystemExit(f"{fname}: ファイル名と slug が一致しません（{slug}）")

        obs = survey["observations"]
        if len(obs) < 2:
            raise SystemExit(f"{fname}: 観測値が {len(obs)} 件しかありません。2件以上必要です")

        # 「複数サイトの平均」と名乗る以上、1サイトしか値がない間取りは帯にしない。
        bands = {}
        for t in RENT_TYPES:
            values = [o["rent"][t] for o in obs if o["rent"].get(t) is not None]
            if len(values) >= 2:
                bands[t] = band(values)
        if not bands:
            print(f"  {slug}: 2サイト以上そろった間取りがないため、帯を作らなかった")
            continue

        out[slug] = {
            "bands": bands,
            "sources": [
                {"name": o["source"], "url": o.get("url"), "retrievedAt": o["retrievedAt"]}
                for o in obs
            ],
            "retrievedAt": max(o["retrievedAt"] for o in obs),
            # 1つでも人の目で確認していない観測値があれば暫定値として扱う。
            "verified": all(o.get("verified") is True for o in obs),
        }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    wide = sum(1 for v in out.values() for b in v["bands"].values() if b["wideSpread"])
    print(f"{len(out)}駅ぶんの帯を書き出した → {os.path.relpath(OUT_FILE, ROOT)}")
    print(f"うち出典間の開きが3万円以上の間取り: {wide}件")


if __name__ == "__main__":
    main()
