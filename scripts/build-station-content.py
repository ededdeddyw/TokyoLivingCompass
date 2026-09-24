#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出典のあるデータだけを使って、全458駅ぶんのコンテンツを組み立てる。

  python3 scripts/build-station-content.py --dry-run
  python3 scripts/build-station-content.py
  python3 scripts/build-station-content.py --locale en

**書き手の記憶による記述は1文字も入れない。**入るのは次のデータから導ける記述だけ。

  所要時間  data/computed/commutes.json  （駅間距離と路線種別からの計算）
  スコア    data/computed/scores.json
  標高      data/computed/terrain.json   （国土地理院）
  浸水想定  data/computed/hazard.json    （重ねるハザードマップ）
  周辺施設  data/computed/pois.json      （OpenStreetMap・ODbL）
  家賃      data/computed/rent-bands.json（3社の相場の平均）

したがって、街のようす（faces）・夜の帰り道（nightWalk）・住民層（residents）・
物件の傾向（housingStock）・これからどう変わるか（outlook）は書かない。
これらはデータが無く、書けば記憶で書くことになる（CLAUDE.md ルール35）。
16層のうち埋まるのは、データのある層だけである。

すでに人が書いた駅（authoredBy が draft か human）と、
文章としてローカライズした駅（ai-localized）は上書きしない。
ただし近くの駅の節（neighbours）だけは、距離・所要時間・家賃の差から組み立てる
データだけの層なので、人が書いた駅でも作り直す。人が「比べたい駅」として選んだ駅は
alternatives に入っており、この処理では触らない。

