#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
書きぶりを確認してもらうためのレビュー用ページを、data/content/ja の現物から生成する。

  python3 scripts/build-review-page.py <出力先.html>

手で書き写すとリポジトリの現物とずれるため、必ずJSONから組み立てる。
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 16層すべてを書き終えた駅だけを載せる。順序は執筆した順。
STATIONS = [
    # 深川エリア
    "kiyosumi-shirakawa", "morishita", "monzen-nakacho",
    # 中央線・城西
    "koenji", "higashi-nakano", "sasazuka",
    # 文京・目黒
    "myogadani", "nakameguro", "musashi-koyama",
    # 港区
    "roppongi", "roppongi-itchome", "nogizaka",
    # 品川・大田
    "osaki", "oimachi", "nakanobu", "nishimagome",
    # 板橋
    "itabashi",
]

LABELS = {
    "faces": "朝・昼・夜・週末のようす",
    "exits": "出口で変わる街のようす",
    "terrain": "坂・高低差",
    "groceries": "日常の買い物",
    "noiseSources": "音が気になりうる場所",
    "hazards": "災害リスク",
    "stationNote": "駅の使い勝手",
    "nightWalk": "夜の帰り道",
    "rentRange": "同じ駅でも家賃に幅がある",
    "rentReason": "家賃がこの水準である理由",
    "family": "子育て",
    "medical": "医療",
    "residents": "住んでいる人の層",
    "housingStock": "物件の傾向",
    "neighbours": "隣の駅との使い分け",
    "outlook": "これからどう変わるか",
}
FACE_LABELS = {"morning": "朝", "daytime": "昼", "night": "夜", "weekend": "週末"}
SLOPE = {"flat": "ほぼ平坦", "some": "坂がある", "hilly": "起伏が大きい"}
TIER = {"discount": "安い", "standard": "標準", "premium": "高い"}
TIER_CLASS = {"discount": "pill-cheap", "standard": "pill-mid", "premium": "pill-high"}

# 指摘を受けて直した箇所。左が直す前、右が直した後。
BEFORE_AFTER = [
    ("住むと効くのは半蔵門線と大江戸線の2路線",
     "住む側にとっての強みは、半蔵門線と大江戸線を使って都心のどの方向へも乗り換えなしで通勤できること"),
    ("合う人には代えがきかない",
     "古着店とライブハウスと個人経営の飲み屋がこれだけ密集した街は東京に他になく、この環境を求める人には替えがきかない"),
    ("弱点は家賃に集約される",
     "弱点は家賃の高さと、桜の時期の週末は花見客で混雑し、買い物や外出に不便を感じること"),
    ("生活の道具としての性能が高い", "日々の暮らしやすさという点で優れている"),
    ("平日昼間は静か。住宅街の顔になる", "平日昼間は静まり、住宅街として静かに過ごせる"),
    ("東西線の朝ラッシュは都内最悪級", "東西線は朝の混雑率が高い区間として知られる"),
    ("カフェの密度は都内でも突出している", "カフェの密度は都内でもかなり高い"),
    ("夜は森下のほうが開いている", "夜遅くまで営業している飲食店は森下のほうが多い"),
    ("駅前は流れが速い", "改札を出た人が立ち止まらずに散っていく"),
    ("町会が機能している", "町会が活発に運営され、祭りにも多くの住民が参加している"),
    ("深川エリアで最も夜が長い", "深川エリアでは飲食店が最も遅くまで営業している"),
    ("ここを甘く見積もると毎日削られる", "ここを甘く見積もると、毎朝を満員電車で過ごす疲れが積み重なる"),
    ("住宅の供給が少ないことも価格に効いている",
     "青山霊園と乃木神社が周辺の土地の多くを占め、新しい住宅が建つ余地が少ないことも、家賃を押し上げている"),
    ("千代田線で大手町へ直通11分というのも効率が良い",
     "千代田線で大手町へ乗り換えなしに11分で着くので、朝の通勤で消耗しない"),
    ("始発駅なので、朝は必ず座って通勤できる",
     "始発駅なので、列車を1本見送れば朝も座って通勤できる"),
    ("甲州街道に近く、車の通りが多い", "甲州街道に近く、日中も夜も車がよく通る"),
    ("桜の時期に週末の生活が滞ること",
     "桜の時期の週末は花見客で混雑し、買い物や外出に不便を感じること"),
    ("桜の時期の週末は生活に支障が出るほど混む",
     "桜の時期の週末は花見客で目黒川沿いの歩道が埋まり、近所のスーパーへ行くだけでも時間がかかる"),
    ("静けさを求めて休日を過ごしたい人には、週末だけ落ち着かないと感じる可能性がある",
     "静かに休日を過ごしたい人は、週末だけは人混みを歩くことになり、それを負担に感じる可能性がある"),
    ("個人経営の飲食店の密度は深川で一番高い",
     "個人経営の飲食店の密度は深川エリアで一番高い"),
    ("日々の暮らしやすさという点では、城南でも指折りの駅だと思う",
     "3路線が使えて駅前で買い物が終わるので、城南エリアの中でも暮らしやすい駅だと思う"),
    ("街並みそのものに目立つ要素はない",
     "歴史のある街並みや緑の多さといった、街そのものに惹かれて選ぶ要素は少ない"),
    ("外食と夜の選択肢を求めるなら高円寺を選びたい",
     "外食できる店の数と、夜遅くまで営業している店の多さを求めるなら高円寺を選びたい"),
    ("医療の選択肢という点では23区でも恵まれている",
     "医療機関の選択肢という点では23区でも恵まれている"),
    ("相場を1つの数字で示しても実際の選択肢は見えてこない",
     "相場を1つの数字で示しても、その予算で実際に借りられる部屋は見えてこない"),
    ("商店街と駅ビルで買い物が終わるので生活に不便はない",
     "商店街と駅ビルで買い物が終わるので、生活に不便を感じる場面は少ない"),
    ("生鮮が安く、自炊するならここで買うことが多くなる",
     "生鮮品が安く、自炊するならここで買うことが多くなる"),
]


