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
  rentValue / rentLow  通勤の速さに対する家賃の安さと、絶対額の安さ
  quietness          人の音（駅から300m以内の飲み屋・飲食店の数と、用途地域の容積率）と、
                     車の音（幹線道路・高速道路までの距離と種別）の両方から出す
  family             学校・園・公園・スーパーが歩ける範囲に足りているかと、
                     坂の少なさ、街の落ち着き（粗暴犯の認知件数）
  singleLife         外食とカフェで生活を完結させやすいか
  disaster           浸水想定区域に入る地点の少なさ
  safety             警視庁の町丁別認知件数（scripts/fetch-crime.py）

施設の数は OpenStreetMap（scripts/fetch-pois.py）から数える。
OSM は地域によって登録の密度が違うため、数そのものではなく、
23区内の駅どうしの相対的な位置（何割の駅より多いか）で点をつける。
駅前が繁華街か住宅地かは OSM では測りきれないので、用途地域（scripts/fetch-zoning.py）と
犯罪の認知件数（scripts/fetch-crime.py）も併せて使う。

残る2軸（internationalFriendliness・style）は、人の判断が要る。
どの軸を何で埋めるかは docs/03-scoring.md §4、進め方は docs/11-all-stations-plan.md。

  python3 scripts/build-scores.py
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def built_density(pct_far):
    """容積率の相対的な位置を、「高い建物が建ち並ぶ街である度合い」に直す。

    以前は乗降客数を使っていたが、乗降客数は駅を通り抜ける人の数であって、
    駅前がどういう街かを表さない。荻窪は1日21万人が乗り降りするが
    駅のすぐ外は住宅地で、新大久保は7万人だが駅前は商業地域である。
    この2駅を乗降客数では区別できず、荻窪のほうが繁華街だと判定していた。

    容積率は都市計画法にもとづいて区が定めた値で、地図を作った人の多さにも
    乗り換え客の数にも左右されない（data/computed/zoning.json）。
    上位3割に入る駅だけが効くように、70パーセンタイルを起点に引き直す。
    """
    return max(0.0, (pct_far - 70) / 0.30)


def saturate(count, enough):
    """「足りているかどうか」に直す。enough を超えたぶんは数えない。

    学校や保育園は、数が多いほどよいものではない。歩ける範囲にいくつかあれば
    足りる。数をそのまま相対評価にすると、人口密度の高い都心が上位に来る。
    実際、新大久保は駅から1,500m以内に小中学校が40校あり、等々力の21校より
    多い。これは新大久保のほうが子育てに向くという意味ではなく、
    人口密度が高いという意味でしかない。
    """
    return min(1.0, count / enough)


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
    zoning = computed("zoning.json", "stations")
    crime = computed("crime.json", "stations")

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
    pct = {c: percentile_scores(counts[c]) for c in counts}
    pct_near = {c: percentile_scores(near[c]) for c in near}

    # 用途地域の容積率。駅前がどれだけ高い建物の建つ街として計画されているか。
    pct_far = percentile_scores(
        {s["slug"]: (zoning.get(s["slug"]) or {}).get("far") or 0 for s in roster})
    # 警視庁の町丁別認知件数。1町丁あたりに直してから駅どうしで比べる。
    def per_place(key):
        return {s["slug"]: (crime.get(s["slug"]) or {}).get("perPlace", {}).get(key)
                for s in roster
                if (crime.get(s["slug"]) or {}).get("perPlace", {}).get(key) is not None}
    pct_violent = percentile_scores(per_place("violent"))
    pct_allCrime = percentile_scores(per_place("total"))

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
            # 店の多さと、容積率から出した街の密度の、高いほうを人の音として使う。
            people = max(
                pct_near["bar"][slug] * 0.65 + pct_near["restaurant"][slug] * 0.35,
                built_density(pct_far[slug]))
            car = road_noise(roads.get(slug))
            scores["quietness"] = clamp(
                100 - (people * 0.55 + car * 0.45) if car is not None else 100 - people)

            # ファミリー適性は、「学校と園が歩ける範囲に足りているか」と
            # 「街が落ち着いているか」の2つから出す。
            #
            # 施設の数をそのまま駅どうしで比べていたときは、新大久保が
            # 全458駅の75パーセンタイルに出ていた。駅から1,500m以内に
            # 小中学校が40校、保育園と幼稚園が16園あり、地形も平坦だからである。
            # しかし40校あるのは人口密度が高いからで、子育てに向くという意味ではない。
            # 等々力は21校だが、どちらが子どもと暮らしやすいかは言うまでもない。
            # そこで、歩ける範囲にいくつかあれば足りるものとして数え、
            # 足りたぶんから先は加点しない（saturate）。
            #
            # 落ち着きは、警視庁の町丁別の粗暴犯（暴行・傷害・脅迫・恐喝）の
            # 認知件数で見る。駅から800m以内の1町丁あたりで、新大久保は36.2件、
            # 荻窪は2.5件である（docs/03-scoring.md §4.5）。
            # 店の数でも乗降客数でも、この2駅を区別できなかった。
            flat = {"flat": 1.0, "some": 0.6, "hilly": 0.25}.get(
                (terrain.get(slug) or {}).get("slope"), 0.6)
            facilities = (
                saturate(counts["school"][slug], 12) * 28
                + saturate(counts["nursery"][slug], 10) * 28
                + saturate(counts["park"][slug], 15) * 18
                + saturate(counts["supermarket"][slug], 5) * 12
                + flat * 14)
            # 施設が足りていても、繁華街であるぶんを割り引く。引き算にすると、
            # 施設の多い駅では引ききれないので掛け算にする。
            hub = max(pct_violent.get(slug, 50),
                      built_density(pct_far[slug])) / 100
            family_raw[slug] = facilities * (1 - 0.6 * hub)

            # 一人暮らし適性は、自炊しなくても生活が回るかで見る。
            scores["singleLife"] = clamp(
                pct["restaurant"][slug] * 0.35
                + pct["cafe"][slug] * 0.2
                + pct["supermarket"][slug] * 0.2
                + scores.get("commute", 50) * 0.25)

            # 治安は、警視庁の町丁別認知件数から出す。
            # 粗暴犯を主に見る。総合計には自転車盗が多く含まれ、
            # 駅前に自転車が多い街ほど件数が増えるため、主役には置かない。
            if station["slug"] in pct_violent:
                scores["safety"] = clamp(
                    100 - (pct_violent[slug] * 0.6 + pct_allCrime[slug] * 0.4))

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
