import { SCORE_AXES, type ScoreAxis } from "./schema";

/** 重みプリセット（docs/03-scoring.md §5）。 */

export type Weights = Record<ScoreAxis, number>;

export const WEIGHT_PRESETS = [
  "balanced",
  "single",
  "family",
  "quiet",
  "value",
  "international",
] as const;

export type WeightPreset = (typeof WEIGHT_PRESETS)[number];

/** 明示しなかった軸に使う既定の重み。 */
const BASE = 1;

function build(overrides: Partial<Weights>): Weights {
  return Object.fromEntries(
    SCORE_AXES.map((axis) => [axis, overrides[axis] ?? BASE]),
  ) as Weights;
}

export const PRESET_WEIGHTS: Record<WeightPreset, Weights> = {
  balanced: build({}),
  single: build({
    commute: 5,
    food: 4,
    rentValue: 4,
    singleLife: 4,
    cafe: 2,
    nightlife: 2,
    transitConvenience: 2,
  }),
  family: build({
    safety: 5,
    quietness: 4,
    family: 5,
    shopping: 4,
    nature: 3,
    healthcare: 3,
    nightlife: 0,
  }),
  quiet: build({
    quietness: 5,
    safety: 4,
    nature: 3,
    rentValue: 3,
    nightlife: 0,
  }),
  value: build({
    rentValue: 6,
    commute: 4,
    shopping: 3,
    style: 0,
    nightlife: 0,
  }),
  international: build({
    internationalFriendliness: 5,
    commute: 4,
    transitConvenience: 3,
    food: 3,
    safety: 2,
  }),
};

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