言語ごとに違うのは文型だけで、組み立ての手順は変わらない。
文型は scripts/station_phrases.py にまとめてある。
"""
import argparse
import json
import math
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from station_phrases import PHRASES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")

DISCOUNT = ["オオゼキ", "業務スーパー", "ロピア", "西友", "オーケー", "赤札堂", "アコレ",
            "ビッグ・エー", "Big-A", "肉のハナマサ", "食品館あおば", "サンディ", "A･Colle"]
PREMIUM = ["成城石井", "紀ノ国屋", "明治屋", "クイーンズ伊勢丹", "福島屋", "北野エース",
           "プレッセ", "三浦屋", "信濃屋", "Shinanoya", "ピカール", "Picard", "Bio c", "Bio C"]


def tier_of(name):
    if any(w in name for w in PREMIUM):
        return "premium"
    if any(w in name for w in DISCOUNT):
        return "discount"
    return "standard"


def load(p):
    return json.load(open(os.path.join(D, p), encoding="utf-8"))


def line_name(name):
    """
    路線名を文章に載る形にする。ekidata の名前は「JR常磐線(上野～取手)」のように
    区間を括弧で添えるが、文中では読みにくいので区間だけ落とす。
    「JR中央線(快速)」の括弧は快速と各駅停車を分ける情報なので残す。
    """
    return re.sub(r"\([^（）()]*～[^（）()]*\)", "", name)


def haversine_m(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = math.radians(b["lat"] - a["lat"])
    dl = math.radians(b["lon"] - a["lon"])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def join(p, items):
    """語を並べる。英語だけ最後のつなぎが and になる。"""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return p["listSep"].join(items[:-1]) + p["lastSep"] + items[-1]


def chunk(items, limit=40):
    """並べると長くなる語を、文に収まる塊に切る。1文が長いと読みにくいため。"""
    out, cur, n = [], [], 0
    for it in items:
        if cur and n + len(it) + 1 > limit:
            out.append(cur)
            cur, n = [], 0
        cur.append(it)
        n += len(it) + 1
    if cur:
        out.append(cur)
    return out


def word(p, key, n):
    """数に応じた語形を返す。英語だけ単数と複数で変わる。"""
    forms = p["words"][key]
    return forms[0] if n == 1 else forms[1]


def five(score):
    """0〜100のスコアを5点満点に直す。src/lib/scoring.ts の toFivePoint と同じ式。"""
    return round(min(5.0, max(1.0, 1 + score / 25)) * 2) / 2


def band_key(prefix, score):
    """スコアを5段階の文型キーにする（leadHazard5 〜 leadHazard1）。"""
    v = five(score)
    step = 5 if v >= 4.5 else 4 if v >= 3.5 else 3 if v >= 2.5 else 2 if v >= 1.5 else 1
    return f"{prefix}{step}"


# 街の性格タグ。スコアと路線数と地形から決まる。
# 条件は「23区の駅の中で上位／下位2割」を目安に置いている。
# 並び順がそのまま表示順になるので、街を言い当てる力が強いものを先に置く。
TAG_RULES = [
    # 繁華街の2段階は station_tags() が先に決める。ここでは扱わない。
    ("lively", lambda sc, st, ter: sc.get("nightlife", 0) >= 80 and sc.get("food", 0) >= 75),
    ("quiet", lambda sc, st, ter: sc.get("quietness", 0) >= 80),
    ("goodValue", lambda sc, st, ter: sc.get("rentValue", -1) >= 80),
    ("pricey", lambda sc, st, ter: 0 <= sc.get("rentValue", -1) <= 20),
    ("fastToCenter", lambda sc, st, ter: sc.get("commute", 0) >= 80),
    ("manyLines", lambda sc, st, ter: len(st["lineIds"]) >= 4),
    ("singleLine", lambda sc, st, ter: len(st["lineIds"]) == 1),
    ("floodArea", lambda sc, st, ter: sc.get("disaster", 100) <= 35),
    ("lowFlood", lambda sc, st, ter: sc.get("disaster", 0) >= 90),
    ("shoppingEasy", lambda sc, st, ter: sc.get("shopping", 0) >= 80),
    ("diningRich", lambda sc, st, ter: sc.get("food", 0) >= 85),
    ("cafeRich", lambda sc, st, ter: sc.get("cafe", 0) >= 85),
    ("lateNight", lambda sc, st, ter: sc.get("nightlife", 0) >= 85),
    ("parkNear", lambda sc, st, ter: sc.get("nature", 0) >= 85),
    ("medicalRich", lambda sc, st, ter: sc.get("healthcare", 0) >= 90),
    # familyFriendly は外してある。いまの family スコアには子どもに関する数字が
    # 1つも入っておらず、駅から300m以内に酒場が63軒ある高円寺が94点で出ていた。
    # 学校と保育園を取ってから付け直す（docs/14-audience-segments.md §4）。
    ("singleFriendly", lambda sc, st, ter: sc.get("singleLife", 0) >= 85),
    ("flat", lambda sc, st, ter: ter.get("slope") == "flat"),
    ("hilly", lambda sc, st, ter: ter.get("slope") == "hilly"),
]
# 同時に立つと読み手が混乱する組み合わせ。先に出たほうを残す。
TAG_CONFLICTS = [("lively", "quiet"), ("majorHub", "quiet"), ("someBustle", "quiet"),
                 ("majorHub", "lively"), ("someBustle", "lively"),
                 ("goodValue", "pricey"), ("floodArea", "lowFlood"),
                 ("flat", "hilly"), ("manyLines", "singleLine")]
MAX_TAGS = 6

# 6つに絞るとき、どれを残すか。住む街を決める人が先に知りたい順に並べる。
# TAG_RULES の並び順で切ると、街の性格を表すタグが後ろにあるせいで落ちる。
# singleFriendly は条件を満たす駅が28あるのに、1駅にしか付いていなかった。
TAG_ORDER = [
    "majorHub", "someBustle", "lively", "quiet",
    "goodValue", "pricey",
    "floodArea", "lowFlood",
    "fastToCenter", "manyLines", "singleLine",
    "familyFriendly", "singleFriendly",
    "shoppingEasy", "diningRich", "lateNight",
    "flat", "hilly",
    "cafeRich", "parkNear", "medicalRich",
]


# タグが足りない駅を埋めるとき、その駅で上のほうにある軸から順に見る。
# しきい値を全体で下げるのではなく、タグが2つ以下の駅にだけ、この表を使う。
FILL_TAGS = [
    ("quietness", "quiet"), ("rentValue", "goodValue"), ("disaster", "lowFlood"),
    ("commute", "fastToCenter"), ("singleLife", "singleFriendly"),
    ("shopping", "shoppingEasy"), ("food", "diningRich"), ("nightlife", "lateNight"),
    ("cafe", "cafeRich"), ("nature", "parkNear"), ("healthcare", "medicalRich"),
]
MIN_TAGS = 4        # ここを下回る駅だけ、下のしきい値で埋める
FILL_FLOOR = 65     # 全458駅の上位3分の1にあたる


def station_tags(sc, st, ter, ctx=None):
    picked = [t for t, ok in TAG_RULES if ok(sc, st, ter)]
    if ctx is not None:
        bustle = bustle_tag(st["slug"], ctx)
        if bustle:
            picked.insert(0, bustle)

    def drop_conflicts(tags):
        for a, b in TAG_CONFLICTS:
            if a in tags and b in tags:
                tags.remove(b if tags.index(a) < tags.index(b) else a)
        return tags

    drop_conflicts(picked)
    # タグが2つ以下だと、その駅が何も語らないページになる。門前仲町は
    # 「平坦」1つだけだった。しきい値を全体で下げると、どの駅も同じ顔になるので、
    # 足りない駅にだけ、その駅で上のほうにある軸から補う。
    if len(picked) < MIN_TAGS:
        for axis, tag in sorted(FILL_TAGS, key=lambda at: -sc.get(at[0], 0)):
            if len(picked) >= MIN_TAGS:
                break
            if tag in picked or sc.get(axis, 0) < FILL_FLOOR:
                continue
            trial = picked + [tag]
            if tag in drop_conflicts(list(trial)):
                picked = trial

    picked.sort(key=lambda t: TAG_ORDER.index(t) if t in TAG_ORDER else len(TAG_ORDER))
    return picked[:MAX_TAGS]


# 「大きな繁華街」は、よそから食事・買い物・飲みのためにわざわざ来る駅だけに付ける。
#
# 機械で決められない。半径300mの飲食店の数で並べると、上位は御徒町578・湯島544・
# 京成上野345・赤坂305・渋谷305 の順になり、新宿は173、池袋は101で上位に出てこない。
# 理由は2つある。
#   1. 隣の繁華街からあふれた店を数えてしまう（湯島と末広町は上野・御徒町の一部、
#      淡路町は神田と秋葉原の続き）
#   2. 新宿・池袋・上野は駅の範囲が広く、代表の座標が繁華街の中心から離れる。
#      商業の中身が百貨店や駅ビルで、OpenStreetMap では点1つにしかならない駅もある
#
# そこで、一覧は人が決め、データで裏を取る（ロースターの WARD_OVERRIDE と同じ扱い）。
# 根拠は docs/12-quality-standard.md に書く。
MAJOR_HUBS = {
    # 山手線沿い
    "shinjuku", "ikebukuro", "shibuya", "ebisu", "gotanda", "shimbashi", "ginza",
    "kanda", "akihabara", "ueno", "okachimachi",
    # 山手線の外側・内側で、よそから飲みに来る駅
    "roppongi", "koenji", "akabane", "kinshicho", "nakano", "kita-senju", "takadanobaba",
    "shimo-kitazawa", "kamata", "asakusa", "asakusa-tx", "sangen-jaya",
    # 買い物でよそから来る駅。飲食店の数では測れない
    "jiyugaoka",
}

# 「やや繁華街」は、駅前に店は多いが、よそから来る駅ではないところ。
#
# 店の数をそのまま全458駅で並べることはできない。OpenStreetMap の登録の細かさが
# 区によって大きく違うためである。駅から500m以内にある商業の建物の棟数は、
# 中央値で台東区205棟に対して板橋区9棟で、20倍以上の開きがある。
# この差は街の実態ではなく、地図を作る人の多さの差である。
#
# そこで、全体で並べるのをやめ、まわりの駅と比べてどれだけ突き出ているかで測る。
# 半径4km以内にある駅の中央値に対する倍率をとれば、区ごとの登録の細かさの差は
# 分子と分母の両方に効くので打ち消し合う。
BUSTLE_NEIGHBOUR_KM = 4.0
SOME_BUSTLE_RATIO = 3.0
# まわりの駅がどこも店の登録が少ない地域では、22軒の駅でも7倍に見えてしまう。
# 倍率だけでなく、実数でも下限を置く。300m以内60軒は、全458駅の上位2割にあたる。
SOME_BUSTLE_MIN_SHOPS = 60
# 分母が小さいと倍率が跳ねる。中央値がこれを下回る地域では、この値を分母に使う。
BUSTLE_FLOOR_SHOPS = 15.0
BUSTLE_FLOOR_LEVELS = 150.0


def bustle_ratio(slug, ctx):
    """まわりの駅と比べて、店と商業の建物がどれだけ多いか。倍率で返す。"""
    cache = ctx.setdefault("_bustleRatio", {})
    if slug in cache:
        return cache[slug]
    roster, shops, floors = ctx["rosterBySlug"], ctx["bustle"], ctx["floors"]
    here = roster.get(slug)
    if here is None:
        return 0.0
    near = [o for o in shops
            if haversine_m(here, roster[o]) <= BUSTLE_NEIGHBOUR_KM * 1000]
    mid_shop = max(statistics.median(shops[o] for o in near), BUSTLE_FLOOR_SHOPS)
    mid_floor = max(statistics.median(floors.get(o, 0) for o in near), BUSTLE_FLOOR_LEVELS)
    r = math.sqrt(max(shops[slug] / mid_shop, 0.01)
                  * max(floors.get(slug, 0) / mid_floor, 0.01))
    cache[slug] = r
    return r


def bustle_tag(slug, ctx):
    """繁華街のタグを決める。大きな繁華街・やや繁華街・なし の3段階。

    隣の大きな駅の続きにあたる駅にも「やや繁華街」は付ける。
    淡路町は神田と秋葉原の続きだが、駅前に店が多いこと自体は住む人に効くため。
    付けないのは「大きな繁華街」のほうである。
    """
    if slug in MAJOR_HUBS:
        return "majorHub"
    if slug not in ctx["bustle"]:
        return None
    if ctx["bustle"][slug] < SOME_BUSTLE_MIN_SHOPS:
        return None
    return "someBustle" if bustle_ratio(slug, ctx) >= SOME_BUSTLE_RATIO else None


def compare_lead(p, a, b, ctx):
    """
    2駅を比べた「一言でいうと」を組み立てる。

    誰にとっても向きが同じ軸から先に書く（ルール40）。
    家賃 → 浸水の想定 → 路線の数 → 都心への近さ → 医療 → 買い物 → 静かさ の順に見て、
    差がはっきりしている軸だけを採る。店の多さのように好みが分かれる軸は入れない。
    """
    sc, bands, roster = ctx["sc"], ctx["bands"], ctx["rosterBySlug"]
    if a not in roster or b not in roster:
        return None
    name_a, name_b = p["stationName"](roster[a]), p["stationName"](roster[b])

    def band(slug):
        v = bands.get(slug, {}).get("bands", {}).get("oneRoom")
        return v["mean"] if v else None

    # 差がこれ以上あるときだけ書く。小さな差を並べても判断の助けにならない。
    AXES = [("disaster", "cmpAxisDisaster", 12), ("commute", "cmpAxisCommute", 8),
            ("healthcare", "cmpAxisHealthcare", 15), ("shopping", "cmpAxisShopping", 15),
            ("quietness", "cmpAxisQuiet", 15)]
    wins_a, wins_b = [], []
    # 路線の数は、スコアではなく本数そのもので比べる
    la, lb = len(roster[a]["lineIds"]), len(roster[b]["lineIds"])
    if la - lb >= 1:
        wins_a.append(p["cmpAxisTransit"])
    elif lb - la >= 1:
        wins_b.append(p["cmpAxisTransit"])
    for axis, label, gap in AXES:
        va, vb = sc.get(a, {}).get(axis), sc.get(b, {}).get(axis)
        if va is None or vb is None:
            continue
        if va - vb >= gap:
            wins_a.append(p[label])
        elif vb - va >= gap:
            wins_b.append(p[label])

    # 片方が1つも上回らないと、「もう一方へ行け」としか読めない一言になる。
    # その場合だけしきい値を半分にして、この駅が上回る軸を探す。
    def relax(target, other, target_name_wins):
        found = []
        for axis, label, gap in AXES:
            va, vb = sc.get(a, {}).get(axis), sc.get(b, {}).get(axis)
            if va is None or vb is None:
                continue
            diff = (va - vb) if target_name_wins else (vb - va)
            if gap / 2 <= diff < gap:
                found.append(p[label])
        return found[:1]

    if not wins_a and wins_b:
        wins_a = relax(wins_a, wins_b, True)
    elif not wins_b and wins_a:
        wins_b = relax(wins_b, wins_a, False)

    ra, rb = band(a), band(b)
    rent = None
    if ra is not None and rb is not None and abs(ra - rb) >= 10000:
        rent = p["cmpRentCheaper"].format(station=name_b if rb < ra else name_a)
        cheaper_is_b = rb < ra

    sep = p["cmpSep"]
    def clause(wins, name):
        return p["cmpAxisWin"].format(axes=sep.join(wins[:2]), station=name)

    if rent:
        # 家賃で負けている側が、ほかの軸で上回るなら「ただし」でつなぐ
        other = wins_a if cheaper_is_b else wins_b
        other_name = name_a if cheaper_is_b else name_b
        if other:
            return p["cmpButJoin"].format(a=rent, b=clause(other, other_name))
        same = wins_b if cheaper_is_b else wins_a
        same_name = name_b if cheaper_is_b else name_a
        if same:
            return p["cmpAndJoin"].format(a=rent, b=clause(same, same_name))
        return p["cmpOnly"].format(a=rent)
    if wins_a and wins_b:
        return p["cmpButJoin"].format(a=clause(wins_b, name_b), b=clause(wins_a, name_a))
    if wins_a:
        return p["cmpOnly"].format(a=clause(wins_a, name_a))
    if wins_b:
        return p["cmpOnly"].format(a=clause(wins_b, name_b))
    return p["cmpOnly"].format(a=p["cmpNothing"])


def build(st, ctx):
    """1駅ぶんのコンテンツを組み立てる。データの無い層は入れない。"""
    p = ctx["p"]
    money, unit, sep = p["money"], p["moneyUnit"], p["listSep"]
    depth_label = p["depth"]
    slug = st["slug"]
    name = p["stationName"](st)
    line_objs = [ctx["lines"][i] for i in st["lineIds"] if i in ctx["lines"]]
    lines = [line_name(p["lineName"](l)) for l in line_objs]
    companies = [l["company"] for l in line_objs]
    com = {e["to"]: e["minutes"] for e in ctx["com"].get(slug, [])}
    ter = ctx["ter"].get(slug, {})
    road = ctx["roads"].get(slug, {})
    haz = ctx["haz"].get(slug, {}).get("flood", {})
    tide = ctx["haz"].get(slug, {}).get("hightide", {})
    band = ctx["bands"].get(slug)
    by_cat = {}
    for poi in ctx["pois"].get(slug, []):
        by_cat.setdefault(poi["category"], []).append(poi)

    c = {"slug": slug, "locale": ctx["locale"], "name": name}

    # ── 見出しと要約 ───────────────────────────────
    fastest = sorted(com.items(), key=lambda kv: kv[1])[:2]
    reach = join(p, (p["reachItem"].format(hub=p["hubs"][h], minutes=m,
                                           minuteWord=word(p, "minute", m))
                     for h, m in fastest))
    rent_txt = ""
    if band and "oneRoom" in band["bands"]:
        b = band["bands"]["oneRoom"]
        rent_txt = p["taglineRent"].format(low=money(b["low"]), high=money(b["high"]), unit=unit)
    c["tagline"] = p["tagline"].format(
        reach=reach, lineCount=len(lines), lineWord=word(p, "line", len(lines)),
        rent=rent_txt).strip()

    where = p["summaryWhere"].format(ward=p["ward"](st), lines=join(p, lines))
    if len(where) > 60:
        # 路線名を全部並べると1文が長くなりすぎる。概要では運営会社と本数だけ出し、
        # 路線名は「駅の使い勝手」に回す。
        firms = sorted(set(companies), key=companies.index)
        where = p["summaryWhereMany"].format(
            ward=p["ward"](st), operators=join(p, (p["company"][co] for co in firms)),
            count=len(lines), lineWord=word(p, "line", len(lines)))
    parts = [where]
    hub_order = ["otemachi", "shinjuku", "shibuya", "shinagawa"]
    parts.append(p["summaryCommute"].format(items=join(p, (
        p["commuteItem"].format(hub=p["hubs"][h], minutes=com[h],
                                minuteWord=word(p, "minute", com[h]))
        for h in hub_order if h in com))))
    if rent_txt:
        parts.append(rent_txt + p["sentenceGap"])
    if ter.get("slope"):
        parts.append(p["summaryTerrain"].format(
            elevation=ter["stationElevationM"], spread=ter["spreadM"],
            slope=p["slope"][ter["slope"]]))
    c["summary"] = "".join(parts).strip()

    # ── 坂（国土地理院） ───────────────────────────
    if ter.get("slope"):
        c["terrain"] = {
            "slope": ter["slope"],
            "note": p["terrainNote"].format(
                where=p["terrainLow"] if ter.get("stationIsLow") else p["terrainHigh"],
                elevation=ter["stationElevationM"], min=ter["minM"],
                max=ter["maxM"], spread=ter["spreadM"]),
        }

    # ── 浸水想定（重ねるハザードマップ） ─────────────
    if haz:
        if haz.get("atStation"):
            head = p["floodAtStation"].format(depth=depth_label[haz["atStation"]])
        elif haz.get("aroundCount"):
            head = p["floodNearOnly"]
        else:
            head = p["floodNone"]
        detail = (p["floodAround"].format(count=haz["aroundCount"],
                                          deepest=depth_label[haz["deepest"]])
                  if haz.get("aroundCount") else "")
        tide_txt = (p["hightide"].format(count=tide["aroundCount"])
                    if tide.get("aroundCount") else "")
        c["hazards"] = (head + detail + tide_txt + p["hazardTrailer"]).strip()

    # ── 買い物（OpenStreetMap） ────────────────────
    sup = by_cat.get("supermarket", [])
    if sup:
        picked, chains = [], set()
        for s in sup:
            key = s["name"][:4]
            if key in chains:
                continue
            chains.add(key)
            picked.append(s)
            if len(picked) >= 4:
                break
        c["groceries"] = [{
            "name": s["name"], "tier": tier_of(s["name"]), "walkMinutes": s["walkMinutes"],
            "sourceUrl": f"https://www.openstreetmap.org/{s['osmType']}/{s['osmId']}",
            "verifiedAt": ctx["poiDate"],
        } for s in picked]

    # ── 医療（OpenStreetMap） ──────────────────────
    cl, ph, hp = by_cat.get("clinic", []), by_cat.get("pharmacy", []), by_cat.get("hospital", [])
    if cl or ph or hp:
        if cl or ph:
            counts = [x for x in (
                p["medicalClinics"].format(
                    count=len(cl), clinicWord=word(p, "clinic", len(cl))) if cl else "",
                p["medicalPharmacies"].format(
                    count=len(ph), pharmacyWord=word(p, "pharmacy", len(ph))) if ph else "") if x]
            bits = [p["medicalCounts"].format(items=join(p, counts))]
        else:
            bits = [p["medicalNone"]]
        if hp:
            near = sorted(hp, key=lambda x: x["distanceM"])[:2]
            bits.append(p["medicalHospitalNearest"].format(
                name=near[0]["name"], distance=near[0]["distanceM"]))
            if len(near) > 1:
                bits.append(p["medicalHospitalSecond"].format(
                    name=near[1]["name"], distance=near[1]["distanceM"]))
        else:
            bits.append(p["medicalNoHospital"])
        bits.append(p["medicalTrailer"])
        c["medical"] = "".join(bits).strip()

    # ── 駅の使い勝手 ───────────────────────────────
    groups = chunk(lines)
    if len(groups) == 1:
        note = [p["stationLines"].format(lines=join(p, lines), count=len(lines),
                                         lineWord=word(p, "line", len(lines)))]
    else:
        note = [p["stationLinesCount"].format(count=len(lines),
                                              lineWord=word(p, "line", len(lines))),
                p["stationLinesHead"].format(lines=join(p, groups[0]))]
        more = ["stationLinesMore", "stationLinesMore2", "stationLinesMore3"]
        for i, g in enumerate(groups[1:]):
            note.append(p[more[min(i, len(more) - 1)]].format(lines=join(p, g)))
    # 乗換の余地は「路線がいくつあるか」ではなく「運営会社が分かれているか」で決まる。
    # 京王と小田急はどちらも私鉄だが別の会社なので、片方が止まっても他方は動く。
    unique = sorted(set(companies), key=companies.index)
    if len(lines) == 1:
        note.append(p["stationSingleLine"])
    elif len(unique) > 1:
        breakdown = join(p, (
            p["stationOperatorItem"].format(
                operator=p["company"][co], count=companies.count(co),
                lineWord=word(p, "line", companies.count(co)))
            for co in unique))
        note.append(p["stationMixedOperators"].format(breakdown=breakdown))
    else:
        key = "stationSameOperatorTwo" if len(lines) == 2 else "stationSameOperator"
        note.append(p[key].format(
            count=len(lines), lineWord=word(p, "line", len(lines)),
            operator=p["company"][unique[0]]))
    sc = ctx["sc"].get(slug, {})
    if "transitConvenience" in sc:
        note.append(p["stationTransitScore"].format(score=sc["transitConvenience"]))
    c["stationNote"] = "".join(note).strip()

    # ── 家賃（当社調べ） ───────────────────────────
    if band:
        b = band["bands"]
        rows = [(k, l) for k, l in p["rentLabels"].items() if k in b]
        c["rentRange"] = {
            "note": p["rentNote"].format(items=join(p, (
                p["rentItem"].format(label=l, low=money(b[k]["low"]),
                                     high=money(b[k]["high"]), unit=unit)
                for k, l in rows))),
            "drivers": list(p["rentDrivers"]),
        }
        reason = []
        if "oneRoom" in b:
            reason.append(p["rentReason"].format(
                low=money(b["oneRoom"]["low"]), high=money(b["oneRoom"]["high"]), unit=unit))
        wide = [l for k, l in rows if b[k]["wideSpread"]]
        if wide:
            reason.append(p["rentWideSpread"].format(layouts=p["rentWideSep"].join(wide)))
        if reason:
            c["rentReason"] = "".join(reason).strip()

    # ── 近くの駅との違い ───────────────────────────
    near = sorted(((haversine_m(st, o), o) for o in ctx["roster"] if o["slug"] != slug),
                  key=lambda t: t[0])[:2]
    nb = []
    for dist, o in near:
        oc = {e["to"]: e["minutes"] for e in ctx["com"].get(o["slug"], [])}
        ob = ctx["bands"].get(o["slug"])
        bits = [p["neighbourDistance"].format(meters=int(dist))]
        if "otemachi" in com and "otemachi" in oc:
            d = oc["otemachi"] - com["otemachi"]
            if abs(d) <= 2:
                bits.append(p["neighbourSame"].format(station=name))
            else:
                key = "neighbourSlower" if d > 0 else "neighbourFaster"
                bits.append(p[key].format(station=name, minutes=abs(d),
                                          minuteWord=word(p, "minute", abs(d))))
        if band and ob and "oneRoom" in band["bands"] and "oneRoom" in ob["bands"]:
            dm = ob["bands"]["oneRoom"]["mean"] - band["bands"]["oneRoom"]["mean"]
            if abs(dm) >= 5000:
                # 平均どうしの差をそのまま出すと「7,233円ほど高い」のように、
                # 元の帯（1万円刻み）より細かい数字になり、精度を偽ることになる。
                rounded = int(round(abs(dm) / 1000)) * 1000
                key = "neighbourRentHigher" if dm > 0 else "neighbourRentLower"
                bits.append(p[key].format(amount=money(rounded), unit=unit))
        lead = compare_lead(p, slug, o["slug"], ctx)
        entry = {"slug": o["slug"]}
        if lead:
            entry["lead"] = lead
        entry["note"] = "".join(bits).strip()
        nb.append(entry)
    if nb:
        c["neighbours"] = nb

    # ── 向いている人・向かない人 ───────────────────
    good, bad = [], []
    if com.get("otemachi", 99) <= 20:
        good.append(p["goodOtemachi"])
    if com.get("shinjuku", 99) <= 20:
        good.append(p["goodShinjuku"])
    if len(lines) >= 3:
        good.append(p["goodManyLines"])
    if ter.get("slope") == "flat":
        good.append(p["goodFlat"])
    if sc.get("shopping", 0) >= 70:
        good.append(p["goodShopping"])
    if sc.get("nature", 0) >= 70:
        good.append(p["goodNature"])
    if not haz.get("aroundCount"):
        good.append(p["goodDry"])
    if band and "oneRoom" in band["bands"] and band["bands"]["oneRoom"]["low"] <= 90000:
        good.append(p["goodCheap"])

    if haz.get("atStation"):
        bad.append(p["badFlood"])
    if ter.get("slope") == "hilly":
        bad.append(p["badHilly"])
    if len(lines) == 1:
        bad.append(p["badOneLine"])
    if sc.get("shopping", 100) <= 30:
        bad.append(p["badShopping"])
    if sc.get("food", 100) <= 30:
        bad.append(p["badFood"])
    if band and "oneRoom" in band["bands"] and band["bands"]["oneRoom"]["low"] >= 150000:
        bad.append(p["badExpensive"])
    c["goodFor"] = good[:5] or [p["goodUnknown"]]
    c["notFor"] = bad[:5] or [p["badUnknown"]]

    # ── 音が気になりうる場所 ───────────────────────
    # 静けさは、人の音と車の音を分けて確かめる（ルール41）。
    # 繁華街から離れていても、幹線道路に面していれば車の音は一日中続く。
    def road_side(v):
        """車線数を「片側n車線」に直す。分離帯のある大通りは片方ずつ登録されている。"""
        lanes = v.get("lanes")
        if not lanes:
            return p["roadSideUnknown"]
        key = "roadSideOneway" if v.get("oneway") else "roadSideBoth"
        n = lanes if v.get("oneway") else max(1, round(lanes / 2))
        return p[key].format(n=n)

    def road_line(cls, v):
        """道路名だけでは、どれくらいうるさいのかが読み手に伝わらない。
        高速道路か一般道か、片側何車線か、駅から何m先かを添える（ルール42）。"""
        side = road_side(v)
        if cls == "motorway":
            key = "noiseRoadMotorway"
        elif v["m"] > 200:
            key = "noiseRoadFar"
        else:
            wide = (v.get("lanes") or 0) >= (3 if v.get("oneway") else 6)
            key = ("noiseRoadVeryNear" if wide and v["m"] <= 40
                   else "noiseRoadBig" if wide else "noiseRoadMid")
        return p[key].format(name=v["name"], m=v["m"], side=side)

    # 音の出どころは2本まで書く。高速道路は音の質が違うので、
    # 一般道より近くなくても先に出す。
    ordered = sorted(
        ((cls, v) for cls in ("motorway", "trunk", "primary", "secondary")
         if (v := road.get(cls)) and v.get("name")),
        key=lambda t: (t[0] != "motorway" or t[1]["m"] > 400, t[1]["m"]))
    near_road = ordered[0] if ordered else None
    lines = []
    for cls, v in ordered:
        if v["m"] <= 250 or (cls == "motorway" and v["m"] <= 400) or not lines:
            lines.append(road_line(cls, v))
        if len(lines) == 2:
            break
    if lines:
        c["noiseSources"] = lines

    # ── 街の性格タグと、節ごとの一言 ───────────────
    tags = station_tags(sc, st, ter, ctx)
    if tags:
        c["tags"] = tags

    leads = {}
    slope = ter.get("slope")
    if slope in ("flat", "some", "hilly"):
        leads["terrain"] = p["leadTerrain" + slope.capitalize()]
    shops = by_cat.get("supermarket", [])
    if shops:
        nearest = min(x["walkMinutes"] for x in shops)
        key = "leadGroceriesMany" if len(shops) >= 3 else "leadGroceriesFew"
        leads["groceries"] = p[key].format(count=len(shops), minutes=nearest)
    else:
        leads["groceries"] = p["leadGroceriesNone"]
    if "disaster" in sc:
        leads["hazards"] = p[band_key("leadHazard", sc["disaster"])]
    if len(lines) == 1:
        leads["stationNote"] = p["leadStationOne"].format(line=lines[0])
    elif "transitConvenience" in sc:
        key = "leadStationMany" if five(sc["transitConvenience"]) >= 3.5 else "leadStationMid"
        leads["stationNote"] = p[key].format(count=len(lines))
    if "rentValue" in sc:
        leads["rentRange"] = p[band_key("leadRent", sc["rentValue"])]
    if "healthcare" in sc:
        leads["medical"] = p[band_key("leadMedical", sc["healthcare"])]
    if near_road and near_road[1].get("name"):
        cls, v = near_road
        key = ("leadNoiseLoud" if (cls == "motorway" and v["m"] <= 200) or v["m"] <= 60
               else "leadNoiseMid" if v["m"] <= 250 else "leadNoiseQuiet")
        leads["noiseSources"] = p[key].format(name=v["name"], m=v["m"])
    if leads:
        c["leads"] = leads

    c["authoredBy"] = "data-generated"
    return c


def check_phrases(locale):
    """文型の埋め忘れを、駅を組み立てる前に見つける。"""
    base = set(PHRASES["ja"])
    missing = sorted(base - set(PHRASES[locale]))
    if missing:
        raise SystemExit(f"{locale} の文型が足りません: {'、'.join(missing)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--locale", default="ja", choices=sorted(PHRASES))
    ap.add_argument("--limit", type=int, default=0, help="先頭から何駅だけ試すか")
    args = ap.parse_args()
    check_phrases(args.locale)

    out_dir = os.path.join(D, "content", args.locale)
    os.makedirs(out_dir, exist_ok=True)

    roster = load("roster/stations.json")
    pois_doc = load("computed/pois.json")
    buildings = load("computed/buildings.json")["stations"]
    ctx = {
        "locale": args.locale,
        "p": PHRASES[args.locale],
        "roster": roster,
        "lines": {l["id"]: l for l in load("reference/lines.json")},
        "com": load("computed/commutes.json"),
        "sc": load("computed/scores.json"),
        "ter": load("computed/terrain.json")["stations"],
        "roads": load("computed/roads.json")["stations"],
        "rosterBySlug": {r["slug"]: r for r in roster},
        # 駅を出てすぐの繁華性。半径300mの飲食店・酒場・カフェの数
        "bustle": {
            r["slug"]: sum(1 for x in pois_doc["stations"].get(r["slug"], [])
                           if x["category"] in ("restaurant", "bar", "cafe")
                           and x["distanceM"] <= 300)
            for r in roster
        },
        # 駅から500m以内にある商業の建物の、階数の合計。
        # 雑居ビルのテナントが OpenStreetMap に入っていないため、
        # 路面の店の数だけでは、縦に積まれた街の厚みを測れない
        "floors": {r["slug"]: buildings.get(r["slug"], {}).get("floors", 0)
                   for r in roster},
        "haz": load("computed/hazard.json")["stations"],
        "bands": load("computed/rent-bands.json"),
        "pois": pois_doc["stations"],
        "poiDate": pois_doc["meta"]["retrievedAt"],
    }

    written = made = skipped = refreshed = 0
    targets = roster[:args.limit] if args.limit else roster
    for st in targets:
        path = os.path.join(out_dir, f"{st['slug']}.json")
        if os.path.exists(path):
            existing = json.load(open(path, encoding="utf-8"))
            # 人が書いた駅と、文章としてローカライズした駅は上書きしない
            if existing.get("authoredBy") in ("human", "draft", "ai-localized"):
                skipped += 1
                # ただし近くの駅・性格タグ・節ごとの一言は、スコアと距離だけで決まる層
                # なので、人が書いた駅でもここで作り直す。人が選んだ駅は alternatives に
                # 入っており、人が書いた一言は上書きしない。
                fresh = build(st, ctx)
                touched = False
                for field in ("neighbours", "tags"):
                    if fresh.get(field) and fresh[field] != existing.get(field):
                        existing[field] = fresh[field]
                        touched = True
                # 一言は、本文と食い違うと読み手を迷わせる。人が本文を書いた駅では、
                # 本文に合わせて一言も人が書くので、既にあるものは上書きしない。
                # 淡路町では、本文が「坂を上るのは御茶ノ水へ出るときだけ」と書いている
                # 横で、組み立てた一言が「どの区画に住むかで負担が変わる」と出ていた。
                # 迷いやすい駅の比較にも、一言を入れる。note は人が書いたものを残す。
                for field in ("neighbours", "alternatives"):
                    for item in existing.get(field) or []:
                        if "lead" in item:
                            continue
                        lead = compare_lead(ctx["p"], st["slug"], item["slug"], ctx)
                        if lead:
                            item["lead"] = lead
                            touched = True

                merged = dict(existing.get("leads") or {})
                for k, v in (fresh.get("leads") or {}).items():
                    if k not in merged:
                        merged[k] = v
                        touched = True
                if merged:
                    existing["leads"] = merged
                if touched and not args.dry_run:
                    json.dump(existing, open(path, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=2)
                    open(path, "a", encoding="utf-8").write("\n")
                    refreshed += 1
                continue
        c = build(st, ctx)
        made += 1
        if not args.dry_run:
            json.dump(c, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            open(path, "a", encoding="utf-8").write("\n")
            written += 1

    print(f"組み立てた駅: {made} / 人が書いた駅・訳した駅は残した: {skipped}"
          f"（うちデータで決まる層だけ作り直した: {refreshed}）")
    if args.dry_run:
        print("（--dry-run のため書き込んでいない）")
    else:
        print(f"書き出した: {written}件 → data/content/{args.locale}/")


if __name__ == "__main__":
    main()
