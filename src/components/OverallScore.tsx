"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import {
  BALANCED,
  isWeightPreset,
  splitSegment,
  type SegmentOption,
  type WeightPreset,
} from "@/lib/weights";

/**
 * 駅ページの総合評価。
 *
 * 総合評価は読み手の区分ごとに変わる。一覧で「子どもと住む・夜は家で過ごす・
 * 家賃の安さを優先」を選んだときの雪が谷大塚は7.1点だが、すべての軸を均等に
 * 見ると5.2点である。一覧から駅ページへ移った読み手に別の数字を見せると、
 * どちらが正しいのか分からなくなる。
 *
 * そこで一覧のリンクが区分を URL に載せ、駅ページはその区分で計算した点数を出す。
 * どの区分で見た点数なのかも、数字のすぐ下に書く。
 *
 * 駅ページは1,832枚を静的に作るので、区分ごとの点数をすべて渡しておき、
 * 表示する1つだけをブラウザ側で選ぶ。
 */
export type OverallLabels = {
  overall: string;
  notAvailable: string;
  /** すべての軸を均等に見たときの注記 */
  balanced: string;
  /** 区分を選んだときの注記。{view} に区分の名前が入る */
  segment: string;
  options: Record<SegmentOption, string>;
};

type Props = {
  scores: Record<WeightPreset, number | null>;
  labels: OverallLabels;
};

function viewName(preset: WeightPreset, labels: OverallLabels): string | null {
  const sides = splitSegment(preset);
  if (!sides) return null;
  return [sides.household, sides.night, sides.money]
    .map((option) => labels.options[option])
    .join(" × ");
}

function Score({ preset, scores, labels }: Props & { preset: WeightPreset }) {
  const value = scores[preset] ?? null;
  const name = viewName(preset, labels);
  return (
    <div className="rounded-2xl border border-sun/40 bg-sun-soft p-4 shadow-sm">
      <p className="text-xs text-sun-ink">{labels.overall}</p>
      <p className="mt-1">
        <strong className="text-2xl font-bold tabular-nums text-ink sm:text-3xl">
          {value === null ? labels.notAvailable : value.toFixed(1)}
        </strong>
        {value !== null && <span className="text-sm text-ink-soft"> / 10</span>}
      </p>
      <p className="mt-1 text-[11px] leading-snug text-ink-soft">
        {name === null ? labels.balanced : labels.segment.replace("{view}", name)}
      </p>
    </div>
  );
}

function FromQuery(props: Props) {
  const params = useSearchParams();
  const raw = params.get("view");
  const preset: WeightPreset = raw && isWeightPreset(raw) ? raw : BALANCED;
  return <Score {...props} preset={preset} />;
}

export function OverallScore(props: Props) {
  // 静的に作った HTML には均等に見たときの点数が入る。
  // 区分つきのリンクで来た読み手には、ブラウザ側でその区分の点数に差し替える。
  return (
    <Suspense fallback={<Score {...props} preset={BALANCED} />}>
      <FromQuery {...props} />
    </Suspense>
  );
}