def e(t):
    return html.escape(str(t))


def load(slug):
    with open(os.path.join(ROOT, "data", "content", "ja", f"{slug}.json"), encoding="utf-8") as f:
        return json.load(f)


def block(title, inner):
    return f'<section class="layer"><h3 class="layer-title">{e(title)}</h3>{inner}</section>'


def render(d):
    parts = [
        '<article class="station" id="%s">' % e(d["slug"]),
        '<header class="station-head">',
        f'<h2 class="station-name">{e(d["name"])}</h2>',
        f'<p class="station-tagline">{e(d["tagline"])}</p>',
        f'<p class="station-summary">{e(d["summary"])}</p>',
        '</header>',
    ]

    if "faces" in d:
        cells = "".join(
            f'<div class="face"><span class="face-label">{e(FACE_LABELS[k])}</span>'
            f'<p>{e(d["faces"][k])}</p></div>'
            for k in ("morning", "daytime", "night", "weekend")
        )
        parts.append(block(LABELS["faces"], f'<div class="faces">{cells}</div>'))

    if "exits" in d:
        rows = "".join(
            f'<dl class="exit"><dt>{e(x["name"])}</dt><dd>{e(x["character"])}</dd></dl>'
            for x in d["exits"]
        )
        parts.append(block(LABELS["exits"], f'<div class="exits">{rows}</div>'))

    if "groceries" in d:
        rows = []
        for g in d["groceries"]:
            note = f'<span class="shop-note">{e(g["note"])}</span>' if g.get("note") else ""
            rows.append(
                f'<div class="shop"><span class="shop-name">{e(g["name"])}</span>'
                f'<span class="pill {TIER_CLASS[g["tier"]]}">{e(TIER[g["tier"]])}</span>'
                f'<span class="walk">徒歩 {g["walkMinutes"]}分</span>{note}</div>'
            )
        parts.append(block(LABELS["groceries"], f'<div class="shops">{"".join(rows)}</div>'))

    if "terrain" in d:
        t = d["terrain"]
        parts.append(block(
            LABELS["terrain"],
            f'<p><strong>{e(SLOPE[t["slope"]])}</strong> — {e(t["note"])}</p>'))

    if "noiseSources" in d:
        items = "".join(f"<li>{e(x)}</li>" for x in d["noiseSources"])
        parts.append(block(LABELS["noiseSources"], f'<ul class="bare">{items}</ul>'))

    for key in ("hazards", "stationNote", "nightWalk", "rentReason",
                "family", "medical", "residents", "housingStock", "outlook"):
        if key in d:
            parts.append(block(LABELS[key], f"<p>{e(d[key])}</p>"))

    if "rentRange" in d:
        r = d["rentRange"]
        parts.append(block(
            LABELS["rentRange"],
            f'<p>{e(r["note"])}</p>'
            f'<p class="drivers"><strong>差を生む要因:</strong> '
            f'{e(" ／ ".join(r["drivers"]))}</p>'))

    if "neighbours" in d:
        items = "".join(
            f'<li><span class="nb">{e(n["slug"])}</span>{e(n["note"])}</li>'
            for n in d["neighbours"])
        parts.append(block(LABELS["neighbours"], f'<ul class="bare">{items}</ul>'))

    fit = "".join(f"<li>{e(x)}</li>" for x in d["goodFor"])
    unfit = "".join(f"<li>{e(x)}</li>" for x in d["notFor"])
    parts.append(
        '<div class="fit-grid">'
        f'<section class="layer"><h3 class="layer-title">向いている人</h3>'
        f'<ul class="bare">{fit}</ul></section>'
        f'<section class="layer"><h3 class="layer-title">向かない人</h3>'
        f'<ul class="bare bad">{unfit}</ul></section></div>')

    parts.append(block(
        "東京在住者コメント",
        f'<blockquote class="quote">{e(d["residentComment"])}</blockquote>'))
    parts.append("</article>")
    return "\n".join(parts)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "review.html"
    data = [load(s) for s in STATIONS]

    nav = " ".join(
        f'<a href="#{e(d["slug"])}">{e(d["name"])}</a>' for d in data)

    ba = "".join(
        '<div class="ba-row">'
        f'<div><span class="tag tag-old">直す前</span><span class="old">{e(a)}</span></div>'
        f'<div><span class="tag tag-new">直した後</span><span>{e(b)}</span></div>'
        '</div>' for a, b in BEFORE_AFTER)

    css = open(os.path.join(ROOT, "scripts", "review-page.css"), encoding="utf-8").read()

    body = f"""<title>16層で書いた17駅</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap">
<style>{css}</style>

<div class="wrap">
  <header class="page-head">
    <p class="eyebrow">TOKYO LIVING COMPASS</p>
    <h1>16層で書き切った17駅</h1>
    <p class="lede">
      駅ページに載せる日本語を、指摘を受けて全文書き直したもの。
      比喩で意味を圧縮した表現を排除し、誰が・何を・どうして・どうなるのかを
      省略せずに書いている。ここに出ているのはリポジトリの現物であり、
      この文章がそのまま駅ページに載る。
    </p>
    <nav class="jump">{nav}</nav>
  </header>

  <section class="ba">
    <h2>指摘を受けて直した書きぶり</h2>
    <div class="ba-list">{ba}</div>
    <p class="note">
      直した観点は六つある。第一に、比喩で意味を圧縮しないこと。
      「効く」は薬に使う言葉であり、路線には使わない。
      第二に、良し悪しの方向まで書くこと。「夜は森下のほうが開いている」では、
      何が開いていて、それが利点なのか欠点なのかを読み手が判断できない。
      第三に、不都合を抽象的な動詞で圧縮しないこと。「週末の生活が滞る」では、
      通勤が遅れるのか買い物に行けないのかが読み手に伝わらない。
      第四に、地域名を比較の基準にするときは「深川エリア」のように範囲を表す語を付けること。
      第五に、「選択肢」「多さ」には何の選択肢・何の多さなのかを書くこと。
      「外食と夜の選択肢」では、夜の何の選択肢なのかが分からない。
      第六に、程度でしかないことを「ない」と言い切らないこと。
      該当した箇所を合計110以上書き直した。
    </p>
  </section>

  {"".join(render(d) for d in data)}

  <section class="caveat">
    <h2>この17駅はまだ下書きである</h2>
    <p>
      構成と観点は基準を満たしているが、個々の事実の裏取りが済んでいない。
      とくに浸水・高潮の想定区域、店名と徒歩分数、ホームの深さは、
      区のハザードマップと現地で確認しなければ公開できない。
      ここで見ていただきたいのは書きぶりであり、事実の正しさではない。
    </p>
  </section>

  <footer>
    Tokyo Living Compass ／ 掲載候補448駅のうち、16層すべてを書き終えたのは17駅。
  </footer>
</div>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"{out} を生成した（{len(data)}駅）")


if __name__ == "__main__":
    main()
