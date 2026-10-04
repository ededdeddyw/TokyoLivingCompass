import { SCORE_AXES, type ScoreAxis } from "./schema";

/**
 * 重みの組み立て（docs/14-audience-segments.md、docs/03-scoring.md §5）。
 *
 * 以前は single / family / quiet / value / international の5つを並べていた。
 * この5つは互いに重なっており、「単身で、かつ静かな街に住みたい」人が
 * どれを選べばいいか決まらなかった。
 *
 * そこで、3つの軸に分ける。それぞれ2つに分かれ、組み合わせて8区分になる。
 *
 *   世帯        子どもと住む / 子どもなし
 *   夜の過ごし方  街で過ごす / 家で過ごす
 *   家賃と立地   家賃の安さを優先 / 立地のよさを優先
 *
 * 18の評価軸そのものは動かさない。どの軸を見るかだけを変える。
 */

export type Weights = Record<ScoreAxis, number>;

/** すべての軸を均等に見るときの重み。 */
const BASE = 1;

/**
 * 区分を選んだときに、どの軸も足されなかった場合の重み。
 *
 * 18軸すべてを1から始めると、選んだ軸に足した分が埋もれる。
 * 実際、全軸を1から始めたときは「夜は家で過ごす」を選んでも
 * 御茶ノ水が1位に出た。通勤・乗換・医療・買い物・飲食店がどれも高いため、
 * 静かさ1軸の低さが他の軸の高さに埋もれていた。
 *
 * そこで区分は「全軸の重みづけ」ではなく「見る軸の選択」として扱う。
 * 誰にとっても外せない軸だけを低い重みで残し、
 * 残りは選んだ側が足したときだけ点数に入るようにする。
 */
const SEGMENT_BASE: Partial<Record<ScoreAxis, number>> = {
  // 誰にとっても向きが同じ軸（docs/13-japanese-style-rules.md ルール40）
  commute: 2,
  disaster: 1.5,
  safety: 1.5,
  shopping: 1,
  healthcare: 1,
  transitConvenience: 1,
};
/** 上の表に無い軸は、選んだ側が足さなければ見ない。 */
const SEGMENT_BASE_OTHER = 0;

function build(overrides: Partial<Weights>, base: (axis: ScoreAxis) => number): Weights {
  return Object.fromEntries(
    SCORE_AXES.map((axis) => [axis, overrides[axis] ?? base(axis)]),
  ) as Weights;
}

const segmentBase = (axis: ScoreAxis) => SEGMENT_BASE[axis] ?? SEGMENT_BASE_OTHER;

/** 区分を決める3つの軸。並び順がそのまま画面の並び順になる。 */
export const SEGMENT_AXES = [
  { key: "household", options: ["kids", "solo"] },
  { key: "night", options: ["out", "home"] },
  { key: "money", options: ["thrifty", "location"] },
] as const;

export type SegmentAxis = (typeof SEGMENT_AXES)[number]["key"];
export type SegmentOption = (typeof SEGMENT_AXES)[number]["options"][number];

/**
 * 選んだ側ごとに、どの軸を重く見るか。
 *
 * 足し算で組み合わせる。0 にはしない。「子どもと住む」を選んだ人が
 * 「夜は街で過ごす」も選ぶことはあるので、片方の選択が
 * もう片方を打ち消さないようにする。
 */
const AXIS_WEIGHTS: Record<string, Partial<Weights>> = {
  // 学校・保育園・公園・医療・静けさを重く見る。夜の店の多さは見ない
  kids: { family: 6, nature: 3, quietness: 3, shopping: 3, healthcare: 3, safety: 4 },
  // 自炊しなくても生活が回るか、通勤が短いかを重く見る
  solo: { singleLife: 4, food: 3, commute: 4, cafe: 2 },
  // 夜に開いている店の多さを重く見る
  out: { nightlife: 6, food: 4, cafe: 3 },
  // 人の音と車の音の少なさを重く見る
  home: { quietness: 6, nature: 3, safety: 3 },
  // 絶対額の安さを重く見る。家賃コスパ（rentValue）は、同じ利便性の駅と比べた
  // 安さなので、池袋のような大きな駅が上に出る。抑えたい人が見たいのは絶対額である
  thrifty: { rentLow: 7, rentValue: 2, shopping: 2 },
  // 通勤の速さと、乗り換えの余地、街並みを重く見る
  location: { commute: 5, transitConvenience: 4, style: 3 },
};

