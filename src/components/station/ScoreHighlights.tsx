import { CircleCheck, CircleAlert } from "lucide-react";

import type { Dictionary } from "@/lib/dictionaries";
import { SCORE_AXES, type ScoreAxis } from "@/lib/schema";
import { toFivePoint } from "@/lib/scoring";

import { AxisIcon } from "../AxisIcon";
import { PREFERENCE_AXES } from "../ScoreGrid";

/**
 * 強みと弱みを3つずつ。18軸を全部読む前に、この駅が何で選ばれ、何を手放すのかを渡す。
 * 好みで向きが変わる軸（飲食店・カフェ・ナイトライフ）は入れない。
 * 強みは上位3割（60点以上）、弱みは下位（40点未満）に入るものだけを出す。
 */
const STRONG = 60;
const WEAK = 40;

export function ScoreHighlights({
  scores,
  dict,
}: {
  scores: Partial<Record<ScoreAxis, number>>;
  dict: Dictionary;
}) {
  const rated = SCORE_AXES.filter(
    (a) => scores[a] !== undefined && !PREFERENCE_AXES.has(a),
  ).map((a) => [a, scores[a] as number] as const);
  const strengths = rated
    .filter(([, v]) => v >= STRONG)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  const weaknesses = rated
    .filter(([, v]) => v < WEAK)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 3);
  const ui = dict.stationUi;

  const list = (items: typeof strengths, good: boolean) => (
    <ul className="mt-3 space-y-2">
      {items.map(([axis, v]) => (
        <li key={axis} className="flex items-center gap-2.5">
          <span
            className={`grid size-8 shrink-0 place-items-center rounded-full ${good ? "bg-good-soft text-good" : "bg-bad-soft text-bad"}`}
          >
            <AxisIcon axis={axis} className="size-4" />
          </span>
          <span className="flex-1 text-sm font-medium text-ink">{dict.axes[axis]}</span>
          <span className="text-sm tabular-nums text-ink-soft">
            <span className="font-semibold text-ink">{toFivePoint(v).toFixed(1)}</span>/5
          </span>
        </li>
      ))}
    </ul>
  );

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <div className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
        <h3 className="flex items-center gap-1.5 text-sm font-bold text-good">
          <CircleCheck aria-hidden="true" className="size-4" />
          {ui.strengths}
        </h3>
        {strengths.length > 0 ? (
          list(strengths, true)
        ) : (
          <p className="mt-3 text-sm text-ink-soft">{ui.strengthsNone}</p>
        )}
      </div>
      <div className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
        <h3 className="flex items-center gap-1.5 text-sm font-bold text-bad">
          <CircleAlert aria-hidden="true" className="size-4" />
          {ui.weaknesses}
        </h3>
        {weaknesses.length > 0 ? (
          list(weaknesses, false)
        ) : (
          <p className="mt-3 text-sm text-ink-soft">{ui.weaknessesNone}</p>
        )}
      </div>
    </div>
  );
}
