import { SCORE_AXES, type ScoreAxis } from "@/lib/schema";
import { gradeSymbol, toFivePoint, toGrade, type Grade } from "@/lib/scoring";
import type { Dictionary } from "@/lib/dictionaries";

import { AxisIcon } from "./AxisIcon";

export const GRADE_STYLES: Record<Grade, string> = {
  excellent: "bg-good-soft text-good",
  good: "bg-accent-soft text-accent-strong",
  fair: "bg-fair-soft text-ink-soft",
  poor: "bg-bad-soft text-bad",
};

export const BAR_STYLES: Record<Grade, string> = {
  excellent: "bg-good",
  good: "bg-accent-bright",
  fair: "bg-fair",
  poor: "bg-bad",
};

/**
 * 好みで向きが変わる軸。飲食店やナイトライフは、多いほうがよい人もいれば
 * 静かなほうがよい人もいる（CLAUDE.md ルール40）。良し悪しの色を付けず、
 * 中立の色の棒で出す。強み・弱みの一覧にも入れない。
 */
export const PREFERENCE_AXES: ReadonlySet<ScoreAxis> = new Set([
  "food",
  "cafe",
  "nightlife",
]);

export function ScoreRow({
  axis,
  value,
  dict,
  className = "",
}: {
  axis: ScoreAxis;
  value: number | undefined;
  dict: Dictionary;
  className?: string;
}) {
  if (value === undefined) {
    return (
      <li className={`flex items-center gap-3 py-2.5 ${className}`}>
        <AxisIcon axis={axis} className="size-4 shrink-0 text-ink-soft/60" />
        <span className="min-w-0 flex-1 text-sm text-ink-soft">{dict.axes[axis]}</span>
        <span className="rounded-full bg-fair-soft px-2 py-0.5 text-xs text-ink-soft">
          {dict.dataQuality.notAvailable}
        </span>
      </li>
    );
  }
  const neutral = PREFERENCE_AXES.has(axis);
  const grade = toGrade(value);
  const points = toFivePoint(value);
  return (
    <li className={`flex items-center gap-3 py-2.5 ${className}`}>
      <AxisIcon axis={axis} className="size-4 shrink-0 text-accent" />
      <span className="min-w-0 flex-1 truncate text-sm text-ink">{dict.axes[axis]}</span>
      <span aria-hidden="true" className="h-2 w-16 shrink-0 overflow-hidden rounded-full bg-line sm:w-24">
        <span
          className={`block h-full rounded-full ${neutral ? "bg-accent-bright/70" : BAR_STYLES[grade]}`}
          style={{ width: `${(points / 5) * 100}%` }}
        />
      </span>
      <span className="w-12 shrink-0 text-right text-sm tabular-nums text-ink">
        <span className="font-semibold">{points.toFixed(1)}</span>
        <span className="text-xs text-ink-soft">/5</span>
      </span>
      {neutral ? (
        <span className="w-7 shrink-0" aria-hidden="true" />
      ) : (
        <span
          className={`w-7 shrink-0 rounded-md py-0.5 text-center text-xs font-semibold ${GRADE_STYLES[grade]}`}
        >
          <span aria-hidden="true">{gradeSymbol(grade)}</span>
          <span className="sr-only">{dict.grades[grade]}</span>
        </span>
      )}
    </li>
  );
}

/**
 * 軸ごとの評点。5点満点で出す。
 * ◎○△× は色だけに頼らず記号とテキストを併記する（docs/01-requirements.md §5）。
 */
export function ScoreGrid({
  scores,
  dict,
}: {
  scores: Partial<Record<ScoreAxis, number>>;
  dict: Dictionary;
}) {
  return (
    <ul className="grid grid-cols-1 sm:grid-cols-2 sm:gap-x-10">
      {SCORE_AXES.map((axis) => (
        <ScoreRow
          key={axis}
          axis={axis}
          value={scores[axis]}
          dict={dict}
          className="border-b border-line"
        />
      ))}
    </ul>
  );
}
