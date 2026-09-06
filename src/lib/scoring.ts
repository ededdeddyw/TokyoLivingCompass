import {
  SCORE_AXES,
  type OfficeHub,
  type RentType,
  type ScoreAxis,
  type Station,
} from "./schema";
import { normalize, PRESET_WEIGHTS, type WeightPreset, type Weights } from "./weights";

/** スコア計算（docs/03-scoring.md）。派生値はここで毎回計算し、データには保存しない。 */

export type Grade = "excellent" | "good" | "fair" | "poor";

const GRADE_SYMBOLS: Record<Grade, string> = {
  excellent: "◎",
  good: "○",
  fair: "△",
  poor: "×",
};

export function toGrade(score: number): Grade {
  if (score >= 80) return "excellent";
  if (score >= 60) return "good";
  if (score >= 40) return "fair";
  return "poor";
}

export function gradeSymbol(grade: Grade): string {
  return GRADE_SYMBOLS[grade];
}

/** 重みつき総合評価。0–10 で返す（表示は小数第1位）。 */
export function overallScore(station: Station, weights: Weights): number {
  const w = normalize(weights);
  const weighted = SCORE_AXES.reduce(
    (sum, axis) => sum + station.scores[axis] * w[axis],
    0,
  );
  return Math.round(weighted) / 10;
}

export function overallScoreForPreset(
  station: Station,
  preset: WeightPreset,
): number {
  return overallScore(station, PRESET_WEIGHTS[preset]);
}

/** スコアの高い順に軸を返す。「なぜ推すのか」の説明に使う。 */
export function strongestAxes(station: Station, count: number): ScoreAxis[] {
  return [...SCORE_AXES]
    .sort((a, b) => station.scores[b] - station.scores[a])
    .slice(0, count);
}

/** スコアの低い順に軸を返す。「弱点」の説明に使う。 */
export function weakestAxes(station: Station, count: number): ScoreAxis[] {
  return [...SCORE_AXES]
    .sort((a, b) => station.scores[a] - station.scores[b])
    .slice(0, count);
}

export function commuteTo(
  station: Station,
  office: OfficeHub,
): { minutes: number; transfers: number } | null {
  const found = station.commutes.find((c) => c.to === office);
  return found ? { minutes: found.minutes, transfers: found.transfers } : null;
}

/** 逆引き検索の入力（docs/01-requirements.md F5）。 */
export type SearchCriteria = {
  office: OfficeHub;
  maxRent: number;
  rentType: RentType;
  maxMinutes: number;
  maxTransfers: number;
  weights: Weights;
};

export type MatchResult = {
  station: Station;
  /** 適合度 0–100 */
  fit: number;
  minutes: number;
  transfers: number;
  rent: number;
  strengths: ScoreAxis[];
  weaknesses: ScoreAxis[];
};

/**
 * 制約フィルタ × 重みつきスコア × 通勤ボーナス（docs/03-scoring.md §6）。
 * 制約を満たさない駅は結果に含めない。
 */
export function rankStations(
  stations: Station[],
  criteria: SearchCriteria,
): MatchResult[] {
  const weights = normalize(criteria.weights);

  const results: MatchResult[] = [];

  for (const station of stations) {
    const commute = commuteTo(station, criteria.office);
    if (!commute) continue;

    const rent = station.rent[criteria.rentType];
    if (rent > criteria.maxRent) continue;
    if (commute.minutes > criteria.maxMinutes) continue;
    if (commute.transfers > criteria.maxTransfers) continue;

    const weighted = SCORE_AXES.reduce(
      (sum, axis) => sum + station.scores[axis] * weights[axis],
      0,
    );

    // 上限に対して所要時間が短いほど加点する。上限ぎりぎりより余裕がある方を上位に。
    const commuteMargin =
      criteria.maxMinutes > 0
        ? Math.max(0, (criteria.maxMinutes - commute.minutes) / criteria.maxMinutes)
        : 0;
    const commuteBonus = commuteMargin * 10;

    results.push({
      station,
      fit: Math.min(100, Math.round(weighted + commuteBonus)),
      minutes: commute.minutes,
      transfers: commute.transfers,
      rent,
      strengths: strongestAxes(station, 3),
      weaknesses: weakestAxes(station, 2),
    });
  }

  return results.sort((a, b) => b.fit - a.fit);
}
