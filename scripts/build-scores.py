#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
機械で出せるスコア軸を全駅ぶん計算する。

出力: data/computed/scores.json

計算しているのは次の軸。
  commute            主要オフィス街への到達しやすさ
  transitConvenience 路線数と事業者の多様性
  shopping           徒歩圏のスーパーの数と価格帯の幅
  healthcare         徒歩圏のクリニック・薬局と、総合病院までの距離
  nature             徒歩圏の公園の数
  food / cafe / nightlife / fitness  徒歩圏の飲食店・カフェ・酒場・ジムの数
  rentValue          通勤の速さに対する家賃の安さ
  quietness          飲み屋・飲食店の少なさから見た静かさ
  family             公園・日常の医療・スーパーの多さと、坂の少なさ
  singleLife         外食とカフェで生活を完結させやすいか
  disaster           浸水想定区域に入る地点の少なさ

施設の数は OpenStreetMap（scripts/fetch-pois.py）から数える。
OSM は地域によって登録の密度が違うため、数そのものではなく、
23区内の駅どうしの相対的な位置（何割の駅より多いか）で点をつける。

残る3軸（safety・internationalFriendliness・style）は、犯罪統計や人の判断が要る。
どの軸を何で埋めるかは docs/03-scoring.md §4、進め方は docs/11-all-stations-plan.md。

  python3 scripts/build-scores.py
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clamp(v):
    return max(0, min(100, int(round(v))))


def commute_score(minutes_by_hub):
    """
    7つのオフィス駅への所要時間の平均から出す。
    1箇所に速いだけの駅より、どこへでも出やすい駅を高く評価する。

    直線だと平均50分あたりで0に張り付き、郊外側の駅を区別できなくなる。
    8分を100として、そこから24分ごとに半減する曲線にした。
      平均 8分=100 / 20分=71 / 32分=50 / 44分=35 / 56分=25
    """
    mean = sum(minutes_by_hub) / len(minutes_by_hub)
    return clamp(100 * (0.5 ** ((mean - 8) / 24)))


# 路線数から決まる基礎点。4路線を超えると効用が頭打ちになるので上げ幅を絞る。
LINES_BASE = {0: 0, 1: 32, 2: 52, 3: 68, 4: 80, 5: 88}


def transit_score(line_count, operator_count):
    base = LINES_BASE.get(line_count, 93 if line_count >= 6 else 0)
    # 事業者がまたがるほど行き先の幅が広い（直通・振替の選択肢が増える）。
    return clamp(base + min(10, max(0, operator_count - 1) * 5))


def percentile_scores(values_by_slug, floor=0):
    """
    施設の数を、駅どうしの相対的な位置で点にする。
    OSM の登録密度は地域差が大きく、数の絶対値をそのまま点にはできない。
    「23区内の駅の中で何割の駅より多いか」なら、その偏りの影響を受けにくい。
    施設が1つもない駅は floor 点にする。
    """
    ranked = sorted(v for v in values_by_slug.values() if v > 0)
    out = {}
    for slug, v in values_by_slug.items():
        if v <= 0:
            out[slug] = floor
            continue
        # 自分以下の駅が何割あるか
        below = sum(1 for r in ranked if r < v)
        same = sum(1 for r in ranked if r == v)
        pct = (below + same / 2) / len(ranked)
        out[slug] = clamp(pct * 100)
    return out


def hospital_nearness(nearest_hospital_m):
    """総合病院までの近さ。500mを満点、2.5kmで0になる直線。"""
    if nearest_hospital_m is None:
        return 0.0
    return max(0.0, min(1.0, (2500 - nearest_hospital_m) / 2000))


def flood_score(hz):
    """
    浸水想定区域に入る地点の少なさ。駅と半径400mの8方位、計9地点を見る。
    区域に入る地点が少ないほど高い。深さの想定が大きいときはさらに引く。

    ここで点にしているのは「想定最大規模の雨が降ったときの試算」であり、
    ふだん浸水する場所かどうかではない（docs/13 ルール32）。
    """
    if not hz:
        return None
    DEPTH_PENALTY = {None: 0, "0.5m未満": 4, "0.5〜3m": 12, "3〜5m": 22,
                     "5〜10m": 32, "10〜20m": 40, "20m以上": 45}
    worst = 0
    covered = 0
    total = 0
    for kind in ("flood", "hightide", "tsunami"):
        k = hz.get(kind)
        if not k:
            continue
        total = max(total, k.get("aroundTotal") or 0)
        covered = max(covered, k.get("aroundCount") or 0)
        worst = max(worst, DEPTH_PENALTY.get(k.get("deepest"), 20))
    if total == 0:
        return None
    # 区域に入る地点の割合に、想定される深さの重みを掛けて引く。
    # 「9地点すべてが区域内」を一律に0点にすると、0.5〜3mの駅と5〜10mの駅が
    # 同じ点になり、どちらが深いのかを読み取れなくなる。
    return clamp(100 - covered / total * (50 + worst))


