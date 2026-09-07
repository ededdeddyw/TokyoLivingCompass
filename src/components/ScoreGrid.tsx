import { SCORE_AXES, type ScoreAxis } from "@/lib/schema";
import { gradeSymbol, toGrade } from "@/lib/scoring";
import type { Dictionary } from "@/lib/dictionaries";

const GRADE_STYLES = {
  excellent: "bg-[#e6f2ea] text-[#1c6b3f]",
  good: "bg-[#eaf1f7] text-[#1f5f8b]",
  fair: "bg-[#f3f4f6] text-[#5b6472]",
  poor: "bg-[#fbeeee] text-[#9a3b3b]",
} as const;

/** 16軸スコア。◎○△× は色だけに頼らず記号とテキストを併記する（docs/01-requirements.md §5）。 */
export function ScoreGrid({
  scores,
  dict,
}: {
  scores: Partial<Record<ScoreAxis, number>>;
  dict: Dictionary;
}) {
  return (
    <ul className="grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
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
        return (
          <li
            key={axis}
            className="flex items-center justify-between gap-3 border-b border-line py-2"
          >
            <span className="text-sm text-ink">{dict.axes[axis]}</span>
            <span className="flex items-center gap-2">
              <span
                className={`rounded px-2 py-0.5 text-sm font-medium ${GRADE_STYLES[grade]}`}
              >
                <span aria-hidden="true">{gradeSymbol(grade)}</span>
                <span className="sr-only">{dict.grades[grade]}</span>
              </span>
              <span className="w-8 text-right text-sm tabular-nums text-ink-soft">
                {value}
              </span>
            </span>
          </li>
        );
      })}
    </ul>
  );
}
