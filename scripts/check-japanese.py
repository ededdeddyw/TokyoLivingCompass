#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本語表現ルール（docs/13-japanese-style-rules.md）のうち、
機械的に判定できるものを検査する。

  python3 scripts/check-japanese.py

検査対象は data/content/ja/*.json と docs/*.md。
機械が見られるのは一部にすぎない。論旨に関わるルール（2・5・10・12・15・20・25）は
検出できないため、書いたあとに人間が全文を読み返して確認する必要がある。
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ルール13: 手段の実力を超える強すぎる断定。
# 数値や出典で裏づけられる場合のみ使ってよいので、検出したら都度判断する。
TOO_STRONG = [
    "100%", "完全に", "必ず", "絶対に", "全く", "まったく問題",
    "最悪級", "突出して", "突出している", "屈指", "随一", "No.1",
    "間違いなく", "確実に", "最高", "最強", "圧倒的",
]

# ルール7: 強調意図のない冗長な述語。
REDUNDANT = [
    "できる状態にする", "を実現する", "を可能にする", "化を図る",
    "することが可能", "を行う必要がある",
]

# ルール1: 造語的・不自然な圧縮表現。
UNNATURAL = ["起点の", "残置", "仕組みで止ま", "軸に据える", "を担保する状態"]

# ルール18: 読み手が引っかかる独自ワード。プロジェクト内で見つけ次第足していく。
# ルール18 の独自ワードに加えて、意味を比喩で圧縮してしまう表現を集めた。
# 「住むと効く」のように、何がどうなるのかを書かずに雰囲気だけ伝える文は、
# 読み手に何も伝わらない（ルール1・4・5）。見つけ次第ここに足していく。
COINED = [
    "街の質感", "生活の道具としての性能", "体感距離", "ブランド化が起き",
    # 目的語を書かずに比喩で済ませる述語
    "効く", "効いて", "力がある", "価値が出る", "のしかかる",
    "刺さる", "化ける", "負担として表れる", "手応え",
    # 「街」を主語にした擬人的な表現。何がどうなるのかを書く
    "街の顔", "顔になる", "顔を見せる", "街の空気", "街の性格",
    "色が濃い", "色は薄い", "懐が深い", "代えがきかない街",
    # 良し悪しの方向が読み取れない述語。
    # 「夜は森下のほうが開いている」は、何が開いていて、それが利点なのか
    # 欠点なのかが分からない。主語と、読み手にとっての意味まで書く。
    "ほうが開いている", "夜が長い", "流れが速い", "空気が違う",
    "濃く残", "機能している", "成立している", "削られる",
    "音を拾う", "体感が", "選択肢は地図上",
]

# ルール27: 不都合を抽象的な動詞で圧縮した表現。
# 「生活が滞る」と書かれても、通勤が遅れるのか買い物に行けないのかが読み手に伝わらない。
# 誰の・どの行動が・どう妨げられるのかを直接書く。
VAGUE_TROUBLE = [
    "滞る", "滞ること", "支障が出る", "支障をきたす",
    "落ち着かないと感じ", "落ち着かないと受け取", "落ち着かない人",
    "回らなくなる", "立ち行かな", "目立つ要素", "指折り",
]

# ルール32: 災害を、資料に書いてある事実ではなく予測や評価として書いた形。
# 「氾濫が想定されている」と書くと、そこが危険な地域だと読む人が出る。
# ハザードマップの記載は「浸水想定区域に含まれる」と事実として書く。
HAZARD_ASSERTION = [
    "氾濫が想定", "浸水が想定される地域", "危険な地域", "危険地域",
    "安全性は", "安全な地域", "安全である", "リスクが高い", "リスクは低い",
    "水害の観点では条件が厳しい", "被害が出る",
]

# ルール33: 条件や人によって変わることを断定した形。
# 始発駅でもホームに列ができれば1本見送る。坂を負担と感じるかは人によって違う。
# 在住者コメント（residentComment）は一人の体験なので対象外にする。
CONDITIONAL_ASSERTION = [
    "始発なので座って通勤できる", "始発があり、座って通勤できる",
    "始発なので朝は座れる", "始発だから座れる",
    "毎日の移動で負担になる", "移動が負担になる", "負担になる。",
]

# ルール34: 費用が動くことだけを書いて終わっている形。
# 「食費が上がる」では、いくら上がるのか、それが読み手にとって痛い額なのかが伝わらない。
# 誰にとっての負担なのかまで書く。
COST_ONLY = [
    "食費が上がる", "食費が上がり", "食費がかさむ", "生活費が上がる",
    "高くつく", "生活コストの低さ", "生活コストを下げて", "生活コストを支えて",
]

# ルール30: それ自体では中身の決まらない名詞に、抽象的な修飾語しか付いていない形。
# 「外食と夜の選択肢」は、夜の何の選択肢なのかが書かれていない。
# 「夜に外食する選択肢」のように動作が書いてあるものは対象外。
# 機械で網羅はできないので、見つけた形を都度ここに足していく。
VAGUE_QUANTITY = [
    "夜の選択肢", "朝の選択肢", "昼の選択肢", "週末の選択肢",
    "医療の選択肢", "生活の選択肢", "街の選択肢", "実際の選択肢",
    "夜の多さ", "生活の多さ", "医療の多さ",
]

# ルール31: 名詞の一部を落とした略語。読み手に通じる形へ開く。
ABBREVIATIONS = {"生鮮": "生鮮品"}

# ルール28: 通称の地域名を、比較や範囲の基準として使うときは「深川エリア」と書く。
# 地名そのものを指す用法（「深川に住む世帯」「深川不動堂」）は対象外。
AREA_NAMES = ("深川", "城南", "城西", "城東", "城北", "湾岸", "下町")
AREA_BARE = re.compile(
    r"(" + "|".join(AREA_NAMES) + r")"
    r"(?!エリア|地区|一帯|方面|に住|不動|八幡|資料|公園|神社|祭|線|店|めし|飯|風)"
)

# ルール3: 文末の調子。「ですます調」と「である調」の混在を見る。
POLITE_END = re.compile(r"(です|ます|ました|ません|でしょう)[。！？]")
PLAIN_END = re.compile(r"(である|だった|した|ない|いる|なる|れる|られる)[。！？]")

# ルール22: 同じ述語の連発。
REPEATED_ENDINGS = [
    "たほうがいい", "確認したい", "必要がある", "ことになる",
    "とみてよい", "しておきたい", "が多い", "が分かれる",
]

# 検査しないキー（slug や locale など、日本語の文章ではないもの）。
SKIP_KEYS = {"slug", "locale", "authoredBy", "tier", "walkMinutes", "name"}


# 用言止めの判定。動詞の終止形はウ段（う・く・ぐ・す・つ・ぬ・ぶ・む・る）で終わり、
# 形容詞は「い」、過去は「た／だ」で終わる。名詞（漢字・カタカナ）で終われば体言止め。
YOGEN_TAIL = re.compile(r"[うくぐすつぬぶむるいたきしちにひみりえけせてねへめれ]$")
NOUN_LIKE = re.compile(r"(こと|もの|ため|とき|ところ|ほう|わけ|はず|つもり|ならでは|次第|通り|形|中心|側)$")


def is_yogen(body):
    """文末が用言（動詞・形容詞）で終わっているか。"""
    if re.search(r"(です|ます|ません|でしょう|だろう|である|だった|[^たな]だ)$", body):
        return True
    if NOUN_LIKE.search(body):
        return False
    return bool(YOGEN_TAIL.search(body))


def sentences(text):
    return [s for s in re.split(r"(?<=[。！？])", text) if s.strip()]


def walk(value, path, out):
    """JSON を再帰的にたどり、日本語の文字列とその場所を集める。"""
    if isinstance(value, dict):
        for k, v in value.items():
            if k in SKIP_KEYS:
                continue
            walk(v, f"{path}.{k}" if path else k, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            walk(v, f"{path}[{i}]", out)
    elif isinstance(value, str) and re.search(r"[ぁ-んァ-ヶ一-龠]", value):
        out.append((path, value))


def check_text(label, path, text, findings, taigen=True, claims=True):
    """
    findings には (種別, ファイル, 場所, ルール番号, 内容) を積む。
    種別は "違反"（機械で確定できるもの）と "要確認"（人間の判断が要るもの）。
    """
    def add(rule, detail, kind="違反"):
        findings.append((kind, label, path, rule, detail))

    # ルール13 は「明らかに言い切れる場合は使ってよい」ため、機械では確定できない。
    # 読み手に対する主張（駅コンテンツ）にだけ適用する。社内ドキュメントの
    # 「必ず参照する」のような指示文は、主張の強さの問題ではないため対象外。
    if claims:
        for word in TOO_STRONG:
            if word in text:
                add("13", f"強い断定: 「{word}」。手段の実力を超えていないか", "要確認")
    for word in REDUNDANT:
        if word in text:
            add("7", f"冗長な述語: 「{word}」")
    for word in UNNATURAL:
        if word in text:
            add("1", f"不自然・造語的: 「{word}」")
    for word in COINED:
        # 「魅力がある」「実力がある」のように、より長い自然な語の一部である場合は除く
        for m in re.finditer(re.escape(word), text):
            before = text[m.start() - 1] if m.start() > 0 else ""
            if word == "力がある" and before in "魅実威財体学":
                continue
            add("18", f"比喩・独自ワード: 「{word}」。何がどうなるのかを書く")
            break

    for word, opened in ABBREVIATIONS.items():
        if re.search(re.escape(word) + r"(?!品|食品|市場)", text):
            add("31", f"略語: 「{word}」。「{opened}」と開いて書く")
    for word in VAGUE_QUANTITY:
        if word in text:
            add("30", f"何の{word[-3:]}なのかが書かれていない: 「{word}」")
    for word in COST_ONLY:
        if word in text:
            add("34", f"費用の書き方: 「{word}」。誰の家計にどう効くのかまで書く")
    for word in HAZARD_ASSERTION:
        if word in text:
            add("32", f"災害の書き方: 「{word}」。"
                      f"資料に書いてある事実として書き、評価を加えない")
    if not path.endswith("residentComment"):
        for word in CONDITIONAL_ASSERTION:
            if word in text:
                add("33", f"条件で変わることの断定: 「{word}」。"
                          f"条件を書くか「〜人もいる」と範囲を限る")
    for word in VAGUE_TROUBLE:
        if word in text:
            add("27", f"不都合の圧縮: 「{word}」。何がどう不便になるのかを書く")
    for m in AREA_BARE.finditer(text):
        # 「城南」のように鉤括弧で括った語は、語そのものへの言及なので対象外
        if text[m.start() - 1:m.start()] == "「" and text[m.end():m.end() + 1] == "」":
            continue
        add("28", f"地域名に範囲を表す語がない: 「{m.group(1)}」。"
                  f"比較や範囲の基準なら「{m.group(1)}エリア」と書く")
        break

    # ルール26: 名詞の「抜け」。「抜ける」「抜け道」などの動詞・複合語は別語なので除く。
    if re.search(r"抜け(?!漏れ|る|た|て|ず|ない|道|穴|殻|出)", text):
        add("26", "名詞の「抜け」。常に「抜け漏れ」と書く")

    # ルール3: 同一フィールド内での文末の混在
    ss = sentences(text)
    polite = sum(1 for s in ss if POLITE_END.search(s))
    plain = sum(1 for s in ss if PLAIN_END.search(s))
    if polite > 0 and plain > 0:
        add("3", f"文末の混在: ですます調 {polite}文 / である調 {plain}文")

    # ルール3: 体言止め。1つのフィールドの中で用言止めと混在している場合だけ指摘する。
    # 「〜人」を並べた箇条書きのように全部が体言止めで揃っているものは、混在ではない。
    if not taigen or len(ss) < 2:
        return
    taigen_ends, yogen_ends = [], 0
    for s in ss:
        body = s.strip().rstrip("。！？")
        if not body:
            continue
        if is_yogen(body):
            yogen_ends += 1
        elif re.search(r"[ぁ-んァ-ヶ一-龠ー]$", body):
            taigen_ends.append(body[-14:])
    if taigen_ends and yogen_ends:
        add("3", f"体言止めと用言止めの混在（体言止め {len(taigen_ends)}文）: "
                 f"「…{taigen_ends[0]}」")


def check_repeats(label, texts, findings):
    """ルール22: 同じ述語が1駅・1文書の中で繰り返されていないか。"""
    joined = "".join(texts)
    for ending in REPEATED_ENDINGS:
        n = joined.count(ending)
        if n >= 3:
            findings.append(("違反", label, "(全体)", "22",
                             f"同じ述語の連発: 「{ending}」が {n} 回"))


def main():
    findings = []

    for p in sorted(glob.glob(os.path.join(ROOT, "data", "content", "ja", "*.json"))):
        label = os.path.basename(p)
        data = json.load(open(p, encoding="utf-8"))
        collected = []
        walk(data, "", collected)
        for path, text in collected:
            check_text(label, path, text, findings)
        check_repeats(label, [t for _, t in collected], findings)

    for p in sorted(glob.glob(os.path.join(ROOT, "docs", "*.md"))):
        label = os.path.basename(p)
        # ルール集そのものと、原文として保存している構想は対象外
        # 13 はルール集、00 は構想の原文、12 は NG 例を引用している品質基準
        if label.startswith(("13-", "00-", "12-")):
            continue
        text = open(p, encoding="utf-8").read()
        # コードブロックと表は検査から外す（記号が多く誤検知が増えるため）
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("|"))
        # 見出しと箇条書きの断片は体言止め判定に馴染まないので、語句だけを見る。
        check_text(label, "(本文)", text, findings, taigen=False, claims=False)

    violations = [f for f in findings if f[0] == "違反"]
    reviews = [f for f in findings if f[0] == "要確認"]

    def dump(items, heading):
        if not items:
            return
        print(f"{heading}（{len(items)}件）\n")
        by_file = {}
        for _kind, label, path, rule, detail in items:
            by_file.setdefault(label, []).append((path, rule, detail))
        for label in sorted(by_file):
            print(f"  ■ {label}")
            for path, rule, detail in by_file[label]:
                print(f"     ルール{rule:>2}  {path}")
                print(f"             {detail}")
            print()

    dump(violations, "◆ 違反")
    dump(reviews, "◇ 要確認（機械では判断できない。人間が見る）")

    print("※ 論旨に関わるルール（2・5・10・12・15・20・25）は機械では見られません。")
    print("   書いたあとに全文を読み返して自分で確認すること。")

    if not violations:
        print("\n確定違反はありません。")
        return
    sys.exit(1)


if __name__ == "__main__":
    main()