/**
 * 区分の各側が足切りに使う軸。
 *
 * 重みつき平均だけで並べると、多くの軸で平均より上の駅が上位を占める。
 * 「夜は家で過ごす」を選んでも渋谷が1位に出ていた。静かさが29点しかなくても、
 * 通勤・乗換・買い物・医療がどれも95点を超えるため、1軸の低さが埋もれる。
 * 重みを上げるだけでは、この埋もれは直らなかった。
 *
 * そこで、区分が重く見る軸には足切りをかける。
 * 静かさを選んだ読み手に、静かさが下位2割に入る駅を上位で見せない。
 */
export const SEGMENT_GATES: Record<SegmentOption, ScoreAxis> = {
  kids: "family",
  solo: "singleLife",
  out: "nightlife",
  home: "quietness",
  thrifty: "rentLow",
  location: "commute",
};

/** 区分のキー。household-night-money をつないだもの。 */
export type SegmentKey = `${"kids" | "solo"}-${"out" | "home"}-${"thrifty" | "location"}`;

export const SEGMENT_KEYS: SegmentKey[] = SEGMENT_AXES[0].options.flatMap((h) =>
  SEGMENT_AXES[1].options.flatMap((n) =>
    SEGMENT_AXES[2].options.map((m) => `${h}-${n}-${m}` as SegmentKey),
  ),
);

/** 軸をすべて均等に見る既定。区分を選んでいない状態にあたる。 */
export const BALANCED = "balanced" as const;

export const WEIGHT_PRESETS = [BALANCED, ...SEGMENT_KEYS] as const;
export type WeightPreset = (typeof WEIGHT_PRESETS)[number];

function compose(key: SegmentKey): Weights {
  const merged: Partial<Weights> = {};
  for (const side of key.split("-")) {
    for (const [axis, add] of Object.entries(AXIS_WEIGHTS[side] ?? {})) {
      const a = axis as ScoreAxis;
      merged[a] = (merged[a] ?? segmentBase(a)) + add;
    }
  }
  return build(merged, segmentBase);
}

export const PRESET_WEIGHTS: Record<WeightPreset, Weights> = {
  [BALANCED]: build({}, () => BASE),
  ...(Object.fromEntries(SEGMENT_KEYS.map((k) => [k, compose(k)])) as Record<
    SegmentKey,
    Weights
  >),
};

/** 区分のキーを、軸ごとの選択に分解する。画面でどちらが選ばれているかを出すのに使う。 */
export function splitSegment(key: WeightPreset): Record<SegmentAxis, SegmentOption> | null {
  if (key === BALANCED) return null;
  const [household, night, money] = key.split("-");
  return {
    household: household as SegmentOption,
    night: night as SegmentOption,
    money: money as SegmentOption,
  };
}

/** 1つの軸だけを入れ替えたキーを返す。画面のボタンのリンク先に使う。 */
export function withOption(
  key: WeightPreset,
  axis: SegmentAxis,
  option: SegmentOption,
): SegmentKey {
  const current = splitSegment(key) ?? { household: "solo", night: "home", money: "thrifty" };
  const next = { ...current, [axis]: option };
  return `${next.household}-${next.night}-${next.money}` as SegmentKey;
}

/** 合計が 1 になるよう正規化する。重みが全て 0 の場合は均等割りにする。 */
export function normalize(weights: Weights): Weights {
  const total = SCORE_AXES.reduce((sum, axis) => sum + weights[axis], 0);
  if (total <= 0) {
    const even = 1 / SCORE_AXES.length;
    return Object.fromEntries(SCORE_AXES.map((a) => [a, even])) as Weights;
  }
  return Object.fromEntries(
    SCORE_AXES.map((a) => [a, weights[a] / total]),
  ) as Weights;
}

export function isWeightPreset(value: string): value is WeightPreset {
  return (WEIGHT_PRESETS as readonly string[]).includes(value);
}

/** 区分が足切りに使う軸を返す。区分を選んでいないときは足切りをしない。 */
export function segmentGateAxes(key: WeightPreset): ScoreAxis[] {
  const sides = splitSegment(key);
  if (!sides) return [];
  return SEGMENT_AXES.map((a) => SEGMENT_GATES[sides[a.key]]);
}
