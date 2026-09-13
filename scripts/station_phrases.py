#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅コンテンツの文型を言語ごとに持つ表。scripts/build-station-content.py が読む。

組み立ての手順は言語によらず同じで、変わるのはここにある文型だけである。
言語を1つ足すときは PHRASES にキーを1つ増やし、同じキーの文型をすべて埋める。
埋め忘れは build-station-content.py が起動時に見つける。

金額・数の書き方も言語ごとに違うので、その関数と語形もここに置く。
日本語は「12万円」、英語は "¥120,000" と書く。英語だけは単数と複数で
語形が変わるので、words に両方を持たせている。

**駅名・路線名の扱い**
英語には出典データが持つローマ字と英語名を使う。
簡体字中国語と韓国語には、確認できる訳名の一覧を持っていないため、
駅名と路線名は日本語の表記のままにする。駅の看板に出ている表記と同じものを
読み手に渡すことになる（CLAUDE.md ルール35）。
区名だけは23件の閉じた集合なので、韓国語には韓国語表記を用意した。
"""


def man(yen):
    """円を「12万」の形にする。1万円未満の端数は小数第1位まで見せる。"""
    v = yen / 10000
    return f"{v:.0f}万" if abs(v - round(v)) < 0.05 else f"{v:.1f}万"


def yen(amount):
    """円を "¥120,000" の形にする。"""
    return f"¥{amount:,}"


def wan(amount):
    """円を「12万」の形にする（簡体字中国語・韓国語も万を単位にする）。"""
    v = amount / 10000
    return f"{v:.0f}万" if abs(v - round(v)) < 0.05 else f"{v:.1f}万"


# 韓国語の区名。23区は閉じた集合なので、訳名を持っておく。
WARD_KO = {
    "chiyoda": "지요다구", "chuo": "주오구", "minato": "미나토구",
    "shinjuku": "신주쿠구", "bunkyo": "분쿄구", "taito": "다이토구",
    "sumida": "스미다구", "koto": "고토구", "shinagawa": "시나가와구",
    "meguro": "메구로구", "ota": "오타구", "setagaya": "세타가야구",
    "shibuya": "시부야구", "nakano": "나카노구", "suginami": "스기나미구",
    "toshima": "도시마구", "kita": "기타구", "arakawa": "아라카와구",
    "itabashi": "이타바시구", "nerima": "네리마구", "adachi": "아다치구",
    "katsushika": "가쓰시카구", "edogawa": "에도가와구",
}

PHRASES = {
    "ja": {
        "money": man,
        "moneyUnit": "円",
        "listSep": "、",
        "lastSep": "、",
        "words": {"line": ("路線", "路線"), "clinic": ("件", "件"),
                  "pharmacy": ("件", "件"), "minute": ("分", "分")},
        "hubs": {"otemachi": "大手町", "shinjuku": "新宿", "shibuya": "渋谷",
                 "tokyo": "東京", "shinagawa": "品川", "toranomon": "虎ノ門",
                 "roppongi": "六本木"},
        "slope": {"flat": "ほぼ平坦である", "some": "ゆるやかな坂がある",
                  "hilly": "起伏が大きい"},
        "operator": {"jr": "JR", "tokyo-metro": "東京メトロ", "toei": "都営",
                     "private": "私鉄"},
        "company": {"jr-east": "JR東日本", "tokyo-metro": "東京メトロ", "toei": "東京都交通局",
                    "tobu": "東武", "seibu": "西武", "keisei": "京成", "keio": "京王",
                    "odakyu": "小田急", "tokyu": "東急", "keikyu": "京急",
                    "saitama-railway": "埼玉高速鉄道", "tsukuba-express": "つくばエクスプレス",
                    "yurikamome": "ゆりかもめ", "tokyo-monorail": "東京モノレール",
                    "rinkai": "東京臨海高速鉄道", "hokuso": "北総鉄道"},
        "depth": {"0.5m未満": "0.5m未満", "0.5〜3m": "0.5〜3m",
                  "3〜5m": "3〜5m", "5〜10m": "5〜10m"},
        "ward": lambda st: st["wardNameJa"],
        "lineName": lambda line: line["nameJa"],
        "stationName": lambda st: st["nameJa"],

        "commuteItem": "{hub}へ{minutes}{minuteWord}",
        "reachItem": "{hub}へ{minutes}{minuteWord}",
        "tagline": "{reach}で着く。{lineCount}{lineWord}が乗り入れる。{rent}",
        "taglineRent": "ワンルームの家賃はおよそ{low}〜{high}{unit}である。",

        "summaryWhere": "{ward}にあり、{lines}が乗り入れる。",
        "summaryCommute": "主なオフィス街までの所要時間は、{items}である。",
        "summaryTerrain": "駅の標高は{elevation}mで、周囲800mの標高差は{spread}mある。"
                          "駅の周りの土地は{slope}。",

        "terrainLow": "駅は周囲より低い場所にあり",
        "terrainHigh": "駅は周囲の中では高いほうにあり",
        "terrainNote": "{where}、標高は{elevation}mである。"
                       "周囲800mの標高は{min}mから{max}mまで分かれ、その差は{spread}mある。"
                       "国土地理院の標高APIから、駅と半径400mの8方位、計9点を読み取った値である。",

        "floodAtStation": "洪水浸水想定区域（想定最大規模）では、駅の地点が区域に入り、"
                          "想定される深さは{depth}である。",
        "floodNearOnly": "洪水浸水想定区域（想定最大規模）では、駅の地点は区域の外にある。",
        "floodNone": "洪水浸水想定区域（想定最大規模）では、駅の地点も、"
                     "駅から400m以内の9地点も、いずれも区域の外にある。",
        "floodAround": "駅から400m以内で見た9地点のうち{count}地点が区域に含まれ、"
                       "その中で最も深い想定は{deepest}である。",
        "hightide": "高潮についても9地点のうち{count}地点が想定区域に入る。",
        "hazardTrailer": "想定される深さは同じ駅でも区画ごとに違うので、"
                         "住所ごとに区のハザードマップで確認したい。"
                         "内水氾濫は全国共通の地図が公開されておらず区が個別に出しているため、"
                         "あわせて見ておきたい。",

        "medicalCounts": "駅から歩いて800m以内に、{items}ある。",
        "medicalClinics": "クリニックが{count}{clinicWord}",
        "medicalPharmacies": "薬局が{count}{pharmacyWord}",
        "medicalNone": "駅から歩いて800m以内には、OpenStreetMap に登録されている"
                       "クリニックも薬局も見当たらない。",
        "medicalHospitals": "病院として登録されている施設は、{items}の距離にある。",
        "medicalHospitalItem": "{name}が{distance}mほど",
        "medicalNoHospital": "駅から2.5km以内には、病院として登録されている施設が見当たらない。",
        "medicalTrailer": "入院できるかどうか、何科があるかまでは OpenStreetMap には"
                          "書かれていないので、各施設のウェブサイトで確かめてほしい。"
                          "夜間や休日にかかれる医療機関は、住む区の救急相談窓口で確認できる。",

        "stationLines": "{lines}の{count}{lineWord}が使える。",
        "stationSingleLine": "乗り入れは1路線だけなので、その路線が止まったときは、"
                             "ほかの路線が通る駅まで歩くことになる。",
        "stationOperatorItem": "{operator}が{count}{lineWord}",
        "stationMixedOperators": "運営は{breakdown}に分かれているので、"
                                 "1つの路線が止まっても、別の運営会社の路線に乗り換えられる。",
        "stationSameOperator": "{count}{lineWord}とも{operator}の路線なので、"
                               "運営会社全体に及ぶ障害のときは、まとめて止まることがある。",
        "stationTransitScore": "路線数と事業者の広がりから計算した乗換の利便性は、"
                               "100点満点で{score}点である。",

        "rentLabels": {"oneRoom": "ワンルーム", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label}が{low}〜{high}{unit}",
        "rentNote": "{items}である。LIFULL HOME'S・Yahoo!不動産・アットホームが公開する"
                    "駅別の相場を平均し、1万円刻みに丸めた（当社調べ）。"
                    "いずれも募集賃料のため、実際の成約額はこれより下がることがある。"
                    "同じ駅でも築年数・駅からの距離・通り沿いかどうかで大きく変わる。",
        "rentDrivers": ["築年数と構造", "駅からの距離", "幹線道路や線路に面しているか",
                        "坂の上か下か", "間取りに対する専有面積"],
        "rentReason": "ワンルームの相場は{low}〜{high}{unit}である。",
        "rentWideSpread": "ただし{layouts}は出典の値が3万円以上ひらいており、"
                          "集計の対象が違うぶん幅を持って見たほうがよい。",
        "rentWideSep": "・",

        "neighbourDistance": "直線で{meters}mの距離にある。",
        "neighbourSame": "大手町へは{station}と同じくらいの時間で着く。",
        "neighbourSlower": "大手町へは{station}より{minutes}{minuteWord}多くかかる。",
        "neighbourFaster": "大手町へは{station}より{minutes}{minuteWord}早く着く。",
        "neighbourRentHigher": "ワンルームの相場は{amount}{unit}ほど高い。",
        "neighbourRentLower": "ワンルームの相場は{amount}{unit}ほど安い。",

        "goodOtemachi": "大手町・丸の内方面へ通勤する人",
        "goodShinjuku": "新宿方面へ通勤する人",
        "goodManyLines": "路線が止まったときに別の経路を使いたい人",
        "goodFlat": "自転車やベビーカーで動くことが多い人",
        "goodShopping": "徒歩圏で買い物を済ませたい人",
        "goodNature": "公園が近いことを重視する人",
        "goodDry": "洪水の浸水想定区域を避けたい人",
        "goodCheap": "家賃を抑えたい単身者",
        "goodUnknown": "データからは、際立った向き先を読み取れていない",
        "badFlood": "洪水の浸水想定区域を避けたい人",
        "badHilly": "坂の上り下りを避けたい人",
        "badOneLine": "運転見合わせのときに別の経路が欲しい人",
        "badShopping": "徒歩圏で買い物を済ませたい人",
        "badFood": "外食できる店の多さを求める人",
        "badExpensive": "家賃を抑えたい人",
        "badUnknown": "この駅ならではの弱点は、データからは読み取れていない",
    },

    "en": {
        "money": yen,
        "moneyUnit": "",
        "listSep": ", ",
        "lastSep": " and ",
        "words": {"line": ("line", "lines"), "clinic": ("clinic", "clinics"),
                  "pharmacy": ("pharmacy", "pharmacies"),
                  "minute": ("minute", "minutes")},
        "hubs": {"otemachi": "Otemachi", "shinjuku": "Shinjuku", "shibuya": "Shibuya",
                 "tokyo": "Tokyo", "shinagawa": "Shinagawa", "toranomon": "Toranomon",
                 "roppongi": "Roppongi"},
        "slope": {"flat": "is close to level", "some": "has gentle slopes",
                  "hilly": "rises and falls sharply"},
        "operator": {"jr": "JR", "tokyo-metro": "Tokyo Metro", "toei": "Toei",
                     "private": "private railways"},
        "company": {"jr-east": "JR East", "tokyo-metro": "Tokyo Metro",
                    "toei": "the Tokyo Metropolitan Bureau of Transportation",
                    "tobu": "Tobu", "seibu": "Seibu", "keisei": "Keisei", "keio": "Keio",
                    "odakyu": "Odakyu", "tokyu": "Tokyu", "keikyu": "Keikyu",
                    "saitama-railway": "Saitama Railway",
                    "tsukuba-express": "Tsukuba Express", "yurikamome": "Yurikamome",
                    "tokyo-monorail": "Tokyo Monorail",
                    "rinkai": "Tokyo Waterfront Area Rapid Transit",
                    "hokuso": "Hokuso Railway"},
        "depth": {"0.5m未満": "less than 0.5 m", "0.5〜3m": "0.5 to 3 m",
                  "3〜5m": "3 to 5 m", "5〜10m": "5 to 10 m"},
        "ward": lambda st: st["ward"].capitalize() + " City",
        "lineName": lambda line: line["nameEn"],
        "stationName": lambda st: st["nameRomaji"],

        "commuteItem": "{minutes} {minuteWord} to {hub}",
        "reachItem": "{hub} in {minutes} {minuteWord}",
        "tagline": "{reach}. Served by {lineCount} {lineWord}. {rent}",
        "taglineRent": "A one-room flat rents for roughly {low} to {high}.",

        "summaryWhere": "The station is in {ward}, served by {lines}. ",
        "summaryCommute": "Journey times to the main business districts are {items}. ",
        "summaryTerrain": "The station stands {elevation} m above sea level, and the ground "
                          "within 800 m varies in height by {spread} m. The land around the "
                          "station {slope}.",

        "terrainLow": "The station sits lower than the ground around it",
        "terrainHigh": "The station sits on the higher side of the ground around it",
        "terrainNote": "{where}, at {elevation} m above sea level. Within 800 m the ground "
                       "ranges from {min} m to {max} m, a difference of {spread} m. "
                       "These figures were read from the elevation API of the Geospatial "
                       "Information Authority of Japan at nine points: the station itself "
                       "and eight compass directions 400 m out.",

        "floodAtStation": "On the flood hazard map for the largest rainfall the government "
                          "models, the station itself falls inside the projected inundation "
                          "area, to a projected depth of {depth}. ",
        "floodNearOnly": "On the flood hazard map for the largest rainfall the government "
                         "models, the station itself falls outside the projected inundation "
                         "area. ",
        "floodNone": "On the flood hazard map for the largest rainfall the government models, "
                     "neither the station nor any of the nine points within 400 m of it falls "
                     "inside the projected inundation area. ",
        "floodAround": "Of the nine points within 400 m of the station, {count} fall inside "
                       "the area, and the deepest projection among them is {deepest}. ",
        "hightide": "For storm surge, {count} of the nine points also fall inside the "
                    "projected area. ",
        "hazardTrailer": "The projected depth differs block by block within the same station "
                         "area, so check the ward hazard map for the specific address. "
                         "Inland flooding from overwhelmed drains has no nationwide map; each "
                         "ward publishes its own, and that is worth reading as well.",

        "medicalCounts": "Within an 800 m walk of the station there are {items}. ",
        "medicalClinics": "{count} {clinicWord}",
        "medicalPharmacies": "{count} {pharmacyWord}",
        "medicalNone": "Within an 800 m walk of the station, OpenStreetMap records neither a "
                       "clinic nor a pharmacy. ",
        "medicalHospitals": "Facilities recorded as hospitals lie at {items}. ",
        "medicalHospitalItem": "{name}, about {distance} m away",
        "medicalNoHospital": "No facility recorded as a hospital lies within 2.5 km of the "
                             "station. ",
        "medicalTrailer": "OpenStreetMap does not record whether a facility admits inpatients "
                          "or which departments it runs, so check each one on its own website. "
                          "For which clinics open at night and at weekends, ask the emergency "
                          "advice line of the ward you live in.",

        "stationLines": "{count} {lineWord} serve the station: {lines}. ",
        "stationSingleLine": "Only one line runs here, so when it stops you will be walking to "
                             "a station on another line. ",
        "stationOperatorItem": "{operator} runs {count} {lineWord}",
        "stationMixedOperators": "The lines are split between operators ({breakdown}), so when "
                                 "one line stops you can change to a line run by a different "
                                 "company. ",
        "stationSameOperator": "All {count} {lineWord} are run by {operator}, so a fault "
                               "affecting that company can stop them together. ",
        "stationTransitScore": "Scored out of 100 from the number of lines and the spread of "
                               "operators, transfer convenience here comes to {score}.",

        "rentLabels": {"oneRoom": "One room", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label} {low} to {high}",
        "rentNote": "{items}. These are the per-station averages published by LIFULL HOME'S, "
                    "Yahoo! Real Estate and at home, averaged together and rounded down to the "
                    "nearest ¥10,000 (our own survey). All three are asking rents, so what "
                    "tenants finally agree can be lower. Within the same station area the "
                    "figure moves a great deal with the age of the building, the walk from the "
                    "station, and whether the flat faces a main road.",
        "rentDrivers": ["Age and construction of the building",
                        "Walking distance from the station",
                        "Whether it faces a main road or the railway",
                        "Whether it sits at the top or the bottom of a slope",
                        "Floor area for the layout"],
        "rentReason": "A one-room flat here goes for {low} to {high}. ",
        "rentWideSpread": "For {layouts}, though, the sources differ by ¥30,000 or more. They "
                          "count different sets of properties, so read those figures as a "
                          "range rather than a point.",
        "rentWideSep": ", ",

        "neighbourDistance": "{meters} m away in a straight line. ",
        "neighbourSame": "It reaches Otemachi in about the same time as {station}. ",
        "neighbourSlower": "It takes {minutes} {minuteWord} longer to reach Otemachi than "
                           "{station}. ",
        "neighbourFaster": "It reaches Otemachi {minutes} {minuteWord} sooner than {station}. ",
        "neighbourRentHigher": "One-room rents run about {amount} higher.",
        "neighbourRentLower": "One-room rents run about {amount} lower.",

        "goodOtemachi": "People commuting to Otemachi and Marunouchi",
        "goodShinjuku": "People commuting towards Shinjuku",
        "goodManyLines": "People who want another route when a line stops",
        "goodFlat": "People who get around by bicycle or with a pushchair",
        "goodShopping": "People who want to finish their shopping on foot",
        "goodNature": "People who want a park close by",
        "goodDry": "People avoiding projected flood inundation areas",
        "goodCheap": "People living alone who want to hold the rent down",
        "goodUnknown": "The data does not show a clear group this station suits",
        "badFlood": "People avoiding projected flood inundation areas",
        "badHilly": "People who would rather not walk up and down slopes",
        "badOneLine": "People who want another route when service is suspended",
        "badShopping": "People who want to finish their shopping on foot",
        "badFood": "People who want plenty of places to eat out",
        "badExpensive": "People who want to hold the rent down",
        "badUnknown": "The data does not show a drawback particular to this station",
    },

    "zh-Hans": {
        "money": wan,
        "moneyUnit": "日元",
        "listSep": "、",
        "lastSep": "、",
        "words": {"line": ("条线路", "条线路"), "clinic": ("家", "家"),
                  "pharmacy": ("家", "家"), "minute": ("分钟", "分钟")},
        "hubs": {"otemachi": "大手町", "shinjuku": "新宿", "shibuya": "涩谷",
                 "tokyo": "东京", "shinagawa": "品川", "toranomon": "虎之门",
                 "roppongi": "六本木"},
        "slope": {"flat": "基本平坦", "some": "有缓坡", "hilly": "起伏较大"},
        "operator": {"jr": "JR", "tokyo-metro": "东京地铁", "toei": "都营地铁",
                     "private": "私营铁路"},
        "company": {"jr-east": "JR东日本", "tokyo-metro": "东京地铁",
                    "toei": "东京都交通局", "tobu": "东武", "seibu": "西武",
                    "keisei": "京成", "keio": "京王", "odakyu": "小田急",
                    "tokyu": "东急", "keikyu": "京急", "saitama-railway": "埼玉高速铁道",
                    "tsukuba-express": "筑波快线", "yurikamome": "百合鸥线",
                    "tokyo-monorail": "东京单轨电车", "rinkai": "东京临海高速铁道",
                    "hokuso": "北总铁道"},
        "depth": {"0.5m未満": "不足0.5米", "0.5〜3m": "0.5至3米",
                  "3〜5m": "3至5米", "5〜10m": "5至10米"},
        "ward": lambda st: st["wardNameJa"],
        "lineName": lambda line: line["nameJa"],
        "stationName": lambda st: st["nameJa"],

        "commuteItem": "到{hub}{minutes}{minuteWord}",
        "reachItem": "到{hub}{minutes}{minuteWord}",
        "tagline": "{reach}。有{lineCount}{lineWord}经过。{rent}",
        "taglineRent": "一室户的租金大致为{low}至{high}{unit}。",

        "summaryWhere": "车站位于{ward}，有{lines}经过。",
        "summaryCommute": "到主要商务区的所需时间为：{items}。",
        "summaryTerrain": "车站海拔{elevation}米，周边800米范围内的高低差为{spread}米。"
                          "车站周围的地形{slope}。",

        "terrainLow": "车站所在的位置低于周围",
        "terrainHigh": "车站所在的位置在周围属于较高的一侧",
        "terrainNote": "{where}，海拔{elevation}米。周边800米范围内，海拔从{min}米到{max}米，"
                       "相差{spread}米。以上数值取自日本国土地理院的海拔API，"
                       "读取了车站本身和半径400米的八个方位，共九个点。",

        "floodAtStation": "在按可能出现的最大降雨量推算的洪水浸水想定区域中，"
                          "车站所在的地点被划入区域，推算的水深为{depth}。",
        "floodNearOnly": "在按可能出现的最大降雨量推算的洪水浸水想定区域中，"
                         "车站所在的地点在区域之外。",
        "floodNone": "在按可能出现的最大降雨量推算的洪水浸水想定区域中，"
                     "车站所在的地点，以及车站400米以内的九个点，都在区域之外。",
        "floodAround": "在车站400米以内查看的九个点中，有{count}个点被划入区域，"
                       "其中推算最深的水深为{deepest}。",
        "hightide": "风暴潮方面，九个点中也有{count}个点被划入想定区域。",
        "hazardTrailer": "同一个车站周边，推算的水深也会因街区而异，"
                         "所以请按具体地址查看所在区发布的灾害地图。"
                         "内涝没有全国统一的地图，由各区分别发布，也一并看一看为好。",

        "medicalCounts": "从车站步行800米以内，有{items}。",
        "medicalClinics": "诊所{count}{clinicWord}",
        "medicalPharmacies": "药店{count}{pharmacyWord}",
        "medicalNone": "从车站步行800米以内，OpenStreetMap 上没有登记的诊所和药店。",
        "medicalHospitals": "登记为医院的设施，距离为{items}。",
        "medicalHospitalItem": "{name}约{distance}米",
        "medicalNoHospital": "车站2.5公里以内，没有登记为医院的设施。",
        "medicalTrailer": "能否住院、设有哪些科室，OpenStreetMap 上没有记载，"
                          "请到各设施的网站上确认。夜间和休息日能就诊的医疗机构，"
                          "可以向所住区的急救咨询窗口查询。",

        "stationLines": "可以使用{lines}这{count}{lineWord}。",
        "stationSingleLine": "只有一条线路经过，这条线路停运时，"
                             "就要步行到有其他线路经过的车站。",
        "stationOperatorItem": "{operator}{count}{lineWord}",
        "stationMixedOperators": "运营方分为{breakdown}，"
                                 "所以一条线路停运时，可以换乘另一家公司的线路。",
        "stationSameOperator": "{count}{lineWord}都由{operator}运营，"
                               "遇到波及整个运营公司的故障时，可能会一起停运。",
        "stationTransitScore": "按线路数量和运营方的分散程度计算，"
                               "换乘便利度为{score}分（满分100分）。",

        "rentLabels": {"oneRoom": "一室户", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label}{low}至{high}{unit}",
        "rentNote": "{items}。取 LIFULL HOME'S、Yahoo!不动产、at home 三家公布的"
                    "分车站行情的平均值，并向下取整到1万日元（本公司调查）。"
                    "三者都是招租价格，实际成交的金额可能低于此。"
                    "即使是同一个车站，房龄、离车站的距离、是否临街，都会让金额差出很多。",
        "rentDrivers": ["房龄和建筑结构", "离车站的步行距离", "是否临主干道或铁路",
                        "在坡上还是坡下", "相对于户型的实际面积"],
        "rentReason": "一室户的行情为{low}至{high}{unit}。",
        "rentWideSpread": "不过{layouts}的各家数值相差3万日元以上，"
                          "统计的对象不同，看的时候应留出幅度。",
        "rentWideSep": "、",

        "neighbourDistance": "直线距离{meters}米。",
        "neighbourSame": "到大手町的时间与{station}差不多。",
        "neighbourSlower": "到大手町比{station}多花{minutes}{minuteWord}。",
        "neighbourFaster": "到大手町比{station}早到{minutes}{minuteWord}。",
        "neighbourRentHigher": "一室户的行情高出{amount}{unit}左右。",
        "neighbourRentLower": "一室户的行情低出{amount}{unit}左右。",

        "goodOtemachi": "到大手町、丸之内一带通勤的人",
        "goodShinjuku": "到新宿方向通勤的人",
        "goodManyLines": "希望线路停运时还有其他路线可走的人",
        "goodFlat": "经常骑自行车或推婴儿车出行的人",
        "goodShopping": "希望步行范围内就能买齐东西的人",
        "goodNature": "看重公园就在附近的人",
        "goodDry": "希望避开洪水浸水想定区域的人",
        "goodCheap": "希望压低租金的单身者",
        "goodUnknown": "从数据中看不出这个车站特别适合哪一类人",
        "badFlood": "希望避开洪水浸水想定区域的人",
        "badHilly": "不想上下坡的人",
        "badOneLine": "希望停运时还有其他路线可走的人",
        "badShopping": "希望步行范围内就能买齐东西的人",
        "badFood": "看重外出就餐的店铺数量的人",
        "badExpensive": "希望压低租金的人",
        "badUnknown": "从数据中看不出这个车站特有的短处",
    },

    "ko": {
        "money": wan,
        "moneyUnit": "엔",
        "listSep": ", ",
        "lastSep": ", ",
        "words": {"line": ("개 노선", "개 노선"), "clinic": ("곳", "곳"),
                  "pharmacy": ("곳", "곳"), "minute": ("분", "분")},
        "hubs": {"otemachi": "오테마치", "shinjuku": "신주쿠", "shibuya": "시부야",
                 "tokyo": "도쿄", "shinagawa": "시나가와", "toranomon": "도라노몬",
                 "roppongi": "롯폰기"},
        "slope": {"flat": "거의 평탄하다", "some": "완만한 언덕이 있다",
                  "hilly": "높낮이 차이가 크다"},
        "operator": {"jr": "JR", "tokyo-metro": "도쿄메트로", "toei": "도영지하철",
                     "private": "사철"},
        "company": {"jr-east": "JR동일본", "tokyo-metro": "도쿄메트로",
                    "toei": "도쿄도 교통국", "tobu": "도부", "seibu": "세이부",
                    "keisei": "게이세이", "keio": "게이오", "odakyu": "오다큐",
                    "tokyu": "도큐", "keikyu": "게이큐",
                    "saitama-railway": "사이타마 고속철도",
                    "tsukuba-express": "쓰쿠바 익스프레스", "yurikamome": "유리카모메",
                    "tokyo-monorail": "도쿄모노레일",
                    "rinkai": "도쿄 임해고속철도", "hokuso": "호쿠소 철도"},
        "depth": {"0.5m未満": "0.5m 미만", "0.5〜3m": "0.5~3m",
                  "3〜5m": "3~5m", "5〜10m": "5~10m"},
        "ward": lambda st: WARD_KO[st["ward"]],
        "lineName": lambda line: line["nameJa"],
        "stationName": lambda st: st["nameJa"],

        "commuteItem": "{hub}까지 {minutes}{minuteWord}",
        "reachItem": "{hub}까지 {minutes}{minuteWord}",
        "tagline": "{reach}. {lineCount}{lineWord}이 지난다. {rent}",
        "taglineRent": "원룸 임대료는 대략 {low}~{high}{unit}이다.",

        "summaryWhere": "역은 {ward}에 있으며, {lines} 노선이 지난다. ",
        "summaryCommute": "주요 업무지구까지 걸리는 시간은 {items}이다. ",
        "summaryTerrain": "역의 표고는 {elevation}m이고, 주변 800m 안의 표고 차이는 "
                          "{spread}m이다. 역 주변의 땅은 {slope}. ",

        "terrainLow": "역은 주변보다 낮은 곳에 있고",
        "terrainHigh": "역은 주변 중에서는 높은 쪽에 있고",
        "terrainNote": "{where}, 표고는 {elevation}m이다. 주변 800m 안의 표고는 {min}m부터 "
                       "{max}m까지 나뉘며, 그 차이는 {spread}m이다. 일본 국토지리원의 "
                       "표고 API에서 역과 반경 400m의 여덟 방위, 모두 아홉 지점을 읽은 값이다.",

        "floodAtStation": "상정할 수 있는 최대 규모의 강우를 전제로 한 홍수 침수 상정 구역에서, "
                          "역이 있는 지점이 구역에 들어가며 상정되는 깊이는 {depth}이다. ",
        "floodNearOnly": "상정할 수 있는 최대 규모의 강우를 전제로 한 홍수 침수 상정 구역에서, "
                         "역이 있는 지점은 구역 밖에 있다. ",
        "floodNone": "상정할 수 있는 최대 규모의 강우를 전제로 한 홍수 침수 상정 구역에서, "
                     "역이 있는 지점도, 역에서 400m 안의 아홉 지점도 모두 구역 밖에 있다. ",
        "floodAround": "역에서 400m 안에서 살펴본 아홉 지점 가운데 {count}곳이 구역에 들어가며, "
                       "그중 가장 깊게 상정된 깊이는 {deepest}이다. ",
        "hightide": "폭풍해일에 대해서도 아홉 지점 가운데 {count}곳이 상정 구역에 들어간다. ",
        "hazardTrailer": "같은 역이라도 구획마다 상정되는 깊이가 다르므로, 주소별로 구청이 "
                         "내놓은 재해 지도에서 확인하는 것이 좋다. 내수 범람은 전국 공통의 "
                         "지도가 공개되어 있지 않고 구청이 각각 내놓고 있으니, 함께 보아 두자.",

        "medicalCounts": "역에서 걸어서 800m 안에 {items} 있다. ",
        "medicalClinics": "의원이 {count}{clinicWord}",
        "medicalPharmacies": "약국이 {count}{pharmacyWord}",
        "medicalNone": "역에서 걸어서 800m 안에는 OpenStreetMap에 등록된 의원도 약국도 "
                       "보이지 않는다. ",
        "medicalHospitals": "병원으로 등록된 시설은 {items} 거리에 있다. ",
        "medicalHospitalItem": "{name}까지 약 {distance}m",
        "medicalNoHospital": "역에서 2.5km 안에는 병원으로 등록된 시설이 보이지 않는다. ",
        "medicalTrailer": "입원할 수 있는지, 어떤 진료과가 있는지까지는 OpenStreetMap에 "
                          "적혀 있지 않으므로, 각 시설의 웹사이트에서 확인하기 바란다. "
                          "야간이나 휴일에 진료받을 수 있는 의료기관은 사는 구의 응급 상담 "
                          "창구에서 확인할 수 있다.",

        "stationLines": "{lines}의 {count}{lineWord}을 이용할 수 있다. ",
        "stationSingleLine": "지나는 노선이 하나뿐이므로, 그 노선이 멈추면 다른 노선이 "
                             "지나는 역까지 걸어가게 된다. ",
        "stationOperatorItem": "{operator} {count}{lineWord}",
        "stationMixedOperators": "운영은 {breakdown}으로 나뉘어 있어, 한 노선이 멈춰도 "
                                 "다른 운영 회사의 노선으로 갈아탈 수 있다. ",
        "stationSameOperator": "{count}{lineWord} 모두 {operator}이 운영하므로, 운영 회사 "
                               "전체에 미치는 장애가 나면 한꺼번에 멈출 수 있다. ",
        "stationTransitScore": "노선 수와 운영 회사가 나뉜 정도로 계산한 환승 편의성은 "
                               "100점 만점에 {score}점이다.",

        "rentLabels": {"oneRoom": "원룸", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label} {low}~{high}{unit}",
        "rentNote": "{items}이다. LIFULL HOME'S, Yahoo!부동산, at home이 공개하는 역별 시세를 "
                    "평균 내어 1만 엔 단위로 내림한 값이다(당사 조사). 모두 모집 임대료이므로, "
                    "실제로 계약되는 금액은 이보다 낮아질 수 있다. 같은 역이라도 건축 연수, "
                    "역에서의 거리, 큰길에 면해 있는지에 따라 크게 달라진다.",
        "rentDrivers": ["건축 연수와 구조", "역에서의 도보 거리", "간선도로나 선로에 면해 있는지",
                        "언덕 위인지 아래인지", "구조 대비 전용 면적"],
        "rentReason": "원룸 시세는 {low}~{high}{unit}이다. ",
        "rentWideSpread": "다만 {layouts}은(는) 출처마다 값이 3만 엔 이상 벌어져 있다. "
                          "집계 대상이 다르므로 폭을 두고 보는 편이 좋다.",
        "rentWideSep": ", ",

        "neighbourDistance": "직선거리로 {meters}m 떨어져 있다. ",
        "neighbourSame": "오테마치까지 걸리는 시간은 {station}에서 갈 때와 비슷하다. ",
        "neighbourSlower": "오테마치까지 {station}보다 {minutes}{minuteWord} 더 걸린다. ",
        "neighbourFaster": "오테마치까지 {station}보다 {minutes}{minuteWord} 빨리 도착한다. ",
        "neighbourRentHigher": "원룸 시세는 {amount}{unit} 정도 비싸다.",
        "neighbourRentLower": "원룸 시세는 {amount}{unit} 정도 싸다.",

        "goodOtemachi": "오테마치, 마루노우치 방면으로 출퇴근하는 사람",
        "goodShinjuku": "신주쿠 방면으로 출퇴근하는 사람",
        "goodManyLines": "노선이 멈췄을 때 다른 경로를 쓰고 싶은 사람",
        "goodFlat": "자전거나 유모차로 다니는 일이 많은 사람",
        "goodShopping": "걸어서 장을 다 보고 싶은 사람",
        "goodNature": "공원이 가까운 것을 중요하게 보는 사람",
        "goodDry": "홍수 침수 상정 구역을 피하고 싶은 사람",
        "goodCheap": "임대료를 낮추고 싶은 1인 가구",
        "goodUnknown": "데이터로는 이 역이 특히 어떤 사람에게 맞는지 읽어낼 수 없다",
        "badFlood": "홍수 침수 상정 구역을 피하고 싶은 사람",
        "badHilly": "언덕을 오르내리는 것을 피하고 싶은 사람",
        "badOneLine": "운행이 중단됐을 때 다른 경로를 쓰고 싶은 사람",
        "badShopping": "걸어서 장을 다 보고 싶은 사람",
        "badFood": "외식할 수 있는 가게가 많기를 바라는 사람",
        "badExpensive": "임대료를 낮추고 싶은 사람",
        "badUnknown": "데이터로는 이 역만의 약점을 읽어낼 수 없다",
    },
}
