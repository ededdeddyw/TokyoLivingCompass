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
    "kiyosumi-shirakawa", "morishita", "monzen-nakacho",
    "koenji", "higashi-nakano", "nakameguro",
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
     "弱点は家賃の高さと、桜の時期に週末の生活が滞ること"),
    ("生活の道具としての性能が高い", "日々の暮らしやすさという点で優れている"),
    ("平日昼間は静か。住宅街の顔になる", "平日昼間は静まり、住宅街として静かに過ごせる"),
    ("東西線の朝ラッシュは都内最悪級", "東西線は朝の混雑率が高い区間として知られる"),
    ("カフェの密度は都内でも突出している", "カフェの密度は都内でもかなり高い"),
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

    body = f"""<title>深川・中央線の6駅</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap">
<style>{css}</style>

<div class="wrap">
  <header class="page-head">
    <p class="eyebrow">TOKYO LIVING COMPASS</p>
    <h1>16層で書き切った6駅</h1>
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
      「効く」は薬に使う言葉であり、路線には使わない。何がどうなるのかを書かずに
      雰囲気だけ伝える文は、読み手に何も残らない。該当した23箇所をすべて書き直した。
    </p>
  </section>

  {"".join(render(d) for d in data)}

  <section class="caveat">
    <h2>この6駅はまだ下書きである</h2>
    <p>
      構成と観点は基準を満たしているが、個々の事実の裏取りが済んでいない。
      とくに浸水・高潮の想定区域、店名と徒歩分数、大江戸線ホームの深さは、
      区のハザードマップと現地で確認しなければ公開できない。
      ここで見ていただきたいのは書きぶりであり、事実の正しさではない。
    </p>
  </section>

  <footer>
    Tokyo Living Compass ／ 掲載候補443駅のうち、16層すべてを書き終えたのは6駅。
  </footer>
</div>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"{out} を生成した（{len(data)}駅）")


if __name__ == "__main__":
    main()
