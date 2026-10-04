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
  quietness          人の音（駅から300m以内の飲み屋・飲食店）と、
                     車の音（幹線道路・高速道路までの距離と種別）の両方から出す
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


def hub_size(pct_passengers):
    """乗降客数の相対的な位置を、「大きな駅である度合い」に直す。

    パーセンタイルをそのまま使うと、1日2万人しか乗り降りしない駅にも
    35前後の値が付く。駅から300m以内に酒場が1軒も無い西巣鴨の静かさが
    65点から42点まで下がり、下げすぎになった。
    上位3割に入る駅だけが効くように、70パーセンタイルを起点に引き直す。
    """
    return max(0.0, (pct_passengers - 70) / 0.30)


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


def rent_index(bands):
    """
    駅ごとの家賃水準を、間取りの違いを均した1つの指数にする。

    ワンルームの相場だけを見ると、駅によって集計の対象がそろっておらず、
    中目黒のワンルームが清澄白河より安く出るような逆転が起きる。
    間取りごとに全駅の中央値を出し、その中央値の何倍かを平均する。
    """
    layouts = ("oneRoom", "oneK", "oneLDK", "twoLDK")
    median = {}
    for layout in layouts:
        vals = sorted(v["bands"][layout]["mean"] for v in bands.values()
                      if isinstance(v, dict) and layout in v.get("bands", {}))
        if vals:
            median[layout] = vals[len(vals) // 2]
    out = {}
    for slug, v in bands.items():
        if not isinstance(v, dict):
            continue
        ratios = [v["bands"][l]["mean"] / median[l]
                  for l in layouts if l in median and l in v.get("bands", {})]
        if ratios:
            out[slug] = sum(ratios) / len(ratios)
    return out


def rent_value_scores(index_by_slug, commute_by_slug):
    """
    通勤の速さに対する家賃の安さ。

    家賃の絶対額をそのまま点にすると、郊外の駅が並んで上位を占め、
    「都心に近いのに安い駅」という、読み手がいちばん知りたい駅が沈む。
    通勤スコアから予想される家賃水準と、実際の家賃水準の差（残差）を点にする。
    """
    pairs = [(commute_by_slug[s], v) for s, v in index_by_slug.items()
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
    for s, rent in index_by_slug.items():
        if s not in commute_by_slug:
            continue
        expected = my + slope * (commute_by_slug[s] - mx)
        # 予想より安いほど割安。符号を反転して「安さ」にする。
        residual[s] = expected - rent
    lo = min(residual.values())
    return percentile_scores({s: v - lo + 1 for s, v in residual.items()})


def road_noise(rec):
    """
    車の音の大きさ。0〜100で、大きいほどうるさい。

    道路の格（高速＞幹線＞主要＞準主要）と、駅からの距離で決める。
    音は距離とともに急に小さくなるので、直線ではなく、
    50mで7割、100mで5割、200mで3割、300mでほぼ0になる曲線を使う。

    繁華街から離れていても幹線道路に面している駅がある。岩本町は靖国通りまで5m、
    昭和通りまで39m、首都高速1号上野線まで46mで、酒場は神田の半分以下だが、
    車の音は一日中続く（docs/13-japanese-style-rules.md ルール41）。
    """
    if not rec:
        return None
    WEIGHT = {"motorway": 100, "trunk": 82, "primary": 62, "secondary": 34}
    worst = 0.0
    for cls, w in WEIGHT.items():
        v = rec.get(cls)
        if not v:
            continue
        near = max(0.0, 1 - (min(v["m"], 300) / 300) ** 0.6)
        # 車線が多いほど交通量も多い。4車線以上を1割増しにする。
        lanes = v.get("lanes") or 2
        worst = max(worst, w * near * (1.1 if lanes >= 4 else 1.0))
    return clamp(worst)


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
    roads = computed("roads.json", "stations")
    hazard = computed("hazard.json", "stations")
    bands = computed("rent-bands.json")
    passengers = computed("passengers.json", "stations")

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

    # 静かさだけは半径300mで数える。
    # ほかの軸は「歩いて行ける選択肢の多さ」なので800m圏でよいが、静かさは
    # 「駅を出たところがどうか」である。800m圏だと、都心では隣の駅と圏が重なって
    # 差が消える。淡路町と神田は800m圏のPOIの54%が同じもので、酒場の数は
    # 淡路町298軒・神田211軒と、実際とは逆に出ていた。250m圏で数え直すと
    # 淡路町26軒・神田69軒になり、街を歩いた感覚と向きがそろう。
    NEAR_M = 300
    counts = {c: {} for c in ("restaurant", "cafe", "bar", "gym", "park",
                              "school", "kindergarten", "childcare")}
    near = {"bar": {}, "restaurant": {}, "cafe": {}}
    extras = {}
    for station in roster:
        lst = pois.get(station["slug"], [])
        by_cat = {}
        for p in lst:
            by_cat.setdefault(p["category"], []).append(p)
        for c in counts:
            counts[c][station["slug"]] = len(by_cat.get(c, []))
        for c in near:
            near[c][station["slug"]] = sum(
                1 for p in by_cat.get(c, []) if p["distanceM"] <= NEAR_M)
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
    # 幼稚園と保育園は、どちらも小さい子どもの預け先なのでまとめて数える
    counts["nursery"] = {s["slug"]: counts["kindergarten"][s["slug"]]
                                    + counts["childcare"][s["slug"]] for s in roster}
    # 駅の大きさ。1日あたりの乗降客数（国土数値情報 S12）。
    # 店の登録の偏りに引きずられない物差しとして使う
    counts["passengers"] = {s["slug"]: passengers.get(s["slug"], {}).get("daily", 0)
                            for s in roster}
    pct = {c: percentile_scores(counts[c]) for c in counts}
    pct_near = {c: percentile_scores(near[c]) for c in near}

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
            # 外食・カフェ・夜の店は、800m圏だけで測ると隣の駅と圏が重なって
            # 駅ごとの差が消える。門前仲町は駅から300m以内に55軒あるのに対し、
            # 清澄白河は14軒だが、800m圏では79軒と95軒で逆転していた。
            # 駅を出てすぐの多さ（300m）と、歩いて行ける選択肢の多さ（800m）を
            # 両方見る。ジムは目的地まで歩くものなので800m圏だけで測る。
            for axis, cat in (("food", "restaurant"), ("cafe", "cafe"),
                              ("nightlife", "bar")):
                if any(counts[cat].values()):
                    scores[axis] = clamp(pct_near[cat][slug] * 0.55
                                         + pct[cat][slug] * 0.45)
            if any(counts["gym"].values()):
                scores["fitness"] = pct["gym"][slug]

            # 静かさは、人の音と車の音の両方から出す。
            # 人の音は駅から300m以内の酒場と飲食店の数、車の音は幹線道路・高速道路
            # までの距離と種別で見る。鉄道の音は、地上か地下かのデータが無いので入らない。
            # 店の数だけで人の音を測ると、大きな駅を拾えない。東京駅は300m以内の
            # 酒場が1軒しか登録されておらず、静かさが76点に出ていた。
            # 1日79万人が乗り降りする駅の駅前は、静かではない。
            # 店の多さと駅の大きさの、高いほうを人の音として使う。
            people = max(
                pct_near["bar"][slug] * 0.65 + pct_near["restaurant"][slug] * 0.35,
                hub_size(pct["passengers"].get(slug, 0)))
            car = road_noise(roads.get(slug))
            scores["quietness"] = clamp(
                100 - (people * 0.55 + car * 0.45) if car is not None else 100 - people)

            # ファミリー適性は、子どもに関わる施設の数を主役に置く。
            #
            # 以前は公園・クリニック・スーパー・平坦さだけで出していたため、
            # 駅から300m以内に酒場が63軒ある高円寺が、全458駅の94パーセンタイルに
            # 出ていた。子どもに関する数字が1つも入っていなかったのが原因である
            # （docs/14-audience-segments.md §1）。
            #
            # 学校は歩いて通う距離（1,500m）、幼稚園と保育園は送り迎えの距離
            # （1,000m）で数える。夜の店の多さは重み0.15では効かなかったので、
            # 0.28まで上げた。子どもと暮らす場所を選ぶうえで、
            # 駅前が飲み屋街かどうかは学校の数と同じくらい大きい。
            #
            # ただし酒場の数だけでは、池袋のような大きな駅を拾えない。
            # OpenStreetMap に登録されている池袋の酒場は、駅から800m以内で53軒である。
            # 御徒町の728軒、淡路町の298軒と比べて桁が違い、実態と合わない
            # （docs/03-scoring.md §4.4）。半径を変えても直らない。
            # そこで乗降客数も見る。1日193万人が使う駅は、酒場の登録が少なくても
            # 子どもと暮らす場所としては落ち着いた環境ではない。
            # 酒場の多さと駅の大きさの、高いほうを減点に使う。
            flat = {"flat": 1.0, "some": 0.55, "hilly": 0.2}.get(
                (terrain.get(slug) or {}).get("slope"), 0.55)
            # 施設の多さを出したうえで、繁華街・大きな駅であるぶんを割り引く。
            # 引き算にすると、池袋のように施設が多い駅では引ききれない。
            # 1日193万人が使う駅は、学校が34校あっても
            # 子どもと暮らす場所としては落ち着いた環境ではない。
            facilities = (
                pct["school"][slug] * 0.26
                + pct["nursery"][slug] * 0.26
                + pct["park"][slug] * 0.22
                + pct["supermarket"][slug] * 0.13
                + flat * 13)
            hub = max(pct_near["bar"][slug],
                      hub_size(pct["passengers"].get(slug, 0))) / 100
            family_raw[slug] = facilities * (1 - 0.55 * hub)

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
    commute_by_slug = {slug: sc["commute"] for slug, sc in out.items() if "commute" in sc}
    index = rent_index(bands)
    for slug, v in rent_value_scores(index, commute_by_slug).items():
        if slug in out:
            out[slug]["rentValue"] = v

    # 家賃コスパ（rentValue）は、同じ利便性の駅と比べた安さである。
    # 池袋はワンルーム8万9千円に対して通勤の利便性がきわめて高いため、
    # コスパでは100点になる。それは正しいが、「家賃を抑えたい」人が見たいのは
    # 絶対額のほうである。そこで、利便性を見ない安さの軸も持つ。
    # percentile_scores は「多いほど高い点」なので、家賃は向きが逆になる。
    # 家賃水準の順位を出してから100から引く
    for slug, v in percentile_scores(index).items():
        if slug in out:
            out[slug]["rentLow"] = 100 - v

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
