#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
住む人の層ごとの「1日の過ごし方」の下書きを、全駅ぶん作る。

  python3 scripts/build-persona-days.py            # 人がまだ読んでいない駅だけ作り直す
  python3 scripts/build-persona-days.py osaki ...  # 指定した駅だけ

出力: data/content/ja/{slug}.json の personaDays（personaDaysStatus は "generated"）

なぜ要るのか。
  1日の過ごし方は、458駅 × 4層 × 3場面で、人の手では書けない量になる。
  そこで、すでに持っているデータ（所要時間・確認済みの食料品店・地図データ上の店と公園・
  電車で行きやすい行き先・地形・騒音）から組み立てる。画面では「データから自動で組み立てた想定」と添えて出す。
  人が読み直した駅は personaDaysStatus を "reviewed" にする（docs/18-persona-days.md §6.7）。

決まり。
  - 店・施設・数字は、データにあるものだけを使う。データが無い場面は書かない。
  - 地図データ（OpenStreetMap）にしかない店には「地図データ上の」と添える。
  - 日本語表現ルール（CLAUDE.md）に沿う。1文60字以内、ですます調、比喩を使わない。
  - 人が書いた・読み直した駅（personaDaysStatus が "reviewed" のもの）は上書きしない。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "data", "content", "ja")

HUB_NAMES = {"shinjuku": "新宿", "shibuya": "渋谷", "tokyo": "東京", "shinagawa": "品川",
             "otemachi": "大手町", "toranomon": "虎ノ門", "roppongi": "六本木"}
