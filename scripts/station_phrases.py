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


def sen(amount):
    """1万円に満たない差を「6千」の形にする。「0.6万」は人が使わない言い方になる。"""
    return f"{round(amount / 1000)}千"


def yen(amount):
    """円を "¥120,000" の形にする。"""
    return f"¥{amount:,}"


def wan(amount):
    """円を「12万」の形にする（簡体字中国語）。"""
    v = amount / 10000
    return f"{v:.0f}万" if abs(v - round(v)) < 0.05 else f"{v:.1f}万"


def man_ko(amount):
    """円を「12만」の形にする。韓国語は万を漢字で書かない。"""
    v = amount / 10000
    return f"{v:.0f}만" if abs(v - round(v)) < 0.05 else f"{v:.1f}만"


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
        "moneySmall": sen,
        "moneyUnit": "円",
        "sentenceGap": "",
        "listSep": "、",
        "lastSep": "、",
        "words": {"line": ("路線", "路線"), "clinic": ("件", "件"),
                  "pharmacy": ("件", "件"), "minute": ("分", "分")},
        "hubs": {"otemachi": "大手町", "shinjuku": "新宿", "shibuya": "渋谷",
                 "tokyo": "東京", "shinagawa": "品川", "toranomon": "虎ノ門",
                 "roppongi": "六本木"},
        "slope": {"flat": "ほぼ平坦です", "some": "ゆるやかな坂があります",
                  "hilly": "起伏が大きくなっています"},
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
        "stationNameWithLine": "{name}（{line}）",

        "commuteItem": "{hub}へ{minutes}{minuteWord}",
        "reachItem": "{hub}へ{minutes}{minuteWord}",
        "tagline": "{reach}で着きます。{lineCount}{lineWord}が乗り入れます。{rent}",
        "taglineRent": "ワンルームの家賃相場はおよそ{low}〜{high}{unit}です。",

        "summaryWhere": "この駅は{ward}にあり、{lines}が乗り入れます。",
        "summaryWhereMany": "この駅は{ward}にあり、{operators}の{count}{lineWord}が乗り入れます。",
        "summaryCommute": "主なオフィス街までの所要時間は、{items}です。",
        "summaryTerrain": "駅の標高は{elevation}mで、周囲800mの標高差は{spread}mあります。"
                          "駅の周りの土地は{slope}。",

        "terrainLow": "駅は周囲より低い場所にあり",
        "terrainHigh": "駅は周囲の中では高いほうにあり",
        # どう測ったかは本文に書かない。節の下に出典としてリンクを出す
        # （src/components/StationDepth.tsx）。
        "terrainNote": "{where}、標高は{elevation}mです。"
                       "周囲800mの標高は{min}mから{max}mまで分かれ、その差は{spread}mあります。",

        # 事実を並べるだけにせず、つなぎの言葉で読ませる（ルール49）。
        # 想定の深さの注意と内水氾濫の案内は、駅ページが毎回出す注記
        # （dict.hazardNote）と重なるので、ここでは繰り返さない。
        "floodAtStation": "駅の地点が大雨のときの洪水浸水想定区域（想定最大規模）に入っており、"
                          "想定される深さは{depth}です。",
        "floodNearOnly": "駅の地点は、大雨のときの洪水浸水想定区域（想定最大規模）の外にあります。",
        "floodNone": "駅の地点も、駅から400m以内で見た9地点も、"
                     "大雨のときの洪水浸水想定区域（想定最大規模）の外にあります。",
        # 駅の地点が区域に入るかどうかで、つなぎの言葉を変える。
        "floodAroundAll": "駅のまわり400m以内で見た9地点も、すべて区域に含まれます。"
                          "その中で最も深い想定は{deepest}です。",
        "floodAroundSome": "駅のまわり400m以内で見た9地点のうち{count}地点も区域に含まれ、"
                           "その中で最も深い想定は{deepest}です。",
        "floodAroundOnly": "ただし駅のまわり400m以内で見た9地点のうち{count}地点は区域に入り、"
                           "その中で最も深い想定は{deepest}です。",
        "hightide": "高潮の想定区域にも、9地点のうち{count}地点が入ります。",
        "hazardTrailer5": "総じて、大雨のときの浸水の想定は23区の駅の中でもとても小さいほうです。",
        "hazardTrailer4": "総じて、大雨のときの浸水の想定は23区の駅の中では小さいほうです。",
        "hazardTrailer3": "総じて、大雨のときの浸水の想定は23区の駅の平均くらいです。",
        "hazardTrailer2": "総じて、大雨のときの浸水の想定は23区の駅の中では大きいほうです。",
        "hazardTrailer1": "総じて、大雨のときの浸水の想定は23区の駅の中でもとても大きいほうです。",

        "medicalCounts": "駅から歩いて800m以内に、{items}あります。",
        "medicalEnough": "日常のかかりつけは、駅の近くで選べます。",
        "medicalClinics": "クリニックが{count}{clinicWord}",
        "medicalPharmacies": "薬局が{count}{pharmacyWord}",
        "medicalNone": "駅から歩いて800m以内には、OpenStreetMap に登録されている"
                       "クリニックも薬局も見当たりません。",
        # 距離はメートルで書かない。どこから測った値なのかが読み手に伝わらず、
        # 細かい数字そのものも求められていない。駅から歩いて何分かで書く。
        "medicalHospitalNearest": "病院では、{name}が歩いて{minutes}分ほどの距離にあります。",
        "medicalHospitalSecond": "次に近いのは{name}で、歩いて{minutes}分ほどかかります。",
        "medicalNoHospital": "一方で、駅から2.5km以内に病院は見当たりません。",
        "medicalTrailer": "ただし入院できるかどうかと、何科があるかまでは分かりません。"
                          "気になる施設は、ウェブサイトで確かめてください。"
                          "夜間や休日にかかれる医療機関は、住む区の救急相談窓口で確認できます。",

        "congestionOnPeak": "{line}の朝の混雑率は{rate}%です。"
                            "この駅を含む{section}が、{line}でいちばん混む区間にあたります。",
        "congestionOffPeak": "{line}の朝の混雑率は{rate}%です。"
                             "いちばん混むのは{section}で、この駅はその区間に入りません。",
        "congestionOffPeak2": "{line}は{rate}%です。"
                              "こちらでいちばん混むのは{section}で、やはりこの駅は外にあります。",
        "congestionUnknown": "{lines}の混雑率は、国土交通省の調査では公表されていません。",
        "congestionAllUnknown": "{lines}の朝の混雑率は、国土交通省の調査では公表されていません。"
                                "この調査は主要な区間を対象にしており、"
                                "この路線は対象に入っていません。",
        "congestionScale4": "国土交通省の目安では、200%は体が触れ合って相当な圧迫感がある状態を指します。"
                            "ドア付近の人は身動きがとれません。",
        "congestionScale3": "国土交通省の目安では、180%は肩が触れ合ってやや圧迫感がある状態を指します。"
                            "ドア付近の人は、体の向きを変えるのが難しくなります。",
        "congestionScale2": "国土交通省の目安では、150%は肩が触れ合わない程度で、"
                            "ドア付近の人が多くなる状態を指します。"
                            "ここはおおむねその状態です。",
        "congestionScale1": "国土交通省の目安では150%で肩が触れ合わない程度になるので、"
                            "ここはそこまで混みません。",
        # 調査の方法は節の下に出典として出す（src/components/StationDepth.tsx）。
        "congestionTrailer": "ただしこの数字は路線の中でいちばん混む区間のものなので、"
                             "この駅から乗る区間が同じ混み方とは限りません。",
        "leadCongestion5": "使える路線の朝の混雑率は、23区の駅の中ではかなり低いほうです。",
        "leadCongestion4": "使える路線の朝の混雑率は、23区の駅の中では低いほうです。",
        "leadCongestion3": "使える路線の朝の混雑率は、23区の駅の平均くらいです。",
        "leadCongestion2": "使える路線の朝の混雑率は、23区の駅の中では高いほうです。",
        "leadCongestion1": "使える路線の朝の混雑率は、23区の駅の中でもかなり高いほうです。",
        "stationLines": "この駅では{lines}の{count}{lineWord}が使えます。",
        "stationLinesCount": "この駅で使えるのは{count}{lineWord}です。",
        "stationLinesHead": "{lines}が通ります。",
        "stationLinesMore": "加えて{lines}も乗り入れます。",
        "stationLinesMore2": "さらに{lines}も使えます。",
        "stationLinesMore3": "このほか{lines}も停まります。",
        "stationSingleLine": "乗り入れは1路線だけなので、その路線が止まったときは、"
                             "ほかの路線が通る駅まで歩くことになります。",
        "stationOperatorItem": "{operator}が{count}{lineWord}",
        "stationMixedOperators": "運営は{breakdown}に分かれています。"
                                 "1つの路線が止まっても、別の運営会社の路線に乗り換えられます。",
        "stationSameOperator": "{count}{lineWord}とも{operator}の路線です。"
                               "運営会社全体に及ぶ障害のときは、まとめて止まることがあります。",
        "stationSameOperatorTwo": "2路線とも{operator}の路線です。"
                                  "運営会社全体に及ぶ障害のときは、まとめて止まることがあります。",

        "rentLabels": {"oneRoom": "ワンルーム", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label}が{low}〜{high}{unit}",
        # 主語を省かない。何の金額なのかを文の先頭に置く。
        # 4間取りを1文に入れると60字を超えるので、2つずつに分ける（ルール43）。
        "rentNoteHead": "駅周辺の家賃相場は、{items}です。",
        "rentNoteMore": "{items}程度です。",
        "rentNoteTrailer": "いずれも LIFULL HOME'S・Yahoo!不動産・アットホームの"
                           "駅別の相場を平均した値です（当社調べ）。1万円刻みに丸めています。"
                           "どれも募集賃料のため、実際の成約額はこれより下がることがあります。"
                           "同じ駅でも築年数・駅からの距離・通り沿いかどうかで大きく変わります。",
        "rentDrivers": ["築年数と構造", "駅からの距離", "幹線道路や線路に面しているか",
                        "坂の上か下か", "間取りに対する専有面積"],
        "rentReason": "駅周辺のワンルームの家賃相場は{low}〜{high}{unit}です。",
        # 相場の数字を繰り返すだけでは、見出しの「理由」に答えていない（ルール49）。
        # 通勤時間に対してどの位置にあるかを書き、押し上げ・押し下げの材料を添える。
        "rentLevel5": "都心のオフィス街までの所要時間から見ると、"
                      "23区の駅の中でもかなり安い水準です。",
        "rentLevel4": "都心のオフィス街までの所要時間から見ると、安いほうの水準です。",
        "rentLevel3": "都心のオフィス街までの所要時間から見ると、"
                      "23区の駅の平均くらいの水準です。",
        "rentLevel2": "都心のオフィス街までの所要時間から見ると、高いほうの水準です。",
        "rentLevel1": "都心のオフィス街までの所要時間から見ると、"
                      "23区の駅の中でもかなり高い水準です。",
        "rentDown": "相場を抑えているのは、{items}です。",
        "rentUp": "相場を押し上げているのは、{items}です。",
        # 1文に両側を詰めると60字を超える（ルール43）。2文に分ける。
        "rentBoth": "{up}が、相場を押し上げる材料です。一方で{down}が、相場を抑えています。",
        "rentAbsoluteLow": "ただし金額そのものは、23区の駅の中では安いほうです。",
        "rentAbsoluteHigh": "ただし金額そのものは、23区の駅の中では高いほうです。",
        "rentFactorFlood": "大雨のときの浸水の想定が大きいこと",
        "rentFactorOneLine": "使える路線が1本だけであること",
        "rentFactorHilly": "住宅地へ出るのに坂を上ること",
        "rentFactorFewShops": "徒歩圏で買い物を済ませにくいこと",
        "rentFactorNoisy": "駅前に酒場が多いこと",
        "rentFactorManyLines": "{count}路線が使えること",
        "rentFactorDry": "大雨のときの浸水の想定が小さいこと",
        "rentFactorFamily": "学校や公園が歩いて行けること",
        "rentFactorQuiet": "駅のまわりが静かなこと",
        "rentFactorFood": "外食できる店が多いこと",
        "rentWideSpread": "ただし{layouts}は出典の値が3万円以上ひらいているため、"
                          "集計の対象が違うぶん幅を持って見てください。",
        "rentWideSep": "・",

        "leadTerrainFlat": "駅の周りはほぼ平坦で、坂を気にせず住む場所を選べます。",
        "leadTerrainSome": "駅の周りにはゆるやかな坂があり、どの区画に住むかで毎日の移動の負担が変わります。",
        "leadTerrainHilly": "駅の周りは起伏が大きく、坂の上に住むか下に住むかで毎日の移動の負担が変わります。",
        "leadGroceriesMany": "歩いて行けるスーパーが{count}軒あり、いちばん近い店までは徒歩{minutes}分です。",
        "leadGroceriesFew": "歩いて行けるスーパーは{count}軒で、いちばん近い店までは徒歩{minutes}分です。",
        "leadGroceriesNone": "駅から歩いて行けるスーパーを OpenStreetMap では確認できませんでした。",
        # 本文の締めが23区の中での位置を書くので、一言では駅の地点そのものを書く。
        "leadHazardAtStation": "駅の地点が、大雨のときの浸水想定区域に入っています。",
        "leadHazardNear": "駅の地点は区域の外ですが、まわりには浸水が想定される区画があります。",
        "leadHazardNone": "駅の地点も、そのまわりも、大雨のときの浸水想定区域の外にあります。",
        "leadStationMany": "{count}路線が使え、乗り換えの選択肢は23区の駅の中では多いほうです。",
        "leadStationMid": "{count}路線が使えます。乗り換えの選択肢は23区の駅の平均くらいです。",
        "leadStationOne": "使える路線は{line}の1本だけです。"
                          "止まった日は、別の駅まで歩いて別の路線に乗り換えることになります。",
        "leadRent5": "通勤にかかる時間に対して、家賃の相場は23区の駅の中でもかなり低いほうです。",
        "leadRent4": "通勤にかかる時間に対して、家賃の相場は低いほうです。",
        "leadRent3": "通勤にかかる時間と家賃の相場の関係は、23区の駅の平均くらいです。",
        "leadRent2": "通勤にかかる時間に対して、家賃の相場は高いほうです。",
        "leadRent1": "通勤にかかる時間に対して、家賃の相場は23区の駅の中でもかなり高いほうです。",
        "leadMedical5": "歩いて行けるクリニックと薬局の数は、23区の駅の中でもとても多いほうです。",
        "leadMedical4": "歩いて行けるクリニックと薬局の数は、23区の駅の中では多いほうです。",
        "leadMedical3": "歩いて行けるクリニックと薬局の数は、23区の駅の平均くらいです。",
        "leadMedical2": "歩いて行けるクリニックと薬局の数は、23区の駅の中では少ないほうです。",
        "leadMedical1": "歩いて行けるクリニックと薬局の数は、23区の駅の中では少ないほうです。",

        "roadSideOneway": "片側{n}車線",
        "roadSideBoth": "片側{n}車線",
        "roadSideUnknown": "大通り",
        # 道路までの距離もメートルで書かない。駅のすぐそばか、少し歩くかが分かれば足りる。
        "roadWhereAtStation": "駅のすぐそば",
        "roadWhereNear": "駅のすぐ近く",
        "roadWhereAway": "駅から少し歩いたところ",
        "noiseRoadVeryNear": "{name}（{side}の大通り）が{where}を通っています。"
                             "一日中、車の通りが絶えません。"
                             "駅に近い物件を見るときは、通りに面していないかを確かめてください",
        "noiseRoadMotorway": "{name}の高架が{where}を通ります。"
                             "高速道路なので、車の音は昼も夜も続きます",
        "noiseRoadBig": "{name}（{side}の大通り）が{where}にあります。一日中、車の通りが絶えません",
        "noiseRoadMid": "{name}（{side}）が{where}にあります。"
                        "通りに面した部屋では、朝夕の車の音が入ります",
        "noiseRoadAtStation": "{name}（{side}）が{where}にあります。"
                              "駅に近い物件を見るときは、"
                              "通りに面していないかを確かめてください",
        "noiseRoadFar": "いちばん近い大きな通りは{name}で、駅から離れています。"
                        "駅の周りは車の音が少なく、落ち着いています",
        # 道路名と距離は本文に書くので、ここでは繰り返さない。
        # 「一言でいうと」は、本文を読む前に結論だけを受け取るためのものである。
        "leadNoiseLoud": "人の声より先に、車の音を確かめたい駅です。",
        "leadNoiseMid": "沿道の部屋かどうかで、部屋の中で聞こえる車の音がはっきり変わります。",
        "leadNoiseQuiet": "大きな通りから離れており、車の音は気になりにくい駅です。",

        "cmpRentCheaper": "家賃相場は{station}のほうが安いです",
        "cmpRentSame": "家賃相場はほぼ同じです",
        "cmpAxisWin": "{axes}は{station}が上回ります",
        "cmpButJoin": "{a}。ただし{b}。",
        "cmpAndJoin": "{a}。{b}。",
        "cmpOnly": "{a}。",
        "cmpSep": "と",
        "cmpAxisDisaster": "大雨のときの浸水の想定の小ささ",
        "cmpAxisTransit": "使える路線の数",
        "cmpAxisCommute": "都心への近さ",
        "cmpAxisHealthcare": "医療機関の多さ",
        "cmpAxisShopping": "買い物のしやすさ",
        "cmpAxisQuiet": "静かさ",
        "cmpAxisSafety": "治安",
        "cmpAxisFamily": "子どもと暮らす条件",
        "cmpAxisFood": "外食できる店の多さ",
        "cmpNothing": "家賃も通勤も災害の想定も、大きくは変わりません",

        # 隣の駅との比較は、事実を1つずつ並べるのではなく、
        # 「何がどう違うか」「そのぶん何を手放すか」が分かる形で書く（ルール49）。
        "neighbourDistanceClose": "{station}から歩いて行ける距離にあります。",
        "neighbourDistanceFar": "{station}から直線でおよそ{km}km離れています。",
        "nbLinesExtra": "{nb}では、{station}で使えない{lines}も使えます。",
        "nbLinesExtraMany": "{nb}では、{station}で使えない路線が{count}本あります。",
        "nbLinesFewerMany": "{nb}で使えるのは{count}路線で、鉄道の便は{station}が上回ります。",
        "nbLinesBetter": "使える路線が多いぶん、鉄道の便は{nb}が上回ります。",
        "nbLinesFewer": "{nb}で使えるのは{lines}だけで、鉄道の便は{station}が上回ります。",
        "nbLinesSwap": "{nb}が乗り入れるのは{lines}で、{station}とは路線が違います。",
        "nbLinesSame": "使える路線は{station}と同じです。",
        "nbCommuteFaster": "たとえば{hub}へは、{nb}のほうが{minutes}{minuteWord}早く着きます。",
        "nbCommuteSlower": "たとえば{hub}へは、{nb}のほうが{minutes}{minuteWord}多くかかります。",
        "nbCommuteSame": "主なオフィス街までの所要時間は、ほとんど変わりません。",
        "nbRentHigherBut": "ただしワンルームの家賃相場は、{nb}のほうが{amount}{unit}ほど高めです。",
        "nbRentHigher": "ワンルームの家賃相場も、{nb}のほうが{amount}{unit}ほど高めです。",
        "nbRentHigherPlain": "ワンルームの家賃相場は、{nb}のほうが{amount}{unit}ほど高めです。",
        "nbRentLowerPlain": "ワンルームの家賃相場は、{nb}のほうが{amount}{unit}ほど安めです。",
        "nbRentLowerBut": "ただしワンルームの家賃相場は、{nb}のほうが{amount}{unit}ほど安めです。",
        "nbRentLower": "ワンルームの家賃相場も、{nb}のほうが{amount}{unit}ほど安めです。",
        "nbRentSame": "ワンルームの家賃相場は、ほとんど変わりません。",
        "nbAxisBut": "ただし{axis}は、{station}のほうが上です。",
        "nbAxisButNb": "ただし{axis}は、{nb}のほうが上です。",
        "nbAxisPlain": "{axis}は、{station}のほうが上です。",
        "nbAxisPlainNb": "{axis}は、{nb}のほうが上です。",
        "nbRestSimilar": "家賃の相場や大雨のときの浸水の想定など、"
                         "ほかの条件に大きな違いはありません。",

        "goodOtemachi": "大手町・丸の内方面へ通勤する人",
        "goodShinjuku": "新宿方面へ通勤する人",
        "goodManyLines": "路線が止まったときに別の経路を使いたい人",
        "goodFlat": "自転車やベビーカーで動くことが多い人",
        "goodShopping": "徒歩圏で買い物を済ませたい人",
        "goodNature": "公園が近いことを重視する人",
        "goodDry": "大雨のときの浸水の想定が小さい土地を選びたい人",
        "goodCheap": "家賃を抑えたい単身者",
        "goodUnknown": "データからは、際立った向き先を読み取れていません",
        "badFlood": "大雨のときの浸水の想定を避けたい人",
        "badHilly": "坂の上り下りを避けたい人",
        "badOneLine": "運転見合わせのときに別の経路が欲しい人",
        "badShopping": "徒歩圏で買い物を済ませたい人",
        "badFood": "外食できる店の多さを求める人",
        "badExpensive": "家賃を抑えたい人",
        "badUnknown": "この駅ならではの弱点は、データからは読み取れていません",
    },

    "en": {
        "money": yen,
        "moneySmall": yen,
        "moneyUnit": "",
        "sentenceGap": " ",
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
        "stationNameWithLine": "{name} ({line})",

        "commuteItem": "{minutes} {minuteWord} to {hub}",
        "reachItem": "{hub} in {minutes} {minuteWord}",
        "tagline": "{reach}. Served by {lineCount} {lineWord}. {rent}",
        "taglineRent": "A one-room flat rents for roughly {low} to {high}.",

        "summaryWhere": "The station is in {ward}, served by {lines}. ",
        "summaryWhereMany": "The station is in {ward}, where {operators} run {count} {lineWord} between them. ",
        "summaryCommute": "Journey times to the main business districts are {items}. ",
        "summaryTerrain": "The station stands {elevation} m above sea level, and the ground "
                          "within 800 m varies in height by {spread} m. The land around the "
                          "station {slope}.",

        "terrainLow": "The station sits lower than the ground around it",
        "terrainHigh": "The station sits on the higher side of the ground around it",
        "terrainNote": "{where}, at {elevation} m above sea level. Within 800 m the ground "
                       "ranges from {min} m to {max} m, a difference of {spread} m.",

        "floodAtStation": "On the flood hazard map for the largest rainfall the government "
                          "models, the station itself falls inside the projected inundation "
                          "area, to a projected depth of {depth}. ",
        "floodNearOnly": "On the flood hazard map for the largest rainfall the government "
                         "models, the station itself falls outside the projected inundation "
                         "area. ",
        "floodNone": "On the flood hazard map for the largest rainfall the government models, "
                     "neither the station nor any of the nine points within 400 m of it falls "
                     "inside the projected inundation area. ",
        "floodAroundAll": "All nine points within 400 m of the station fall inside the area "
                          "too, and the deepest projection among them is {deepest}. ",
        "floodAroundSome": "Of the nine points within 400 m of the station, {count} also fall "
                           "inside the area, and the deepest projection is {deepest}. ",
        "floodAroundOnly": "Even so, {count} of the nine points within 400 m fall inside the "
                           "area, and the deepest projection there is {deepest}. ",
        "hightide": "For storm surge, {count} of the nine points also fall inside the "
                    "projected area. ",
        "hazardTrailer5": "On the whole, the flood projection here is among the smallest "
                          "in the 23 wards.",
        "hazardTrailer4": "On the whole, the flood projection here is on the small side "
                          "for the 23 wards.",
        "hazardTrailer3": "On the whole, the flood projection here is about average "
                          "for the 23 wards.",
        "hazardTrailer2": "On the whole, the flood projection here is on the large side "
                          "for the 23 wards.",
        "hazardTrailer1": "On the whole, the flood projection here is among the largest "
                          "in the 23 wards.",

        "medicalCounts": "Within an 800 m walk of the station there are {items}. ",
        "medicalEnough": "Day-to-day care is available close to the station. ",
        "medicalClinics": "{count} {clinicWord}",
        "medicalPharmacies": "{count} {pharmacyWord}",
        "medicalNone": "Within an 800 m walk of the station, OpenStreetMap records neither a "
                       "clinic nor a pharmacy. ",
        "medicalHospitalNearest": "The nearest hospital is {name}, "
                                  "about {minutes} minutes' walk from the station. ",
        "medicalHospitalSecond": "The next nearest is {name}, about {minutes} minutes' walk. ",
        "medicalNoHospital": "No facility recorded as a hospital lies within 2.5 km of the "
                             "station. ",
        "medicalTrailer": "\"Hospital\" here means a facility OpenStreetMap records as one. "
                          "OpenStreetMap does not record whether a facility admits inpatients "
                          "or which departments it runs, so check each one on its own website. "
                          "For which clinics open at night and at weekends, ask the emergency "
                          "advice line of the ward you live in.",

        "congestionOnPeak": "{line} runs at {rate}% of capacity in the morning peak. "
                            "The busiest stretch of the line is {section}, "
                            "which includes this station. ",
        "congestionOffPeak": "{line} runs at {rate}% of capacity in the morning peak. "
                             "The busiest stretch is {section}, which this station is not on. ",
        "congestionOffPeak2": "{line} runs at {rate}%. Its busiest stretch is {section}, "
                              "which this station is likewise not on. ",
        "congestionUnknown": "{lines} is not covered by the ministry's congestion survey. ",
        "congestionAllUnknown": "The ministry's congestion survey does not publish figures "
                                "for {lines}. It covers the major commuter stretches, "
                                "and this line is not among them. ",
        "congestionScale4": "At 200%, the ministry's scale describes bodies pressed together "
                            "and passengers near the doors unable to move. ",
        "congestionScale3": "At 180%, the ministry's scale describes shoulders touching "
                            "and difficulty turning around. ",
        "congestionScale2": "At 150%, the ministry's scale describes shoulders not quite "
                            "touching, with crowding near the doors. ",
        "congestionScale1": "At 100%, the ministry's scale describes every passenger "
                            "either seated or able to hold a strap or pillar. ",
        "congestionTrailer": "The figures describe each line's busiest stretch, "
                             "so the stretch you ride may be easier. ",
        "leadCongestion5": "Among the 23 wards' stations, the lines here are very lightly "
                           "loaded in the morning. ",
        "leadCongestion4": "Among the 23 wards' stations, the lines here are lightly loaded "
                           "in the morning. ",
        "leadCongestion3": "Morning loading on the lines here is about average for the "
                           "23 wards' stations. ",
        "leadCongestion2": "Among the 23 wards' stations, the lines here are heavily loaded "
                           "in the morning. ",
        "leadCongestion1": "Among the 23 wards' stations, the lines here are some of the most "
                           "heavily loaded in the morning. ",
        "stationLines": "{count} {lineWord} serve the station: {lines}. ",
        "stationLinesCount": "{count} {lineWord} serve the station. ",
        "stationLinesHead": "{lines} run through it. ",
        "stationLinesMore": "{lines} also call here. ",
        "stationLinesMore2": "{lines} are available too. ",
        "stationLinesMore3": "{lines} stop here as well. ",
        "stationSingleLine": "Only one line runs here, so when it stops you will be walking to "
                             "a station on another line. ",
        "stationOperatorItem": "{operator} runs {count} {lineWord}",
        "stationMixedOperators": "The lines are split between operators ({breakdown}), so when "
                                 "one line stops you can change to a line run by a different "
                                 "company. ",
        "stationSameOperator": "All {count} {lineWord} are run by {operator}, so a fault "
                               "affecting that company can stop them together. ",
        "stationSameOperatorTwo": "Both lines are run by {operator}, so a fault affecting that company can stop them together. ",

        "rentLabels": {"oneRoom": "One room", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label} {low} to {high}",
        "rentNoteHead": "Around this station, {items}. ",
        "rentNoteMore": "{items}. ",
        "rentNoteTrailer": "These are the per-station averages published by LIFULL HOME'S, "
                           "Yahoo! Real Estate and at home, averaged together and rounded down "
                           "to the nearest \u00a510,000 (our own survey). All three are asking "
                           "rents, so what tenants finally agree can be lower. Within the same "
                           "station area the figure moves a great deal with the age of the "
                           "building, the walk from the station, and whether the flat faces a "
                           "main road.",
        "rentDrivers": ["Age and construction of the building",
                        "Walking distance from the station",
                        "Whether it faces a main road or the railway",
                        "Whether it sits at the top or the bottom of a slope",
                        "Floor area for the layout"],
        "rentReason": "A one-room flat here goes for {low} to {high}. ",
        "rentLevel5": "Set against how long it takes to reach the central business districts, "
                      "that is among the lowest in the 23 wards. ",
        "rentLevel4": "Set against how long it takes to reach the central business districts, "
                      "that is on the low side. ",
        "rentLevel3": "Set against how long it takes to reach the central business districts, "
                      "that is about average for the 23 wards. ",
        "rentLevel2": "Set against how long it takes to reach the central business districts, "
                      "that is on the high side. ",
        "rentLevel1": "Set against how long it takes to reach the central business districts, "
                      "that is among the highest in the 23 wards. ",
        "rentDown": "What holds the figure down: {items}. ",
        "rentUp": "What pushes the figure up: {items}. ",
        "rentBoth": "{up} pushes the figure up. On the other side, {down} holds it down. ",
        "rentAbsoluteLow": "In plain yen, though, it is on the low side for the 23 wards. ",
        "rentAbsoluteHigh": "In plain yen, though, it is on the high side for the 23 wards. ",
        "rentFactorFlood": "a large projected flood depth",
        "rentFactorOneLine": "only one line, the {line}, serving the station",
        "rentFactorHilly": "a climb from the station to much of the housing",
        "rentFactorFewShops": "little daily shopping within walking distance",
        "rentFactorNoisy": "many bars by the station and voices outside late at night",
        "rentFactorManyLines": "{count} lines and a wide choice of connections",
        "rentFactorDry": "a small projected flood depth",
        "rentFactorFamily": "schools and parks within walking distance",
        "rentFactorQuiet": "quiet surroundings",
        "rentFactorFood": "plenty of places to eat out",
        "rentWideSpread": "For {layouts}, though, the sources differ by ¥30,000 or more. They "
                          "count different sets of properties, so read those figures as a "
                          "range rather than a point.",
        "rentWideSep": ", ",

        "leadTerrainFlat": "The ground around the station is almost level, so you can choose where to live without thinking about slopes.",
        "leadTerrainSome": "There are gentle slopes around the station, and which block you live on changes how much effort getting about takes.",
        "leadTerrainHilly": "The ground around the station rises and falls sharply, and living above or below the slope changes how much effort getting about takes.",
        "leadGroceriesMany": "There are {count} supermarkets within walking distance, and the nearest is {minutes} minutes on foot.",
        "leadGroceriesFew": "There are {count} supermarkets within walking distance, and the nearest is {minutes} minutes on foot.",
        "leadGroceriesNone": "OpenStreetMap records no supermarket within walking distance of the station.",
        "leadHazardAtStation": "The station itself sits inside the area projected to flood in the heaviest rainfall the government models.",
        "leadHazardNear": "The station itself is outside the projected flood area, but blocks nearby are inside it.",
        "leadHazardNone": "Neither the station nor the ground around it falls inside the projected flood area.",
        "leadStationMany": "{count} lines serve the station, and the choice of connections is wider than at most stations in the 23 wards.",
        "leadStationMid": "{count} lines serve the station. The choice of connections is about average for the 23 wards.",
        "leadStationOne": "Only the {line} serves this station, so when it stops you walk to another station.",
        "leadRent5": "Set against how long the commute takes, rents here are among the lowest in the 23 wards.",
        "leadRent4": "Set against how long the commute takes, rents here are on the low side.",
        "leadRent3": "The balance between commuting time and rent is about average for the 23 wards.",
        "leadRent2": "Set against how long the commute takes, rents here are on the high side.",
        "leadRent1": "Set against how long the commute takes, rents here are among the highest in the 23 wards.",
        "leadMedical5": "The number of clinics and pharmacies within walking distance is among the highest in the 23 wards.",
        "leadMedical4": "The number of clinics and pharmacies within walking distance is on the high side for the 23 wards.",
        "leadMedical3": "The number of clinics and pharmacies within walking distance is about average for the 23 wards.",
        "leadMedical2": "The number of clinics and pharmacies within walking distance is on the low side for the 23 wards.",
        "leadMedical1": "The number of clinics and pharmacies within walking distance is low for the 23 wards.",

        "roadSideOneway": "{n} lanes each way",
        "roadSideBoth": "{n} lanes each way",
        "roadSideUnknown": "a main road",
        "roadWhereAtStation": "right beside the station",
        "roadWhereNear": "just outside the station",
        "roadWhereAway": "a short walk from the station",
        "noiseRoadVeryNear": "{name} ({side}) runs {where}. Traffic on it never stops, "
                             "so for a flat close to the station, check whether it faces the road",
        "noiseRoadMotorway": "The {name} viaduct runs {where}. It is an expressway, "
                             "so traffic is audible day and night",
        "noiseRoadBig": "{name} ({side}) runs {where}. Traffic on it never stops",
        "noiseRoadMid": "{name} ({side}) runs {where}. In a flat facing it, "
                        "the cars are audible morning and evening",
        "noiseRoadAtStation": "{name} ({side}) runs {where}, so for a flat close to "
                              "the station, check whether it faces the road",
        "noiseRoadFar": "The nearest big road, {name}, is far enough that "
                        "little traffic noise reaches the station area",
        "leadNoiseLoud": "At this station, check the traffic noise before the noise people make.",
        "leadNoiseMid": "Whether a flat faces the road changes what you hear indoors.",
        "leadNoiseQuiet": "The big roads are far enough that traffic noise is unlikely to bother you.",

        "cmpRentCheaper": "rents are lower at {station}",
        "cmpRentSame": "rents are about the same",
        "cmpAxisWin": "{station} is ahead on {axes}",
        "cmpButJoin": "{a}, but {b}.",
        "cmpAndJoin": "{a}, and {b}.",
        "cmpOnly": "{a}.",
        "cmpSep": " and ",
        "cmpAxisDisaster": "how little of the area is in the flood projection",
        "cmpAxisTransit": "the number of lines",
        "cmpAxisCommute": "how close the centre is",
        "cmpAxisHealthcare": "the number of medical facilities",
        "cmpAxisShopping": "how easy the shopping is",
        "cmpAxisQuiet": "quiet",
        "cmpAxisSafety": "safety",
        "cmpAxisFamily": "what it offers families",
        "cmpAxisFood": "the number of places to eat out",
        "cmpNothing": "rent, commuting and the flood projection are all much the same",

        "neighbourDistanceClose": "Close enough to walk to from {station}. ",
        "neighbourDistanceFar": "About {km} km from {station} in a straight line. ",
        "nbLinesExtra": "{nb} also has the {lines}, which {station} does not. ",
        "nbLinesExtraMany": "{nb} has {count} lines that {station} does not. ",
        "nbLinesFewerMany": "{nb} has {count} lines, so {station} is the better connected. ",
        "nbLinesBetter": "With more lines, {nb} is the better connected of the two. ",
        "nbLinesFewer": "{nb} has only the {lines}, so {station} is the better connected. ",
        "nbLinesSwap": "{nb} has the {lines}, a different set from {station}. ",
        "nbLinesSame": "It is served by the same lines as {station}. ",
        "nbCommuteFaster": "To {hub}, for instance, {nb} is {minutes} {minuteWord} quicker. ",
        "nbCommuteSlower": "To {hub}, for instance, {nb} takes {minutes} {minuteWord} longer. ",
        "nbCommuteSame": "Journey times to the main business districts are much the same. ",
        "nbRentHigherBut": "A one-room flat, though, costs about {amount} more at {nb}. ",
        "nbRentHigher": "A one-room flat also costs about {amount} more at {nb}. ",
        "nbRentHigherPlain": "A one-room flat costs about {amount} more at {nb}. ",
        "nbRentLowerPlain": "A one-room flat costs about {amount} less at {nb}. ",
        "nbRentLowerBut": "A one-room flat, though, costs about {amount} less at {nb}. ",
        "nbRentLower": "A one-room flat also costs about {amount} less at {nb}. ",
        "nbRentSame": "One-room rents are much the same. ",
        "nbAxisBut": "On {axis}, though, {station} comes out ahead. ",
        "nbAxisButNb": "On {axis}, though, {nb} comes out ahead. ",
        "nbAxisPlain": "On {axis}, {station} comes out ahead. ",
        "nbAxisPlainNb": "On {axis}, {nb} comes out ahead. ",
        "nbRestSimilar": "Rents, flood projections and the rest differ little. ",
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
        "moneySmall": lambda a: f"{round(a / 1000)}千",
        "moneyUnit": "日元",
        "sentenceGap": "",
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
        "stationNameWithLine": "{name}（{line}）",

        "commuteItem": "到{hub}{minutes}{minuteWord}",
        "reachItem": "到{hub}{minutes}{minuteWord}",
        "tagline": "{reach}。有{lineCount}{lineWord}经过。{rent}",
        "taglineRent": "一室户的租金大致为{low}至{high}{unit}。",

        "summaryWhere": "车站位于{ward}，有{lines}经过。",
        "summaryWhereMany": "车站位于{ward}，{operators}共有{count}{lineWord}经过。",
        "summaryCommute": "到主要商务区的所需时间为：{items}。",
        "summaryTerrain": "车站海拔{elevation}米，周边800米范围内的高低差为{spread}米。"
                          "车站周围的地形{slope}。",

        "terrainLow": "车站所在的位置低于周围",
        "terrainHigh": "车站所在的位置在周围属于较高的一侧",
        "terrainNote": "{where}，海拔{elevation}米。周边800米范围内，"
                       "海拔从{min}米到{max}米，相差{spread}米。",

        "floodAtStation": "在按可能出现的最大降雨量推算的洪水浸水想定区域中，"
                          "车站所在的地点被划入区域，推算的水深为{depth}。",
        "floodNearOnly": "在按可能出现的最大降雨量推算的洪水浸水想定区域中，"
                         "车站所在的地点在区域之外。",
        "floodNone": "在按可能出现的最大降雨量推算的洪水浸水想定区域中，"
                     "车站所在的地点，以及车站400米以内的九个点，都在区域之外。",
        "floodAroundAll": "车站400米以内查看的九个点也全部被划入区域，"
                          "其中推算最深的水深为{deepest}。",
        "floodAroundSome": "车站400米以内查看的九个点中，也有{count}个点被划入区域，"
                           "其中推算最深的水深为{deepest}。",
        "floodAroundOnly": "不过车站400米以内查看的九个点中，有{count}个点被划入区域，"
                           "其中推算最深的水深为{deepest}。",
        "hightide": "风暴潮方面，九个点中也有{count}个点被划入想定区域。",
        "hazardTrailer5": "总的来说，大雨时的浸水推算在23区的车站中非常小。",
        "hazardTrailer4": "总的来说，大雨时的浸水推算在23区的车站中偏小。",
        "hazardTrailer3": "总的来说，大雨时的浸水推算与23区车站的平均水平相当。",
        "hazardTrailer2": "总的来说，大雨时的浸水推算在23区的车站中偏大。",
        "hazardTrailer1": "总的来说，大雨时的浸水推算在23区的车站中非常大。",

        "medicalCounts": "从车站步行800米以内，有{items}。",
        "medicalEnough": "日常看病，在车站附近就能选。",
        "medicalClinics": "诊所{count}{clinicWord}",
        "medicalPharmacies": "药店{count}{pharmacyWord}",
        "medicalNone": "从车站步行800米以内，OpenStreetMap 上没有登记的诊所和药店。",
        "medicalHospitalNearest": "离车站最近的医院是{name}，步行约{minutes}分钟。",
        "medicalHospitalSecond": "其次是{name}，步行约{minutes}分钟。",
        "medicalNoHospital": "车站2.5公里以内，没有登记为医院的设施。",
        "medicalTrailer": "这里说的医院，是 OpenStreetMap 上登记为医院的设施。"
                          "能否住院、设有哪些科室，OpenStreetMap 上没有记载，"
                          "请到各设施的网站上确认。夜间和休息日能就诊的医疗机构，"
                          "可以向所住区的急救咨询窗口查询。",

        "congestionOnPeak": "{line}早高峰的拥挤率为{rate}%。全线最拥挤的区间是{section}，本站在该区间内。",
        "congestionOffPeak": "{line}早高峰的拥挤率为{rate}%。最拥挤的区间是{section}，本站不在该区间内。",
        "congestionOffPeak2": "{line}为{rate}%。该线最拥挤的区间是{section}，本站同样不在其中。",
        "congestionUnknown": "{lines}的拥挤率未在国土交通省的调查中公布。",
        "congestionAllUnknown": "{lines}的早高峰拥挤率未在国土交通省的调查中公布。"
                                "该调查以主要区间为对象，不包含这条线路。",
        "congestionScale4": "按国土交通省的标准，200%指身体相互接触、压迫感很强，车门附近的人无法移动。",
        "congestionScale3": "按国土交通省的标准，180%指肩膀相互接触、略有压迫感，转身困难。",
        "congestionScale2": "按国土交通省的标准，150%指肩膀不会相互接触，车门附近人较多。",
        "congestionScale1": "按国土交通省的标准，100%指所有人都能就座或抓住吊环、立柱。",
        "congestionTrailer": "这是全线最拥挤区间的数值，本站乘车的区间未必相同。",
        "leadCongestion5": "可使用线路的早高峰拥挤率，在23区的车站中非常低。",
        "leadCongestion4": "可使用线路的早高峰拥挤率，在23区的车站中偏低。",
        "leadCongestion3": "可使用线路的早高峰拥挤率，与23区车站的平均水平相当。",
        "leadCongestion2": "可使用线路的早高峰拥挤率，在23区的车站中偏高。",
        "leadCongestion1": "可使用线路的早高峰拥挤率，在23区的车站中非常高。",
        "stationLines": "可以使用{lines}这{count}{lineWord}。",
        "stationLinesCount": "可以使用的线路共{count}{lineWord}。",
        "stationLinesHead": "{lines}经过。",
        "stationLinesMore": "此外{lines}也在此停靠。",
        "stationLinesMore2": "还可以使用{lines}。",
        "stationLinesMore3": "另有{lines}停靠。",
        "stationSingleLine": "只有一条线路经过，这条线路停运时，"
                             "就要步行到有其他线路经过的车站。",
        "stationOperatorItem": "{operator}{count}{lineWord}",
        "stationMixedOperators": "运营方分为{breakdown}，"
                                 "所以一条线路停运时，可以换乘另一家公司的线路。",
        "stationSameOperator": "{count}{lineWord}都由{operator}运营，"
                               "遇到波及整个运营公司的故障时，可能会一起停运。",
        "stationSameOperatorTwo": "2条线路都由{operator}运营，遇到波及整个运营公司的故障时，可能会一起停运。",

        "rentLabels": {"oneRoom": "一室户", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label}{low}至{high}{unit}",
        "rentNoteHead": "车站周边的租金行情，{items}。",
        "rentNoteMore": "{items}。",
        "rentNoteTrailer": "以上取 LIFULL HOME'S、Yahoo!不动产、at home 三家公布的"
                           "分车站行情的平均值，并向下取整到1万日元（本公司调查）。"
                           "三者都是招租价格，实际成交的金额可能低于此。"
                           "即使是同一个车站，房龄、离车站的距离、是否临街，都会让金额差出很多。",
        "rentDrivers": ["房龄和建筑结构", "离车站的步行距离", "是否临主干道或铁路",
                        "在坡上还是坡下", "相对于户型的实际面积"],
        "rentReason": "一室户的行情为{low}至{high}{unit}。",
        "rentLevel5": "按到主要商务区所需的时间来看，在23区的车站中相当便宜。",
        "rentLevel4": "按到主要商务区所需的时间来看，属于偏低的水平。",
        "rentLevel3": "按到主要商务区所需的时间来看，与23区车站的平均水平相当。",
        "rentLevel2": "按到主要商务区所需的时间来看，属于偏高的水平。",
        "rentLevel1": "按到主要商务区所需的时间来看，在23区的车站中相当高。",
        "rentDown": "压低行情的因素有：{items}。",
        "rentUp": "推高行情的因素有：{items}。",
        "rentBoth": "{up}推高行情，而{down}则压低行情。",
        "rentAbsoluteLow": "不过就金额本身而言，在23区的车站中偏低。",
        "rentAbsoluteHigh": "不过就金额本身而言，在23区的车站中偏高。",
        "rentFactorFlood": "大雨时推算的浸水深度较大",
        "rentFactorOneLine": "可用的线路只有{line}一条",
        "rentFactorHilly": "从车站到住宅区要上坡的街区较多",
        "rentFactorFewShops": "步行范围内不易买齐日用品",
        "rentFactorNoisy": "车站附近酒馆多，夜里人声不断",
        "rentFactorManyLines": "有{count}条线路可用，换乘选择多",
        "rentFactorDry": "大雨时推算的浸水深度较小",
        "rentFactorFamily": "学校和公园都在步行范围内",
        "rentFactorQuiet": "车站周边安静",
        "rentFactorFood": "可以外食的店很多",
        "rentWideSpread": "不过{layouts}的各家数值相差3万日元以上，"
                          "统计的对象不同，看的时候应留出幅度。",
        "rentWideSep": "、",

        "leadTerrainFlat": "车站周边基本平坦，选住处时不必考虑坡道。",
        "leadTerrainSome": "车站周边有缓坡，住在哪个街区会改变每天出行的费力程度。",
        "leadTerrainHilly": "车站周边起伏较大，住在坡上还是坡下，会改变每天出行的费力程度。",
        "leadGroceriesMany": "步行可达的超市有{count}家，最近的一家步行{minutes}分钟。",
        "leadGroceriesFew": "步行可达的超市有{count}家，最近的一家步行{minutes}分钟。",
        "leadGroceriesNone": "OpenStreetMap 上查不到车站步行范围内的超市。",
        "leadHazardAtStation": "车站所在的地点，被划入大雨时的浸水想定区域。",
        "leadHazardNear": "车站所在的地点在区域之外，但周边有被划入浸水想定区域的街区。",
        "leadHazardNone": "车站所在的地点及其周边，都在大雨时的浸水想定区域之外。",
        "leadStationMany": "有{count}条线路可用，换乘的选择在23区的车站中偏多。",
        "leadStationMid": "有{count}条线路可用。换乘的选择与23区车站的平均水平相当。",
        "leadStationOne": "可用的线路只有{line}一条，这条线停运时就要走到别的车站。",
        "leadRent5": "相对于通勤所需的时间，这里的租金行情在23区的车站中相当低。",
        "leadRent4": "相对于通勤所需的时间，这里的租金行情偏低。",
        "leadRent3": "通勤时间与租金行情的关系，与23区车站的平均水平相当。",
        "leadRent2": "相对于通勤所需的时间，这里的租金行情偏高。",
        "leadRent1": "相对于通勤所需的时间，这里的租金行情在23区的车站中相当高。",
        "leadMedical5": "步行可达的诊所和药店数量，在23区的车站中非常多。",
        "leadMedical4": "步行可达的诊所和药店数量，在23区的车站中偏多。",
        "leadMedical3": "步行可达的诊所和药店数量，与23区车站的平均水平相当。",
        "leadMedical2": "步行可达的诊所和药店数量，在23区的车站中偏少。",
        "leadMedical1": "步行可达的诊所和药店数量，在23区的车站中较少。",

        "roadSideOneway": "单向{n}车道",
        "roadSideBoth": "单向{n}车道",
        "roadSideUnknown": "大马路",
        "roadWhereAtStation": "就在车站旁边",
        "roadWhereNear": "在车站附近",
        "roadWhereAway": "离车站走一小段",
        "noiseRoadVeryNear": "{name}（{side}的大马路）{where}。一整天车流不断，"
                             "看车站附近的房子时，要确认是否临街",
        "noiseRoadMotorway": "{name}的高架{where}经过。是高速公路，车声白天黑夜都不停",
        "noiseRoadBig": "{name}（{side}的大马路）{where}。一整天车流不断",
        "noiseRoadMid": "{name}（{side}）{where}。临街的房间，早晚车声会进到屋里",
        "noiseRoadAtStation": "{name}（{side}）{where}。看车站附近的房子时，要确认是否临街",
        "noiseRoadFar": "最近的大马路是{name}，离车站有一段距离，车声不太传到车站周边",
        "leadNoiseLoud": "这个车站要先确认车声，而不是人声。",
        "leadNoiseMid": "是否临街，屋里听到的车声会明显不同。",
        "leadNoiseQuiet": "离大马路有一段距离，车声不太会造成困扰。",

        "cmpRentCheaper": "租金行情是{station}更便宜",
        "cmpRentSame": "租金行情差不多",
        "cmpAxisWin": "{axes}是{station}更强",
        "cmpButJoin": "{a}。不过{b}。",
        "cmpAndJoin": "{a}。{b}。",
        "cmpOnly": "{a}。",
        "cmpSep": "和",
        "cmpAxisDisaster": "浸水预估的范围小",
        "cmpAxisTransit": "可用线路的数量",
        "cmpAxisCommute": "离市中心的近",
        "cmpAxisHealthcare": "医疗机构的多",
        "cmpAxisShopping": "买东西的方便",
        "cmpAxisQuiet": "安静",
        "cmpAxisSafety": "治安",
        "cmpAxisFamily": "与孩子同住的条件",
        "cmpAxisFood": "可以外食的店的数量",
        "cmpNothing": "租金、通勤和灾害预估都没有大的差别",

        "neighbourDistanceClose": "从{station}走得到的距离。",
        "neighbourDistanceFar": "距{station}直线约{km}公里。",
        "nbLinesExtra": "{nb}还能用{station}没有的{lines}。",
        "nbLinesExtraMany": "{nb}有{count}条{station}没有的线路。",
        "nbLinesFewerMany": "{nb}可用{count}条线路，铁路出行的方便程度是{station}更强。",
        "nbLinesBetter": "可用的线路更多，铁路出行的方便程度是{nb}更强。",
        "nbLinesFewer": "{nb}只能用{lines}，铁路出行的方便程度是{station}更强。",
        "nbLinesSwap": "{nb}可用的是{lines}，与{station}的线路不同。",
        "nbLinesSame": "可用的线路与{station}相同。",
        "nbCommuteFaster": "例如到{hub}，{nb}要快{minutes}{minuteWord}。",
        "nbCommuteSlower": "例如到{hub}，{nb}要多花{minutes}{minuteWord}。",
        "nbCommuteSame": "到主要商务区的时间几乎没有差别。",
        "nbRentHigherBut": "不过一室户的租金行情，{nb}要高出约{amount}{unit}。",
        "nbRentHigher": "一室户的租金行情也是{nb}高出约{amount}{unit}。",
        "nbRentHigherPlain": "一室户的租金行情，{nb}高出约{amount}{unit}。",
        "nbRentLowerPlain": "一室户的租金行情，{nb}低约{amount}{unit}。",
        "nbRentLowerBut": "不过一室户的租金行情，{nb}要低约{amount}{unit}。",
        "nbRentLower": "一室户的租金行情也是{nb}低约{amount}{unit}。",
        "nbRentSame": "一室户的租金行情几乎相同。",
        "nbAxisBut": "不过{axis}是{station}更强。",
        "nbAxisButNb": "不过{axis}是{nb}更强。",
        "nbAxisPlain": "{axis}是{station}更强。",
        "nbAxisPlainNb": "{axis}是{nb}更强。",
        "nbRestSimilar": "租金行情、浸水推算等其他条件没有太大差别。",
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
        "money": man_ko,
        "moneySmall": lambda a: f"{round(a / 1000)}천",
        "moneyUnit": "엔",
        "sentenceGap": " ",
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
        "stationNameWithLine": "{name}（{line}）",

        "commuteItem": "{hub}까지 {minutes}{minuteWord}",
        "reachItem": "{hub}까지 {minutes}{minuteWord}",
        "tagline": "{reach}. {lineCount}{lineWord}이 지난다. {rent}",
        "taglineRent": "원룸 임대료는 대략 {low}~{high}{unit}이다.",

        "summaryWhere": "역은 {ward}에 있으며, {lines} 노선이 지난다. ",
        "summaryWhereMany": "역은 {ward}에 있으며, {operators}의 {count}{lineWord}이 지난다. ",
        "summaryCommute": "주요 업무지구까지 걸리는 시간은 {items}이다. ",
        "summaryTerrain": "역의 표고는 {elevation}m이고, 주변 800m 안의 표고 차이는 "
                          "{spread}m이다. 역 주변의 땅은 {slope}. ",

        "terrainLow": "역은 주변보다 낮은 곳에 있고",
        "terrainHigh": "역은 주변 중에서는 높은 쪽에 있고",
        "terrainNote": "{where}, 표고는 {elevation}m이다. 주변 800m 안의 표고는 {min}m부터 "
                       "{max}m까지 나뉘며, 그 차이는 {spread}m이다.",

        "floodAtStation": "상정할 수 있는 최대 규모의 강우를 전제로 한 홍수 침수 상정 구역에서, "
                          "역이 있는 지점이 구역에 들어가며 상정되는 깊이는 {depth}이다. ",
        "floodNearOnly": "상정할 수 있는 최대 규모의 강우를 전제로 한 홍수 침수 상정 구역에서, "
                         "역이 있는 지점은 구역 밖에 있다. ",
        "floodNone": "상정할 수 있는 최대 규모의 강우를 전제로 한 홍수 침수 상정 구역에서, "
                     "역이 있는 지점도, 역에서 400m 안의 아홉 지점도 모두 구역 밖에 있다. ",
        "floodAroundAll": "역에서 400m 안에서 살펴본 아홉 지점도 모두 구역에 들어가며, "
                          "그중 가장 깊게 상정된 깊이는 {deepest}이다. ",
        "floodAroundSome": "역에서 400m 안에서 살펴본 아홉 지점 가운데 {count}곳도 구역에 들어가며, "
                           "그중 가장 깊게 상정된 깊이는 {deepest}이다. ",
        "floodAroundOnly": "다만 역에서 400m 안의 아홉 지점 가운데 {count}곳은 구역에 들어가며, "
                           "그중 가장 깊게 상정된 깊이는 {deepest}이다. ",
        "hightide": "폭풍해일에 대해서도 아홉 지점 가운데 {count}곳이 상정 구역에 들어간다. ",
        "hazardTrailer5": "전체적으로 큰비가 올 때의 침수 상정은 23구의 역 중에서 매우 작은 편이다. ",
        "hazardTrailer4": "전체적으로 큰비가 올 때의 침수 상정은 23구의 역 중에서 작은 편이다. ",
        "hazardTrailer3": "전체적으로 큰비가 올 때의 침수 상정은 23구 역의 평균 정도다. ",
        "hazardTrailer2": "전체적으로 큰비가 올 때의 침수 상정은 23구의 역 중에서 큰 편이다. ",
        "hazardTrailer1": "전체적으로 큰비가 올 때의 침수 상정은 23구의 역 중에서 매우 큰 편이다. ",

        "medicalCounts": "역에서 걸어서 800m 안에 {items} 있다. ",
        "medicalEnough": "일상적으로 다닐 병원은 역 근처에서 고를 수 있다. ",
        "medicalClinics": "의원이 {count}{clinicWord}",
        "medicalPharmacies": "약국이 {count}{pharmacyWord}",
        "medicalNone": "역에서 걸어서 800m 안에는 OpenStreetMap에 등록된 의원도 약국도 "
                       "보이지 않는다. ",
        "medicalHospitalNearest": "역에서 가장 가까운 병원은 {name}이며, "
                                  "걸어서 약 {minutes}분 거리에 있다. ",
        "medicalHospitalSecond": "그다음으로 가까운 곳은 {name}으로, 걸어서 약 {minutes}분 걸린다. ",
        "medicalNoHospital": "역에서 2.5km 안에는 병원으로 등록된 시설이 보이지 않는다. ",
        "medicalTrailer": "여기서 말하는 병원은 OpenStreetMap에 병원으로 등록된 시설이다. "
                          "입원할 수 있는지, 어떤 진료과가 있는지까지는 OpenStreetMap에 "
                          "적혀 있지 않으므로, 각 시설의 웹사이트에서 확인하기 바란다. "
                          "야간이나 휴일에 진료받을 수 있는 의료기관은 사는 구의 응급 상담 "
                          "창구에서 확인할 수 있다.",

        "congestionOnPeak": "{line}의 아침 혼잡률은 {rate}%이다. "
                            "노선에서 가장 혼잡한 구간은 {section}이며, 이 역이 그 구간에 들어간다. ",
        "congestionOffPeak": "{line}의 아침 혼잡률은 {rate}%이다. "
                             "가장 혼잡한 구간은 {section}이고, 이 역은 그 구간에 들어가지 않는다. ",
        "congestionOffPeak2": "{line}은 {rate}%이다. 이 노선에서 가장 혼잡한 구간은 {section}이며, "
                              "이 역도 그 구간에 들어가지 않는다. ",
        "congestionUnknown": "{lines}의 혼잡률은 국토교통성 조사에서 공표되지 않았다. ",
        "congestionAllUnknown": "{lines}의 아침 혼잡률은 국토교통성 조사에서 공표되지 않았다. "
                                "이 조사는 주요 구간을 대상으로 하며, "
                                "이 노선은 대상에 들어가지 않는다. ",
        "congestionScale4": "국토교통성 기준으로 200%는 몸이 서로 닿아 상당한 압박감이 있고, "
                            "문 근처의 사람은 움직일 수 없는 상태를 말한다. ",
        "congestionScale3": "국토교통성 기준으로 180%는 어깨가 닿아 다소 압박감이 있고, "
                            "몸의 방향을 바꾸기 어려운 상태를 말한다. ",
        "congestionScale2": "국토교통성 기준으로 150%는 어깨가 닿지 않을 정도이며, "
                            "문 근처에 사람이 많아지는 상태를 말한다. ",
        "congestionScale1": "국토교통성 기준으로 100%는 좌석에 앉거나 손잡이나 기둥을 "
                            "잡을 수 있는 상태를 말한다. ",
        "congestionTrailer": "노선에서 가장 혼잡한 구간의 값이므로, "
                             "이 역에서 타는 구간이 같은 정도라고는 할 수 없다. ",
        "leadCongestion5": "이용할 수 있는 노선의 아침 혼잡률은 23구의 역 중에서 매우 낮은 편이다. ",
        "leadCongestion4": "이용할 수 있는 노선의 아침 혼잡률은 23구의 역 중에서 낮은 편이다. ",
        "leadCongestion3": "이용할 수 있는 노선의 아침 혼잡률은 23구 역의 평균 정도이다. ",
        "leadCongestion2": "이용할 수 있는 노선의 아침 혼잡률은 23구의 역 중에서 높은 편이다. ",
        "leadCongestion1": "이용할 수 있는 노선의 아침 혼잡률은 23구의 역 중에서도 매우 높다. ",
        "stationLines": "{lines}의 {count}{lineWord}을 이용할 수 있다. ",
        "stationLinesCount": "이용할 수 있는 노선은 {count}{lineWord}이다. ",
        "stationLinesHead": "{lines}이 지난다. ",
        "stationLinesMore": "여기에 {lines}도 들어온다. ",
        "stationLinesMore2": "{lines}도 이용할 수 있다. ",
        "stationLinesMore3": "이 밖에 {lines}도 정차한다. ",
        "stationSingleLine": "지나는 노선이 하나뿐이므로, 그 노선이 멈추면 다른 노선이 "
                             "지나는 역까지 걸어가게 된다. ",
        "stationOperatorItem": "{operator} {count}{lineWord}",
        "stationMixedOperators": "운영은 {breakdown}으로 나뉘어 있어, 한 노선이 멈춰도 "
                                 "다른 운영 회사의 노선으로 갈아탈 수 있다. ",
        "stationSameOperator": "{count}{lineWord} 모두 {operator}이 운영하므로, 운영 회사 "
                               "전체에 미치는 장애가 나면 한꺼번에 멈출 수 있다. ",
        "stationSameOperatorTwo": "2개 노선 모두 {operator}이 운영하므로, 운영 회사 전체에 미치는 장애가 나면 한꺼번에 멈출 수 있다. ",

        "rentLabels": {"oneRoom": "원룸", "oneK": "1K",
                       "oneLDK": "1LDK", "twoLDK": "2LDK"},
        "rentItem": "{label} {low}~{high}{unit}",
        "rentNoteHead": "역 주변의 임대료 시세는 {items}이다. ",
        "rentNoteMore": "{items}이다. ",
        "rentNoteTrailer": "LIFULL HOME'S, Yahoo!부동산, at home이 공개하는 역별 시세를 "
                           "평균 내어 1만 엔 단위로 내림한 값이다(당사 조사). 모두 모집 임대료이므로, "
                           "실제로 계약되는 금액은 이보다 낮아질 수 있다. 같은 역이라도 건축 연수, "
                           "역에서의 거리, 큰길에 면해 있는지에 따라 크게 달라진다.",
        "rentDrivers": ["건축 연수와 구조", "역에서의 도보 거리", "간선도로나 선로에 면해 있는지",
                        "언덕 위인지 아래인지", "구조 대비 전용 면적"],
        "rentReason": "원룸 시세는 {low}~{high}{unit}이다. ",
        "rentLevel5": "도심 업무지구까지 걸리는 시간에 비하면, 23구의 역 중에서도 상당히 싼 편이다. ",
        "rentLevel4": "도심 업무지구까지 걸리는 시간에 비하면, 싼 편이다. ",
        "rentLevel3": "도심 업무지구까지 걸리는 시간에 비하면, 23구 역의 평균 정도다. ",
        "rentLevel2": "도심 업무지구까지 걸리는 시간에 비하면, 비싼 편이다. ",
        "rentLevel1": "도심 업무지구까지 걸리는 시간에 비하면, 23구의 역 중에서도 상당히 비싸다. ",
        "rentDown": "시세를 낮추는 요인으로는 {items}이 있다. ",
        "rentUp": "시세를 끌어올리는 요인으로는 {items}이 있다. ",
        "rentBoth": "{up}이 시세를 끌어올리는 한편, {down}이 시세를 낮추고 있다. ",
        "rentAbsoluteLow": "다만 금액 자체는 23구의 역 중에서 싼 편이다. ",
        "rentAbsoluteHigh": "다만 금액 자체는 23구의 역 중에서 비싼 편이다. ",
        "rentFactorFlood": "큰비가 올 때 상정되는 침수 깊이가 큰 점",
        "rentFactorOneLine": "쓸 수 있는 노선이 {line} 하나뿐인 점",
        "rentFactorHilly": "역에서 주택가로 나갈 때 언덕을 오르는 구획이 많은 점",
        "rentFactorFewShops": "걸어서 장을 보기 어려운 점",
        "rentFactorNoisy": "역 앞에 술집이 많아 밤에도 사람 소리가 이어지는 점",
        "rentFactorManyLines": "{count}개 노선을 쓸 수 있어 환승 선택지가 많은 점",
        "rentFactorDry": "큰비가 올 때 상정되는 침수 깊이가 작은 점",
        "rentFactorFamily": "학교와 공원이 걸어갈 수 있는 거리에 있는 점",
        "rentFactorQuiet": "역 주변이 조용한 점",
        "rentFactorFood": "외식할 수 있는 가게가 많은 점",
        "rentWideSpread": "다만 {layouts}에서는 출처마다 값이 3만 엔 이상 벌어져 있다. "
                          "집계 대상이 다르므로 폭을 두고 보는 편이 좋다.",
        "rentWideSep": ", ",

        "leadTerrainFlat": "역 주변은 거의 평탄해서, 언덕을 신경 쓰지 않고 살 곳을 고를 수 있다.",
        "leadTerrainSome": "역 주변에는 완만한 언덕이 있어, 어느 구획에 사는지에 따라 매일의 이동 부담이 달라진다.",
        "leadTerrainHilly": "역 주변은 높낮이 차가 커서, 언덕 위에 사는지 아래에 사는지에 따라 매일의 이동 부담이 달라진다.",
        "leadGroceriesMany": "걸어갈 수 있는 슈퍼마켓이 {count}곳 있고, 가장 가까운 곳까지는 걸어서 {minutes}분이다.",
        "leadGroceriesFew": "걸어갈 수 있는 슈퍼마켓은 {count}곳이고, 가장 가까운 곳까지는 걸어서 {minutes}분이다.",
        "leadGroceriesNone": "역에서 걸어갈 수 있는 슈퍼마켓을 OpenStreetMap에서는 확인할 수 없었다.",
        "leadHazardAtStation": "역이 있는 지점이 큰비가 올 때의 침수 예상 구역에 들어간다.",
        "leadHazardNear": "역이 있는 지점은 구역 밖이지만, 주변에는 침수가 상정된 구획이 있다.",
        "leadHazardNone": "역이 있는 지점도 그 주변도, 큰비가 올 때의 침수 예상 구역 밖에 있다.",
        "leadStationMany": "{count}개 노선을 쓸 수 있어, 환승 선택지는 23구의 역 중에서 많은 편이다.",
        "leadStationMid": "{count}개 노선을 쓸 수 있다. 환승 선택지는 23구 역의 평균 정도다.",
        "leadStationOne": "쓸 수 있는 노선은 {line} 하나뿐이라, 이 노선이 멈추면 다른 역까지 걸어가게 된다.",
        "leadRent5": "통근에 걸리는 시간에 비해, 임대료 시세는 23구의 역 중에서도 상당히 낮다.",
        "leadRent4": "통근에 걸리는 시간에 비해, 임대료 시세는 낮은 편이다.",
        "leadRent3": "통근 시간과 임대료 시세의 관계는, 23구 역의 평균 정도다.",
        "leadRent2": "통근에 걸리는 시간에 비해, 임대료 시세는 높은 편이다.",
        "leadRent1": "통근에 걸리는 시간에 비해, 임대료 시세는 23구의 역 중에서도 상당히 높다.",
        "leadMedical5": "걸어갈 수 있는 의원과 약국의 수는, 23구의 역 중에서도 매우 많다.",
        "leadMedical4": "걸어갈 수 있는 의원과 약국의 수는, 23구의 역 중에서 많은 편이다.",
        "leadMedical3": "걸어갈 수 있는 의원과 약국의 수는, 23구 역의 평균 정도다.",
        "leadMedical2": "걸어갈 수 있는 의원과 약국의 수는, 23구의 역 중에서 적은 편이다.",
        "leadMedical1": "걸어갈 수 있는 의원과 약국의 수는, 23구의 역 중에서 적다.",

        "roadSideOneway": "편도 {n}차선",
        "roadSideBoth": "편도 {n}차선",
        "roadSideUnknown": "큰길",
        "roadWhereAtStation": "역 바로 옆",
        "roadWhereNear": "역 가까이",
        "roadWhereAway": "역에서 조금 걸은 곳",
        "noiseRoadVeryNear": "{name}（{side}의 큰길）가 {where}을 지난다. 하루 종일 차가 끊이지 않으니, "
                             "역에서 가까운 집은 길에 면해 있는지 확인하고 싶다",
        "noiseRoadMotorway": "{name} 고가가 {where}을 지난다. 고속도로라 차 소리가 낮에도 밤에도 이어진다",
        "noiseRoadBig": "{name}（{side}의 큰길）가 {where}에 있다. 하루 종일 차가 끊이지 않는다",
        "noiseRoadMid": "{name}（{side}）가 {where}에 있다. 길에 면한 방에서는 아침저녁 차 소리가 들어온다",
        "noiseRoadAtStation": "{name}（{side}）가 {where}에 있다. 역에서 가까운 집을 볼 때는 "
                              "길에 면해 있는지 확인하고 싶다",
        "noiseRoadFar": "가장 가까운 큰길인 {name}는 역에서 떨어져 있어, 역 주변까지 차 소리는 잘 닿지 않는다",
        "leadNoiseLoud": "이 역은 사람 소리보다 차 소리를 먼저 확인하고 싶다.",
        "leadNoiseMid": "도로변 방인지 아닌지에 따라 방 안에서 들리는 차 소리가 확연히 달라진다.",
        "leadNoiseQuiet": "큰길에서 떨어져 있어, 차 소리는 신경 쓰이기 어렵다.",

        "cmpRentCheaper": "임대료 시세는 {station}가 더 싸다",
        "cmpRentSame": "임대료 시세는 비슷하다",
        "cmpAxisWin": "{axes}는 {station}가 앞선다",
        "cmpButJoin": "{a}. 다만 {b}.",
        "cmpAndJoin": "{a}. {b}.",
        "cmpOnly": "{a}.",
        "cmpSep": "와 ",
        "cmpAxisDisaster": "침수 예상 범위의 작음",
        "cmpAxisTransit": "쓸 수 있는 노선 수",
        "cmpAxisCommute": "도심까지의 가까움",
        "cmpAxisHealthcare": "의료기관의 많음",
        "cmpAxisShopping": "장보기의 편함",
        "cmpAxisQuiet": "조용함",
        "cmpAxisSafety": "치안",
        "cmpAxisFamily": "아이와 함께 사는 조건",
        "cmpAxisFood": "외식할 수 있는 가게의 수",
        "cmpNothing": "임대료도 통근도 재해 예상도 크게 다르지 않다",

        "neighbourDistanceClose": "{station}에서 걸어갈 수 있는 거리에 있다. ",
        "neighbourDistanceFar": "{station}에서 직선거리로 약 {km}km 떨어져 있다. ",
        "nbLinesExtra": "{nb}에서는 {station}에서 쓸 수 없는 {lines}도 쓸 수 있다. ",
        "nbLinesExtraMany": "{nb}에는 {station}에서 쓸 수 없는 노선이 {count}개 있다. ",
        "nbLinesFewerMany": "{nb}에서 쓸 수 있는 노선은 {count}개로, 철도 이용은 {station}가 앞선다. ",
        "nbLinesBetter": "쓸 수 있는 노선이 많은 만큼, 철도 이용은 {nb}가 앞선다. ",
        "nbLinesFewer": "{nb}에서 쓸 수 있는 것은 {lines}뿐이라, 철도 이용은 {station}가 앞선다. ",
        "nbLinesSwap": "{nb}에서 쓸 수 있는 것은 {lines}로, {station}와는 노선이 다르다. ",
        "nbLinesSame": "쓸 수 있는 노선은 {station}와 같다. ",
        "nbCommuteFaster": "예를 들어 {hub}까지는 {nb}가 {minutes}{minuteWord} 빠르다. ",
        "nbCommuteSlower": "예를 들어 {hub}까지는 {nb}가 {minutes}{minuteWord} 더 걸린다. ",
        "nbCommuteSame": "주요 업무지구까지 걸리는 시간은 거의 차이가 없다. ",
        "nbRentHigherBut": "다만 원룸 시세는 {nb}가 {amount}{unit} 정도 비싸다. ",
        "nbRentHigher": "원룸 시세도 {nb}가 {amount}{unit} 정도 비싸다. ",
        "nbRentHigherPlain": "원룸 시세는 {nb}가 {amount}{unit} 정도 비싸다. ",
        "nbRentLowerPlain": "원룸 시세는 {nb}가 {amount}{unit} 정도 싸다. ",
        "nbRentLowerBut": "다만 원룸 시세는 {nb}가 {amount}{unit} 정도 싸다. ",
        "nbRentLower": "원룸 시세도 {nb}가 {amount}{unit} 정도 싸다. ",
        "nbRentSame": "원룸 시세는 거의 차이가 없다. ",
        "nbAxisBut": "다만 {axis}는 {station}가 앞선다. ",
        "nbAxisButNb": "다만 {axis}는 {nb}가 앞선다. ",
        "nbAxisPlain": "{axis}는 {station}가 앞선다. ",
        "nbAxisPlainNb": "{axis}는 {nb}가 앞선다. ",
        "nbRestSimilar": "임대료 시세나 침수 상정 등 다른 조건에는 큰 차이가 없다. ",
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