def rent_value_scores(one_room_by_slug, commute_by_slug):
    """
    通勤の速さに対する家賃の安さ。

    家賃の絶対額をそのまま点にすると、郊外の駅が並んで上位を占め、
    「都心に近いのに安い駅」という、読み手がいちばん知りたい駅が沈む。
    通勤スコアから予想される家賃と、実際の家賃の差（残差）を点にする。
    """
    pairs = [(commute_by_slug[s], v) for s, v in one_room_by_slug.items()
             if s in commute_by_slug]
    if len(pairs) < 20:
        return {}
    n = len(pairs)
    mx = sum(c for c, _ in pairs) / n
    my = sum(r for _, r in pairs) / n
    var = sum((c - mx) ** 2 for c, _ in pairs)
    if var == 0:
        return {}
    slope = sum((c - mx) * (r - my) for c, r in pairs) / var
    residual = {}
    for s, rent in one_room_by_slug.items():
        if s not in commute_by_slug:
            continue
        expected = my + slope * (commute_by_slug[s] - mx)
        # 予想より安いほど割安。符号を反転して「安さ」にする。
        residual[s] = expected - rent
    lo = min(residual.values())
    return percentile_scores({s: v - lo + 1 for s, v in residual.items()})


def main():
    roster = json.load(
        open(os.path.join(ROOT, "data", "roster", "stations.json"), encoding="utf-8")
    )
    commutes = json.load(
        open(os.path.join(ROOT, "data", "computed", "commutes.json"), encoding="utf-8")
    )
    lines = {
        l["id"]: l
        for l in json.load(
            open(os.path.join(ROOT, "data", "reference", "lines.json"), encoding="utf-8")
        )
    }

    # 施設データ。まだ取れていなければ、その軸は飛ばす。
    poi_path = os.path.join(ROOT, "data", "computed", "pois.json")
    pois = (json.load(open(poi_path, encoding="utf-8"))["stations"]
            if os.path.exists(poi_path) else {})

    def computed(name, key=None):
        path = os.path.join(ROOT, "data", "computed", name)
        if not os.path.exists(path):
            return {}
        doc = json.load(open(path, encoding="utf-8"))
        return doc[key] if key else doc

    terrain = computed("terrain.json", "stations")
    hazard = computed("hazard.json", "stations")
    bands = computed("rent-bands.json")

    TIER_OF = {"オオゼキ": "d", "業務スーパー": "d", "西友": "d", "オーケー": "d",
               "赤札堂": "d", "ロピア": "d", "Big-A": "d", "ビッグ・エー": "d",
               "肉のハナマサ": "d", "食品館あおば": "d", "サンディ": "d", "アコレ": "d",
               "成城石井": "p", "紀ノ国屋": "p", "明治屋": "p", "クイーンズ伊勢丹": "p",
               "福島屋": "p", "北野エース": "p", "プレッセ": "p", "三浦屋": "p",
               "信濃屋": "p", "ピカール": "p"}

    def tier(name):
        for k, v in TIER_OF.items():
            if k in name:
                return v
        return "s"

    counts = {c: {} for c in ("restaurant", "cafe", "bar", "gym", "park")}
    extras = {}
    for station in roster:
        lst = pois.get(station["slug"], [])
        by_cat = {}
        for p in lst:
            by_cat.setdefault(p["category"], []).append(p)
        for c in counts:
            counts[c][station["slug"]] = len(by_cat.get(c, []))
        hospitals = by_cat.get("hospital", [])
        extras[station["slug"]] = {
            "shops": [tier(p["name"]) for p in by_cat.get("supermarket", [])],
            "clinics": len(by_cat.get("clinic", [])),
            "pharmacies": len(by_cat.get("pharmacy", [])),
            "nearestHospitalM": min((h["distanceM"] for h in hospitals), default=None),
            "hasPoi": bool(lst),
        }

    # 数の絶対値で点をつけると、東京では上位に固まって差がつかない。
    # 実際、スーパーを6軒で頭打ちにしたところ446駅中236駅が90点台になった。
    # どの軸も駅どうしの相対的な位置で点にする。
    counts["supermarket"] = {s["slug"]: len(extras[s["slug"]]["shops"]) for s in roster}
    counts["dailyCare"] = {s["slug"]: extras[s["slug"]]["clinics"]
                                      + extras[s["slug"]]["pharmacies"] for s in roster}
    pct = {c: percentile_scores(counts[c]) for c in counts}

    out = {}
    # ファミリー適性は5つの材料の重みつき平均なので、そのままだと真ん中に寄り、
    # 駅どうしの差が読み取れない。ほかの軸と同じく相対的な位置に直す。
    family_raw = {}
    for station in roster:
        scores = {}

        entries = commutes.get(station["slug"])
        if entries:
            scores["commute"] = commute_score([e["minutes"] for e in entries])

        ids = station["lineIds"]
        operators = {lines[i]["operator"] for i in ids if i in lines}
        scores["transitConvenience"] = transit_score(len(ids), len(operators))

        e = extras.get(station["slug"])
        if e and e["hasPoi"]:
            slug = station["slug"]
            # 買い物は店の数だけでなく価格帯の幅も見る。
            # 安い店と高い店を選べるほうが、日々の出費を調整しやすい。
            variety = min(1.0, len(set(e["shops"])) / 3.0)
            scores["shopping"] = clamp(pct["supermarket"][slug] * 0.75 + variety * 25)
            # 医療は、日常のかかりつけと、いざというときの総合病院の両方を見る。
            scores["healthcare"] = clamp(
                pct["dailyCare"][slug] * 0.6
                + hospital_nearness(e["nearestHospitalM"]) * 40)
            scores["nature"] = pct["park"][slug]
            for axis, cat in (("food", "restaurant"), ("cafe", "cafe"),
                              ("nightlife", "bar"), ("fitness", "gym")):
                if any(counts[cat].values()):
                    scores[axis] = pct[cat][slug]

            # 静かさは、夜に人が集まる店の少なさで見る。
            # 幹線道路と線路の騒音はデータが無いため、ここには入っていない。
            scores["quietness"] = clamp(
                100 - (pct["bar"][slug] * 0.65 + pct["restaurant"][slug] * 0.35))

            # ファミリー適性は、公園・日常の医療・スーパーの多さと、
            # ベビーカーで歩ける平坦さ、それに夜の店の少なさを合わせる。
            flat = {"flat": 1.0, "some": 0.55, "hilly": 0.2}.get(
                (terrain.get(slug) or {}).get("slope"), 0.55)
            family_raw[slug] = (
                pct["park"][slug] * 0.3
                + pct["dailyCare"][slug] * 0.2
                + pct["supermarket"][slug] * 0.2
                + flat * 15
                + (100 - pct["bar"][slug]) * 0.15)

            # 一人暮らし適性は、自炊しなくても生活が回るかで見る。
            scores["singleLife"] = clamp(
                pct["restaurant"][slug] * 0.35
                + pct["cafe"][slug] * 0.2
                + pct["supermarket"][slug] * 0.2
                + scores.get("commute", 50) * 0.25)

        fs = flood_score(hazard.get(station["slug"]))
        if fs is not None:
            scores["disaster"] = fs

        if scores:
            out[station["slug"]] = scores

    for slug, v in percentile_scores(family_raw).items():
        if slug in out:
            out[slug]["family"] = v

    # 家賃コスパは、全駅の家賃と通勤スコアの関係から出すため、ここでまとめて入れる。
    one_room = {slug: v["bands"]["oneRoom"]["mean"]
                for slug, v in bands.items()
                if isinstance(v, dict) and "oneRoom" in v.get("bands", {})}
    commute_by_slug = {slug: sc["commute"] for slug, sc in out.items() if "commute" in sc}
    for slug, v in rent_value_scores(one_room, commute_by_slug).items():
        if slug in out:
            out[slug]["rentValue"] = v

    path = os.path.join(ROOT, "data", "computed", "scores.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    by_name = {s["slug"]: s["nameJa"] for s in roster}
    ranked = sorted(out.items(), key=lambda kv: -kv[1].get("commute", 0))
    print(f"スコアを計算した駅: {len(out)} / {len(roster)}")
    print("\n通勤スコア 上位10")
    for slug, sc in ranked[:10]:
        print(f"  {by_name[slug]:<12} commute={sc.get('commute')} transit={sc['transitConvenience']}")
    print("\n通勤スコア 下位10")
    for slug, sc in ranked[-10:]:
        print(f"  {by_name[slug]:<12} commute={sc.get('commute')} transit={sc['transitConvenience']}")

    dist = collections.Counter(v["transitConvenience"] // 10 * 10 for v in out.values())
    print("\n乗換利便性の分布")
    for k in sorted(dist):
        print(f"  {k:>3}台: {dist[k]}駅")


if __name__ == "__main__":
    main()