SLOPE_WEEKDAY = {
    "flat": "駅のまわりは平坦で、自転車でも歩きでも移動が楽です。",
    "some": "駅のまわりには坂があり、住む場所によっては上り下りがあります。",
    "hilly": "駅のまわりは坂が多く、住む場所によっては毎日の上り下りが続きます。",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def line_name(name):
    """「JR東海道本線(東京～熱海)」のような括弧書きを外す。"""
    return re.sub(r"[（(].*?[)）]", "", name).strip()


def first_sentence(text):
    m = re.match(r"(.+?。)", text or "")
    return m.group(1) if m else None


class Station:
    def __init__(self, slug, ctx):
        self.slug = slug
        self.roster = ctx["roster"][slug]
        self.content = load(os.path.join(CONTENT, f"{slug}.json"))
        self.scores = ctx["scores"].get(slug, {})
        self.commutes = sorted(ctx["commutes"].get(slug, []), key=lambda c: c["minutes"])
        self.pois = ctx["pois"].get(slug, [])
        self.life = ctx["lifestyle"].get(slug)
        self.names = ctx["names"]
        self.ward = self.roster["wardNameJa"]
        self.hazard = ctx["hazard"].get(slug) or {}

    # --- 材料 ---

    def hubs(self, n=2):
        # 駅そのものがオフィス街にあたる駅（六本木・虎ノ門など）で、自分の駅を勤め先にしない
        # 東京駅から大手町（1分）のように歩いて行ける近さのオフィス街も、通勤の例にしない
        return [c for c in self.commutes
                if c["to"] in HUB_NAMES and c["to"] != self.slug and c["minutes"] >= 3][:n]

    def nearest(self, category, max_min=10):
        items = sorted((p for p in self.pois if p["category"] == category and p.get("name")),
                       key=lambda p: p["walkMinutes"])
        return [p for p in items if p["walkMinutes"] <= max_min]

    def grocery(self):
        """人が確かめた食料品店のうち、いちばん近いもの。"""
        shops = [g for g in self.content.get("groceries") or [] if g.get("walkMinutes")]
        return min(shops, key=lambda g: g["walkMinutes"]) if shops else None

    def grocery_hours(self, name):
        for p in self.pois:
            if p["category"] == "supermarket" and p.get("name") and p["name"] in name:
                return p.get("openingHours")
        return None

    def station_name(self, slug):
        return self.names.get(slug, slug)

    # --- 文 ---

    def commute_lines(self, who):
        hubs = self.hubs()
        if not hubs:
            return []
        h = hubs[0]
        t = "乗り換えはありません" if h["transfers"] == 0 else f"途中で{h['transfers']}回乗り換えます"
        lines = [f"{HUB_NAMES[h['to']]}までは{h['minutes']}分です。{t}。"]
        if who == "dinks" and len(hubs) > 1:
            h2 = hubs[1]
            t2 = "乗り換えはありません" if h2["transfers"] == 0 else f"途中で{h2['transfers']}回乗り換えます"
            lines = [f"1人は{HUB_NAMES[h['to']]}まで{h['minutes']}分です。"
                     f"もう1人は{HUB_NAMES[h2['to']]}まで{h2['minutes']}分で、{t2}。"]
        return lines

    def shopping_line(self, lead, verb):
        """「{lead}、歩いて2分ほどの〇〇（23時まで営業）で{verb}。」"""
        g = self.grocery()
        if not g:
            return None
        hours = self.grocery_hours(g["name"])
        close = None
        if hours:
            m = re.search(r"-(\d{1,2}):(\d{2})\s*$", hours)
            if m:
                minute = {"00": "", "30": "半"}.get(m.group(2), f"{int(m.group(2))}分")
                close = f"{int(m.group(1))}時{minute}"
        where = f"歩いて{g['walkMinutes']}分ほどの{g['name']}"
        if close:
            where += f"（{close}まで営業）"
        return f"{lead}、{where}で{verb}。"

    def evening_line(self):
        food = self.scores.get("food")
        night = self.scores.get("nightlife")
        if food is None:
            return None
        if food >= 85 and (night or 0) >= 80:
            return "駅のまわりには飲食店が多く、帰りが遅くなっても夕食をとる店を探せます。"
        if food < 30:
            return "駅のまわりで外食できる店は少ないので、夕食は家で作るか、乗り換える駅で済ませます。"
        return None

    def quiet_line(self):
        q = self.scores.get("quietness")
        noise = (self.content.get("noiseSources") or [None])[0]
        if q is not None and q >= 70:
            return "駅のまわりは人の声も車の音も少なく、家で静かに過ごせます。"
        if noise:
            return noise if noise.endswith("。") else noise + "。"
        return None

    def cafe_line(self):
        cafes = self.nearest("cafe", 5)
        if len(cafes) >= 3:
            return "駅から歩いて5分ほどの範囲にカフェがいくつもあり、本を読んだり作業をしたりできます。"
        if len(cafes) == 0 and self.scores.get("cafe", 50) < 30:
            return "駅のまわりにカフェは少ないので、外で過ごすなら隣の街まで出ます。"
        return None

    def indoor_trip_line(self):
        if not self.life:
            return None
        dest = [d for d in self.life["indoorDest"] if d["to"] != self.slug]
        if not dest:
            return "買い物や外食は、駅のまわりで済みます。"
        d = dest[0]
        return f"買い物や外食には、{self.station_name(d['to'])}まで電車で{d['minutes']}分ほどで出られます。"

    def outdoor_lines(self):
        out = []
        small = self.nearest("park", 6)
        if self.life and self.life["greenParks"]:
            out.append(f"歩いて行ける範囲に、広い公園（{self.life['greenParks'][0]}）があります。")
        elif small:
            out.append(f"歩いて{small[0]['walkMinutes']}分ほどの小さな公園（地図データ上の{small[0]['name']}）を散歩します。")
        if self.life:
            far = [d for d in self.life["outdoorDest"] if d["to"] != self.slug and d["parks"]]
            if far:
                d = far[0]
                out.append(f"休日は、{self.station_name(d['to'])}まで電車で{d['minutes']}分ほどの{d['parks'][0]}へ出かけます。")
        return out

    def small_park_line(self):
        small = self.nearest("park", 6)
        if small:
            return f"歩いて{small[0]['walkMinutes']}分ほどの小さな公園（地図データ上の{small[0]['name']}）を散歩します。"
        return None

    def gym_line(self):
        gyms = self.nearest("gym", 8)
        if gyms:
            return f"歩いて{gyms[0]['walkMinutes']}分ほどのジム（地図データ上の{gyms[0]['name']}）で体を動かします。"
        return None

    def medical_line(self):
        return first_sentence(self.content.get("medical"))

    def hospital_line(self):
        # 本文の「医療」と同じ病院を挙げる。地図データの病院と診療所の区別はぶれるので、
        # 本文を組み立てる側（build-station-content.py の sort_medical）で振り分け直している。
        for sent in re.split(r"(?<=。)", self.content.get("medical") or ""):
            if sent.startswith("病院では、"):
                return sent
        return None

    def nursery_line(self):
        n = len(self.nearest("kindergarten", 15))
        if n:
            return f"朝、保育園に子どもを送ってから出勤します。保育園の空き状況は、{self.ward}のページで住所ごとに確かめておきます。"
        return f"朝、保育園に子どもを送ってから出勤します。空き状況は、{self.ward}のページで住所ごとに確かめておきます。"

    # --- 向いている点・工夫が要る点 ---

    GOOD = {
        "commute": "都心のオフィス街まで短い時間で通えます。",
        "shopping": "毎日の買い物が、駅のまわりで済みます。",
        "healthcare": "病院やクリニックが、歩いて行ける範囲にそろっています。",
        "safety": "駅のまわりで、暴行や空き巣のような重い犯罪の件数が少ないほうです。",
        "quietness": "駅のまわりは人の声も車の音も少なく、家で静かに過ごせます。",
        "family": "学校・保育園・公園が、歩いて行ける範囲にそろっています。",
        "food": "外食できる店が多く、食事に困りません。",
        "singleLife": "外食できる店やスーパーが近く、一人でも生活が駅のまわりで終わります。",
        "disaster": "大雨のときの浸水の想定も高潮の想定も、23区の駅の中では小さいほうです。",
        "rentLow": "家賃の額そのものは、23区の駅の中では安いほうです。",
    }
    CARE = {
        "commute": "都心のオフィス街までは時間がかかるので、勤め先によっては通勤が負担になります。",
        "shopping": "駅のまわりで日々の買い物ができる店は少なめです。",
        "healthcare": "歩いて行ける範囲の病院やクリニックは少なめです。",
        "safety": "駅のまわりで、暴行や空き巣のような重い犯罪の件数は多いほうです。",
        "quietness": "駅のまわりは人の声か車の音が多く、部屋の場所によっては音が気になります。",
        "family": "学校・保育園・公園は、歩いて行ける範囲に多くありません。",
        "food": "外食できる店は少ないので、食事は家で作ることが多くなります。",
        "singleLife": "自炊をしないと、一人暮らしの生活が駅のまわりで終わりにくい環境です。",
        "disaster": "大雨のときの浸水の想定か高潮の想定がある区画が多いので、住所ごとにハザードマップで確かめます。",
        "rentLow": "家賃の額そのものは、23区の駅の中では高いほうです。",
    }
    AXES = {
        "single": ["singleLife", "safety", "shopping", "commute", "rentLow"],
        "dinks": ["commute", "food", "safety", "shopping", "healthcare", "rentLow"],
        "family": ["family", "safety", "shopping", "healthcare", "disaster", "quietness", "rentLow"],
        "senior": ["healthcare", "shopping", "quietness", "safety", "disaster", "rentLow"],
    }

    def axis_usable(self, axis):
        """
        浸水の想定は、23区の駅どうしで比べた点だけで「小さいほう」と書かない。
        中目黒は点では中ほどだが、駅の地点が浸水想定区域に入っている。
        駅の地点と、駅のまわりで見た地点のどちらにも想定が無いときだけ「小さい」と書き、
        駅の地点が区域に入るか、まわりの半分以上が入るときだけ「工夫が要る」と書く。
        """
        if axis != "disaster":
            return True
        kinds = [self.hazard.get(k) or {} for k in ("flood", "hightide", "tsunami")]
        at_station = any(k.get("atStation") for k in kinds)
        around = max((k.get("aroundCount") or 0) / max(1, k.get("aroundTotal") or 9) for k in kinds)
        score = self.scores.get("disaster", 50)
        if score >= 55:
            return not at_station and around == 0
        if score < 45:
            return at_station or around >= 0.5
        return False

    def good_care(self, persona, used):
        """向いている点と工夫が要る点。本文にもう出ている文と同じものは選ばない。"""
        vals = sorted(((self.scores[a], a) for a in self.AXES[persona]
                       if a in self.scores and self.axis_usable(a)),
                      reverse=True)
        if not vals:
            return None, None
        goods = [self.GOOD[a] for v, a in vals if v >= 55 and self.GOOD[a] not in used]
        cares = [self.CARE[a] for v, a in reversed(vals) if v < 45 and self.CARE[a] not in used]
        good = goods[0] if goods else "どの点も23区の駅の中ほどで、大きく困る点も目立つ強みも少ない駅です。"
        care = cares[0] if cares else "大きく困る点は少ないですが、部屋ごとの騒音や坂は、内見で確かめておきます。"
        return good, care

    # --- 層ごと ---

    def build(self):
        days = {}
        slope = SLOPE_WEEKDAY.get((self.content.get("terrain") or {}).get("slope"))
        quiet, cafe, indoor_trip = self.quiet_line(), self.cafe_line(), self.indoor_trip_line()
        outdoor = self.outdoor_lines()
        gym = self.gym_line()
        hub = self.hubs(1)
        work = f"{HUB_NAMES[hub[0]['to']]}の会社に勤める" if hub else "都心の会社に勤める"

        def keep(items):
            return [x for x in items if x]

        def put(persona, who, weekday, indoor, outdoor_lines):
            good, care = self.good_care(persona, set(weekday) | set(indoor) | set(outdoor_lines))
            if not (weekday and indoor and outdoor_lines and good):
                return
            days[persona] = {"who": who, "weekday": weekday, "indoor": indoor,
                             "outdoor": outdoor_lines, "good": good, "care": care}

        put("single", f"一人暮らしで、{work}想定です。",
            keep([*self.commute_lines("single"), self.shopping_line("帰り道に", "夕食を買います"),
                  self.evening_line(),
                  "夜道の明るさと人通りは、部屋を決める前に夜に一度歩いて確かめておきます。"]),
            keep([quiet, cafe, indoor_trip]),
            keep([gym, *outdoor]))
        hubs = self.hubs()
        dinks_who = (f"共働きの夫婦で、勤め先は{HUB_NAMES[hubs[0]['to']]}と{HUB_NAMES[hubs[1]['to']]}の想定です。"
                     if len(hubs) > 1 else "共働きの夫婦の想定です。")
        put("dinks", dinks_who,
            keep([*self.commute_lines("dinks"), self.shopping_line("帰りの早いほうが", "食材を買います"),
                  self.evening_line()]),
            keep([quiet, indoor_trip]),
            keep(outdoor))
        put("family", "共働きで、保育園に通う子どもが1人いる想定です。",
            keep([self.nursery_line(), slope, self.shopping_line("夕方", "食材を買って帰ります")]),
            keep([quiet, indoor_trip]),
            keep(outdoor))
        put("senior", "退職した夫婦の想定です。",
            keep(["通勤はありません。", self.medical_line(), self.hospital_line(), slope]),
            keep([quiet, indoor_trip]),
            # 近所の散歩。広い公園が無い駅では outdoor[0] が小さな公園の文になるので、重ねない
            list(dict.fromkeys(keep(outdoor[:1] + [self.small_park_line()]))))
        return days


def main():
    roster = {s["slug"]: s for s in load(os.path.join(ROOT, "data", "roster", "stations.json"))}
    ctx = {
        "roster": roster,
        "scores": load(os.path.join(ROOT, "data", "computed", "scores.json")),
        "commutes": load(os.path.join(ROOT, "data", "computed", "commutes.json")),
        "pois": load(os.path.join(ROOT, "data", "computed", "pois.json"))["stations"],
        "hazard": load(os.path.join(ROOT, "data", "computed", "hazard.json")).get("stations", {}),
        "lifestyle": load(os.path.join(ROOT, "data", "computed", "lifestyle.json"))["stations"],
    }
    # 行き先の駅名は、駅ページの表示名（content.name）を使う
    ctx["names"] = {slug: load(os.path.join(CONTENT, f"{slug}.json"))["name"]
                    for slug in roster if os.path.exists(os.path.join(CONTENT, f"{slug}.json"))}
    only = set(sys.argv[1:])
    written = skipped = 0
    for slug in roster:
        if only and slug not in only:
            continue
        path = os.path.join(CONTENT, f"{slug}.json")
        if not os.path.exists(path):
            continue
        st = Station(slug, ctx)
        if st.content.get("personaDays") and st.content.get("personaDaysStatus") == "reviewed":
            skipped += 1
            continue
        days = st.build()
        if not days:
            continue
        st.content["personaDays"] = days
        # データだけから組み立てた。人が読み直した駅（reviewed）とは分けて、画面でそう添える
        st.content["personaDaysStatus"] = "generated"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(st.content, f, ensure_ascii=False, indent=2)
            f.write("\n")
        written += 1
    print(f"組み立てた駅: {written} / 人が読み直した駅（触らない）: {skipped}")


if __name__ == "__main__":
    main()
