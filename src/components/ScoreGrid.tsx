import { SCORE_AXES, type ScoreAxis } from "@/lib/schema";
import { gradeSymbol, toFivePoint, toGrade } from "@/lib/scoring";
import type { Dictionary } from "@/lib/dictionaries";

const GRADE_STYLES = {
  excellent: "bg-[#e6f2ea] text-[#1c6b3f]",
  good: "bg-[#eaf1f7] text-[#1f5f8b]",
  fair: "bg-[#f3f4f6] text-[#5b6472]",
  poor: "bg-[#fbeeee] text-[#9a3b3b]",
} as const;

const BAR_STYLES = {
  excellent: "bg-[#1c6b3f]",
  good: "bg-[#1f5f8b]",
  fair: "bg-[#9aa2ae]",
  poor: "bg-[#9a3b3b]",
} as const;

/**
 * 軸ごとの評点。5点満点で出し、0–100の内部値も併記する。
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
    <ul className="grid grid-cols-1 gap-x-8 gap-y-1 sm:grid-cols-2">
      {SCORE_AXES.map((axis) => {
        const value = scores[axis];
        if (value === undefined) {
          return (
            <li
              key={axis}
              className="flex items-center justify-between gap-3 border-b border-line py-2"
            >
              <span className="text-sm text-ink-soft">{dict.axes[axis]}</span>
              <span className="text-sm text-ink-soft">
                {dict.dataQuality.notAvailable}
              </span>
            </li>
          );
        }
        const grade = toGrade(value);
        const points = toFivePoint(value);
        return (
          <li
            key={axis}
            className="flex items-center gap-3 border-b border-line py-2"
          >
            <span className="min-w-0 flex-1 truncate text-sm text-ink">
              {dict.axes[axis]}
            </span>
            <span
              aria-hidden="true"
              className="hidden h-1.5 w-20 shrink-0 overflow-hidden rounded-full bg-line sm:block"
            >
              <span
                className={`block h-full rounded-full ${BAR_STYLES[grade]}`}
                style={{ width: `${(points / 5) * 100}%` }}
              />
            </span>
            <span className="shrink-0 text-sm tabular-nums text-ink">
              <span className="font-medium">{points.toFixed(1)}</span>
              <span className="text-xs text-ink-soft">/5</span>
            </span>
            <span
              className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${GRADE_STYLES[grade]}`}
            >
              <span aria-hidden="true">{gradeSymbol(grade)}</span>
              <span className="sr-only">{dict.grades[grade]}</span>
            </span>
          </li>
        );
      })}
    </ul>
  );
}
