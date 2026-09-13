#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出典のあるデータだけを使って、全448駅ぶんの日本語コンテンツを組み立てる。

  python3 scripts/build-station-content.py --dry-run
  python3 scripts/build-station-content.py

**書き手の記憶による記述は1文字も入れない。**入るのは次のデータから導ける記述だけ。

  所要時間  data/computed/commutes.json  （駅間距離と路線種別からの計算）
  スコア    data/computed/scores.json
  標高      data/computed/terrain.json   （国土地理院）
  浸水想定  data/computed/hazard.json    （重ねるハザードマップ）
  周辺施設  data/computed/pois.json      （OpenStreetMap・ODbL）
  家賃      data/computed/rent-bands.json（LIFULL HOME'S と Yahoo!不動産の平均）

したがって、街のようす（faces）・夜の帰り道（nightWalk）・住民層（residents）・
物件の傾向（housingStock）・これからどう変わるか（outlook）は書かない。
これらはデータが無く、書けば記憶で書くことになる（CLAUDE.md ルール35）。
16層のうち埋まるのは、データのある層だけである。

すでに人が書いた駅（authoredBy が draft か human）は上書きしない。
"""
import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
OUT = os.path.join(D, "content", "ja")

HUB_JA = {"otemachi": "大手町", "shinjuku": "新宿", "shibuya": "渋谷", "tokyo": "東京",
          "shinagawa": "品川", "toranomon": "虎ノ門", "roppongi": "六本木"}
SLOPE_JA = {"flat": "ほぼ平坦である", "some": "ゆるやかな坂がある", "hilly": "起伏が大きい"}
OPERATOR_JA = {"jr": "JR", "tokyo-metro": "東京メトロ", "toei": "都営", "private": "私鉄"}

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


def man(yen):
    """円を「12万」の形にする。1万円未満は切り捨てず小数第1位まで見せる。"""
    v = yen / 10000
    return f"{v:.0f}万" if abs(v - round(v)) < 0.05 else f"{v:.1f}万"


def haversine_m(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = math.radians(b["lat"] - a["lat"])
    dl = math.radians(b["lon"] - a["lon"])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def build(st, ctx):
    """1駅ぶんのコンテンツを組み立てる。データの無い層は入れない。"""
    slug, name = st["slug"], st["nameJa"]
    lines = [ctx["lines"][i]["nameJa"] for i in st["lineIds"] if i in ctx["lines"]]
    ops = {ctx["lines"][i]["operator"] for i in st["lineIds"] if i in ctx["lines"]}
    com = {e["to"]: e["minutes"] for e in ctx["com"].get(slug, [])}
    ter = ctx["ter"].get(slug, {})
    haz = ctx["haz"].get(slug, {}).get("flood", {})
    tide = ctx["haz"].get(slug, {}).get("hightide", {})
    band = ctx["bands"].get(slug)
    pois = ctx["pois"].get(slug, [])
    by_cat = {}
    for p in pois:
        by_cat.setdefault(p["category"], []).append(p)

    c = {"slug": slug, "locale": "ja", "name": name}

    # ── 見出しと要約 ───────────────────────────────
    fastest = sorted(com.items(), key=lambda kv: kv[1])[:2]
    reach = "、".join(f"{HUB_JA[h]}へ{m}分" for h, m in fastest)
    rent_txt = ""
    if band and "oneRoom" in band["bands"]:
        b = band["bands"]["oneRoom"]
        rent_txt = f"ワンルームの家賃はおよそ{man(b['low'])}〜{man(b['high'])}円である。"
    c["tagline"] = f"{reach}で着く。{len(lines)}路線が乗り入れる。{rent_txt}"

    parts = [f"{st['wardNameJa']}にあり、{'、'.join(lines)}が乗り入れる。"]
    parts.append("主なオフィス街までの所要時間は、"
                 + "、".join(f"{HUB_JA[h]}へ{com[h]}分" for h in
                             ["otemachi", "shinjuku", "shibuya", "shinagawa"] if h in com)
                 + "である。")
    if rent_txt:
        parts.append(rent_txt)
    if ter.get("slope"):
        parts.append(f"駅の標高は{ter['stationElevationM']}mで、周囲800mの標高差は"
                     f"{ter['spreadM']}mある。駅の周りの土地は{SLOPE_JA[ter['slope']]}。")
    c["summary"] = "".join(parts)

    # ── 坂（国土地理院） ───────────────────────────
    if ter.get("slope"):
        low = ter.get("stationIsLow")
        where = "駅は周囲より低い場所にあり" if low else "駅は周囲の中では高いほうにあり"
        c["terrain"] = {
            "slope": ter["slope"],
            "note": f"{where}、標高は{ter['stationElevationM']}mである。"
                    f"周囲800mの標高は{ter['minM']}mから{ter['maxM']}mまで分かれ、"
                    f"その差は{ter['spreadM']}mある。"
                    f"国土地理院の標高APIから、駅と半径400mの8方位、計9点を読み取った値である。",
        }

    # ── 浸水想定（重ねるハザードマップ） ─────────────
    if haz:
        if haz.get("atStation"):
            head = (f"洪水浸水想定区域（想定最大規模）では、駅の地点が区域に入り、"
                    f"想定される深さは{haz['atStation']}である。")
        elif haz.get("aroundCount"):
            head = (f"洪水浸水想定区域（想定最大規模）では、駅の地点は区域の外にある。")
        else:
            head = ("洪水浸水想定区域（想定最大規模）では、駅の地点も、"
                    "駅から400m以内の9地点も、いずれも区域の外にある。")
        detail = ""
        if haz.get("aroundCount"):
            detail = (f"駅から400m以内で見た9地点のうち{haz['aroundCount']}地点が区域に含まれ、"
                      f"その中で最も深い想定は{haz['deepest']}である。")
        tide_txt = ""
        if tide.get("aroundCount"):
            tide_txt = (f"高潮についても9地点のうち{tide['aroundCount']}地点が想定区域に入る。")
        c["hazards"] = (head + detail + tide_txt
                        + "想定される深さは同じ駅でも区画ごとに違うので、"
                          "住所ごとに区のハザードマップで確認したい。"
                          "内水氾濫は全国共通の地図が公開されておらず区が個別に出しているため、"
                          "あわせて見ておきたい。")

    # ── 買い物（OpenStreetMap） ────────────────────
    sup = by_cat.get("supermarket", [])
    if sup:
        picked, chains = [], set()
        for p in sup:
            key = p["name"][:4]
            if key in chains:
                continue
            chains.add(key)
            picked.append(p)
            if len(picked) >= 4:
                break
        c["groceries"] = [{
            "name": p["name"], "tier": tier_of(p["name"]), "walkMinutes": p["walkMinutes"],
            "sourceUrl": f"https://www.openstreetmap.org/{p['osmType']}/{p['osmId']}",
            "verifiedAt": ctx["poiDate"],
        } for p in picked]

    # ── 医療（OpenStreetMap） ──────────────────────
    cl, ph, hp = by_cat.get("clinic", []), by_cat.get("pharmacy", []), by_cat.get("hospital", [])
    if cl or ph or hp:
        if cl or ph:
            near_txt = "、".join(
                x for x in (f"クリニックが{len(cl)}件" if cl else "",
                            f"薬局が{len(ph)}件" if ph else "") if x)
            bits = [f"駅から歩いて800m以内に、{near_txt}ある。"]
        else:
            bits = ["駅から歩いて800m以内には、OpenStreetMap に登録されている"
                    "クリニックも薬局も見当たらない。"]
        if hp:
            near = sorted(hp, key=lambda x: x["distanceM"])[:2]
            bits.append("病院として登録されている施設は、"
                        + "、".join(f"{h['name']}が{h['distanceM']}mほど" for h in near)
                        + "の距離にある。")
        else:
            bits.append("駅から2.5km以内には、病院として登録されている施設が見当たらない。")
        bits.append("入院できるかどうか、何科があるかまでは OpenStreetMap には"
                    "書かれていないので、各施設のウェブサイトで確かめてほしい。"
                    "夜間や休日にかかれる医療機関は、住む区の救急相談窓口で確認できる。")
        c["medical"] = "".join(bits)

    # ── 駅の使い勝手 ───────────────────────────────
    note = [f"{'、'.join(lines)}の{len(lines)}路線が使える。"]
    if len(lines) == 1:
        note.append("乗り入れは1路線だけなので、その路線が止まったときは、"
                    "ほかの路線が通る駅まで歩くことになる。")
    elif len(ops) > 1:
        breakdown = "、".join(
            f"{OPERATOR_JA[o]}が{sum(1 for i in st['lineIds'] if i in ctx['lines'] and ctx['lines'][i]['operator'] == o)}路線"
            for o in sorted(ops, key=lambda o: list(OPERATOR_JA).index(o)))
        note.append(f"運営は{breakdown}に分かれているので、"
                    "1つの路線が止まっても、別の運営会社の路線に乗り換えられる。")
    else:
        note.append(f"{len(lines)}路線とも{OPERATOR_JA[list(ops)[0]]}の路線なので、"
                    "運営会社全体に及ぶ障害のときは、まとめて止まることがある。")
    sc = ctx["sc"].get(slug, {})
    if "transitConvenience" in sc:
        note.append(f"路線数と事業者の広がりから計算した乗換の利便性は、100点満点で{sc['transitConvenience']}点である。")
    c["stationNote"] = "".join(note)

    # ── 家賃（当社調べ） ───────────────────────────
    if band:
        b = band["bands"]
        rows = [(k, l) for k, l in [("oneRoom", "ワンルーム"), ("oneK", "1K"),
                                    ("oneLDK", "1LDK"), ("twoLDK", "2LDK")] if k in b]
        c["rentRange"] = {
            "note": "、".join(f"{l}が{man(b[k]['low'])}〜{man(b[k]['high'])}円" for k, l in rows)
                    + "である。LIFULL HOME'S と Yahoo!不動産が公開する駅別の相場を平均し、"
                      "1万円刻みに丸めた（当社調べ）。いずれも募集賃料のため、"
                      "実際の成約額はこれより下がることがある。"
                      "同じ駅でも築年数・駅からの距離・通り沿いかどうかで大きく変わる。",
            "drivers": ["築年数と構造", "駅からの距離", "幹線道路や線路に面しているか",
                        "坂の上か下か", "間取りに対する専有面積"],
        }
        wide = [l for k, l in rows if b[k]["wideSpread"]]
        reason = [f"ワンルームの相場は{man(b['oneRoom']['low'])}〜{man(b['oneRoom']['high'])}円である。"
                  if "oneRoom" in b else ""]
        if wide:
            reason.append(f"ただし{('・'.join(wide))}は2社の値が3万円以上ひらいており、"
                          "集計の対象が違うぶん幅を持って見たほうがよい。")
        c["rentReason"] = "".join(x for x in reason if x)

    # ── 隣の駅との使い分け ─────────────────────────
    near = sorted(
        ((haversine_m(st, o), o) for o in ctx["roster"] if o["slug"] != slug),
        key=lambda t: t[0])[:2]
    nb = []
    for dist, o in near:
        oc = {e["to"]: e["minutes"] for e in ctx["com"].get(o["slug"], [])}
        ob = ctx["bands"].get(o["slug"])
        bits = [f"直線で{int(dist)}mの距離にある。"]
        if "otemachi" in com and "otemachi" in oc:
            d = oc["otemachi"] - com["otemachi"]
            bits.append(f"大手町へは{name}と同じくらいの時間で着く。" if abs(d) <= 2
                        else (f"大手町へは{name}より{abs(d)}分"
                              f"{'多くかかる' if d > 0 else '早く着く'}。"))
        if band and ob and "oneRoom" in band["bands"] and "oneRoom" in ob["bands"]:
            dm = ob["bands"]["oneRoom"]["mean"] - band["bands"]["oneRoom"]["mean"]
            if abs(dm) >= 5000:
                bits.append(f"ワンルームの相場は{man(abs(dm))}円ほど"
                            f"{'高い' if dm > 0 else '安い'}。")
        nb.append({"slug": o["slug"], "note": "".join(bits)})
    if nb:
        c["neighbours"] = nb

    # ── 向いている人・向かない人 ───────────────────
    good, bad = [], []
    if com.get("otemachi", 99) <= 20:
        good.append("大手町・丸の内方面へ通勤する人")
    if com.get("shinjuku", 99) <= 20:
        good.append("新宿方面へ通勤する人")
    if len(lines) >= 3:
        good.append("路線が止まったときに別の経路を使いたい人")
    if ter.get("slope") == "flat":
        good.append("自転車やベビーカーで動くことが多い人")
    if sc.get("shopping", 0) >= 70:
        good.append("徒歩圏で買い物を済ませたい人")
    if sc.get("nature", 0) >= 70:
        good.append("公園が近いことを重視する人")
    if not haz.get("aroundCount"):
        good.append("洪水の浸水想定区域を避けたい人")
    if band and "oneRoom" in band["bands"] and band["bands"]["oneRoom"]["low"] <= 90000:
        good.append("家賃を抑えたい単身者")

    if haz.get("atStation"):
        bad.append("洪水の浸水想定区域を避けたい人")
    if ter.get("slope") == "hilly":
        bad.append("坂の上り下りを避けたい人")
    if len(lines) == 1:
        bad.append("運転見合わせのときに別の経路が欲しい人")
    if sc.get("shopping", 100) <= 30:
        bad.append("徒歩圏で買い物を済ませたい人")
    if sc.get("food", 100) <= 30:
        bad.append("外食できる店の多さを求める人")
    if band and "oneRoom" in band["bands"] and band["bands"]["oneRoom"]["low"] >= 150000:
        bad.append("家賃を抑えたい人")
    if not bad:
        bad.append("この駅ならではの弱点は、データからは読み取れていない")
    c["goodFor"] = good[:5] or ["データからは、際立った向き先を読み取れていない"]
    c["notFor"] = bad[:5]

    c["authoredBy"] = "data-generated"
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="先頭から何駅だけ試すか")
    args = ap.parse_args()

    roster = load("roster/stations.json")
    pois_doc = load("computed/pois.json")
    ctx = {
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
        path = os.path.join(OUT, f"{st['slug']}.json")
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
        print(f"書き出した: {written}件 → data/content/ja/")


if __name__ == "__main__":
    main()
