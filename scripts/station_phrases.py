#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
駅コンテンツの文型を言語ごとに持つ表。scripts/build-station-content.py が読む。

組み立ての手順は言語によらず同じで、変わるのはここにある文型だけである。
言語を1つ足すときは PHRASES にキーを1つ増やし、同じキーの文型をすべて埋める。
埋め忘れは build-station-content.py が起動時に見つける。

金額・距離・時間の書き方も言語ごとに違うので、その関数もここに置く。
日本語は「12万円」、英語は "¥120,000" と書く。
"""


def man(yen):
    """円を「12万」の形にする。1万円未満の端数は小数第1位まで見せる。"""
    v = yen / 10000
    return f"{v:.0f}万" if abs(v - round(v)) < 0.05 else f"{v:.1f}万"


def yen(amount):
    """円を "¥120,000" の形にする。"""
    return f"¥{amount:,}"


PHRASES = {
    "ja": {
        "money": man,
        "moneyUnit": "円",
        "listSep": "、",
        "hubs": {"otemachi": "大手町", "shinjuku": "新宿", "shibuya": "渋谷",
                 "tokyo": "東京", "shinagawa": "品川", "toranomon": "虎ノ門",
                 "roppongi": "六本木"},
        "slope": {"flat": "ほぼ平坦である", "some": "ゆるやかな坂がある",
                  "hilly": "起伏が大きい"},
        "operator": {"jr": "JR", "tokyo-metro": "東京メトロ", "toei": "都営",
                     "private": "私鉄"},
        "ward": lambda st: st["wardNameJa"],
        "lineName": lambda line: line["nameJa"],
        "stationName": lambda st: st["nameJa"],

        "reachItem": "{hub}へ{minutes}分",
        "tagline": "{reach}で着く。{lineCount}路線が乗り入れる。{rent}",
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
        "medicalClinics": "クリニックが{count}件",
        "medicalPharmacies": "薬局が{count}件",
        "medicalNone": "駅から歩いて800m以内には、OpenStreetMap に登録されている"
                       "クリニックも薬局も見当たらない。",
        "medicalHospitals": "病院として登録されている施設は、{items}の距離にある。",
        "medicalHospitalItem": "{name}が{distance}mほど",
        "medicalNoHospital": "駅から2.5km以内には、病院として登録されている施設が見当たらない。",
        "medicalTrailer": "入院できるかどうか、何科があるかまでは OpenStreetMap には"
                          "書かれていないので、各施設のウェブサイトで確かめてほしい。"
                          "夜間や休日にかかれる医療機関は、住む区の救急相談窓口で確認できる。",

        "stationLines": "{lines}の{count}路線が使える。",
        "stationSingleLine": "乗り入れは1路線だけなので、その路線が止まったときは、"
                             "ほかの路線が通る駅まで歩くことになる。",
        "stationOperatorItem": "{operator}が{count}路線",
        "stationMixedOperators": "運営は{breakdown}に分かれているので、"
                                 "1つの路線が止まっても、別の運営会社の路線に乗り換えられる。",
        "stationSameOperator": "{count}路線とも{operator}の路線なので、"
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
        "neighbourSlower": "大手町へは{station}より{minutes}分多くかかる。",
        "neighbourFaster": "大手町へは{station}より{minutes}分早く着く。",
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
}
