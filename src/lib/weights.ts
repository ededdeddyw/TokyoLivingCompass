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
 *   お金の置き方  家賃を抑える / 立地に出す
 *
 * 17の評価軸そのものは動かさない。軸ごとの重みだけを変える。
 */

export type Weights = Record<ScoreAxis, number>;

/** すべての軸を均等に見るときの重み。 */
const BASE = 1;

/**
 * 区分を選んだときの、何も足されなかった軸の重み。
 *
 * 17軸すべてを1から始めると、選んだ軸に足した分が埋もれる。
 * 実際、全軸を1から始めたときは「子どもと住む」を選んでも
 * 池袋・御茶ノ水・秋葉原が上位に出た。飲食店・カフェ・医療・買い物といった
 * 都心で高く出る軸が11本あり、家族向けの軸に足した分を上回っていた。
 *
 * そこで、誰にとっても外せない軸は高いところから始め、
 * 好みで分かれる軸は低いところから始める。
 */
const SEGMENT_BASE: Partial<Record<ScoreAxis, number>> = {
  // 誰にとっても向きが同じ軸（docs/13-japanese-style-rules.md ルール40）
  commute: 2,
  rentValue: 2,
  disaster: 2,
  safety: 2,
  shopping: 1.5,
  healthcare: 1.5,
  quietness: 1.5,
  transitConvenience: 1.5,
  food: 1,
  nature: 0.5,
};
/** 上の表に無い軸（夜の店、カフェ、街のおしゃれさなど）の既定。 */
const SEGMENT_BASE_OTHER = 0.3;

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
  // 学区・公園・医療・静けさが効く。夜の店の多さは重くしない
  kids: { family: 5, safety: 3, nature: 3, quietness: 2, shopping: 2, healthcare: 2 },
  // 自炊しなくても生活が回るか、通勤が短いかが効く
  solo: { singleLife: 4, food: 2, commute: 2, cafe: 2 },
  // 夜に開いている店の多さが効く
  out: { nightlife: 5, food: 3, cafe: 2 },
  // 人の音と車の音の少なさが効く
  home: { quietness: 5, safety: 2, nature: 2 },
  // 同じ利便性でどれだけ安いかが効く
  thrifty: { rentValue: 6, shopping: 2 },
  // 通勤の速さと、乗り換えの余地、街並みが効く
  location: { commute: 4, transitConvenience: 3, style: 2 },
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
