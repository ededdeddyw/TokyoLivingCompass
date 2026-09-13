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

すでに人が書いた駅（authoredBy が draft か human）は上書きしない。

言語ごとに違うのは文型だけで、組み立ての手順は変わらない。
文型は scripts/station_phrases.py にまとめてある。
"""
import argparse
import json
import math
import os
import re
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


def word(p, key, n):
    """数に応じた語形を返す。英語だけ単数と複数で変わる。"""
    forms = p["words"][key]
    return forms[0] if n == 1 else forms[1]


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

    parts = [p["summaryWhere"].format(ward=p["ward"](st), lines=join(p, lines))]
    hub_order = ["otemachi", "shinjuku", "shibuya", "shinagawa"]
    parts.append(p["summaryCommute"].format(items=join(p, (
        p["commuteItem"].format(hub=p["hubs"][h], minutes=com[h],
                                minuteWord=word(p, "minute", com[h]))
        for h in hub_order if h in com))))
    if rent_txt:
        parts.append(rent_txt)
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
            bits.append(p["medicalHospitals"].format(items=join(p, (
                p["medicalHospitalItem"].format(name=h["name"], distance=h["distanceM"])
                for h in near))))
        else:
            bits.append(p["medicalNoHospital"])
        bits.append(p["medicalTrailer"])
        c["medical"] = "".join(bits).strip()

    # ── 駅の使い勝手 ───────────────────────────────
    note = [p["stationLines"].format(lines=join(p, lines), count=len(lines),
                                     lineWord=word(p, "line", len(lines)))]
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
        note.append(p["stationSameOperator"].format(
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

    # ── 隣の駅との使い分け ─────────────────────────
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
                key = "neighbourRentHigher" if dm > 0 else "neighbourRentLower"
                bits.append(p[key].format(amount=money(abs(dm)), unit=unit))
        nb.append({"slug": o["slug"], "note": "".join(bits).strip()})
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
    ctx = {
        "locale": args.locale,
        "p": PHRASES[args.locale],
        "roster": roster,
        "lines": {l["id"]: l for l in load("reference/lines.json")},
        "com": load("computed/commutes.json"),
        "sc": load("computed/scores.json"),
        "ter": load("computed/terrain.json")["stations"],
        "haz": load("computed/hazard.json")["stations"],
        "bands": load("computed/rent-bands.json"),
        "pois": pois_doc["stations"],
        "poiDate": pois_doc["meta"]["retrievedAt"],
    }

    written = made = skipped = 0
    targets = roster[:args.limit] if args.limit else roster
    for st in targets:
        path = os.path.join(out_dir, f"{st['slug']}.json")
        if os.path.exists(path):
            existing = json.load(open(path, encoding="utf-8"))
            # 人が書いた駅は上書きしない
            if existing.get("authoredBy") in ("human", "draft"):
                skipped += 1
                continue
        c = build(st, ctx)
        made += 1
        if not args.dry_run:
            json.dump(c, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            open(path, "a", encoding="utf-8").write("\n")
            written += 1

    print(f"組み立てた駅: {made} / 人が書いた駅は残した: {skipped}")
    if args.dry_run:
        print("（--dry-run のため書き込んでいない）")
    else:
        print(f"書き出した: {written}件 → data/content/{args.locale}/")


if __name__ == "__main__":
    main()
