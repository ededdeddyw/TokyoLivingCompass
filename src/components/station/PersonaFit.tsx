"use client";

import { useState } from "react";
import { Armchair, Mountain, Sun, CalendarDays, ThumbsUp, TriangleAlert, TrainFront } from "lucide-react";

import type { PersonaFitLabels } from "@/lib/dictionaries";
import type { Persona, PlayStyle } from "@/lib/schema";

/**
 * 住む人の層と休日の過ごし方ごとの、向き不向き（docs/18-persona-days.md）。
 *
 * 点は駅のまわりだけで完結させず、電車で行きやすい駅まで含めて出している。
 * 大崎のまわりに広い公園は少ないが、電車で十数分の浜離宮やお台場へ行けるので、
 * アウトドア派でも休日を過ごせる。その「行き先」を点数と並べて見せる。
 *
 * 駅ページは静的に作るので、8通りの点をすべて渡しておき、ブラウザ側で選ぶ。
 */
export type PersonaDay = {
  who: string;
  weekday: string[];
  indoor: string[];
  outdoor: string[];
  good: string;
  care: string;
};


export type Destination = { name: string; minutes: number; here: boolean; parks?: string[] };

type Props = {
  scores: Record<`${Persona}-${PlayStyle}`, number | null>;
  /** 公開用の点に含めた通勤の割合（0〜1） */
  commuteShare: Record<Persona, number>;
  outdoorDest: Destination[];
  indoorDest: Destination[];
  days?: Partial<Record<Persona, PersonaDay>>;
  labels: PersonaFitLabels;
};

const PERSONA_ORDER: Persona[] = ["single", "dinks", "family", "senior"];
const STYLE_ORDER: PlayStyle[] = ["indoor", "outdoor"];

function Chips<T extends string>({
  legend,
  options,
  value,
  onChange,
  names,
}: {
  legend: string;
  options: T[];
  value: T;
  onChange: (v: T) => void;
  names: Record<T, string>;
}) {
  return (
    <fieldset>
      <legend className="text-xs font-semibold text-ink-soft">{legend}</legend>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {options.map((o) => (
          <button
            key={o}
            type="button"
            aria-pressed={o === value}
            onClick={() => onChange(o)}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-semibold transition ${
              o === value
                ? "border-accent bg-accent text-white"
                : "border-line bg-surface text-ink hover:border-accent"
            }`}
          >
            {names[o]}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function PersonaFit({ scores, commuteShare, outdoorDest, indoorDest, days, labels }: Props) {
  const [persona, setPersona] = useState<Persona>("single");
  const [style, setStyle] = useState<PlayStyle>("indoor");

  const value = scores[`${persona}-${style}`];
  const share = Math.round(commuteShare[persona] * 10);
  const day = days?.[persona];
  const dest = style === "outdoor" ? outdoorDest : indoorDest;
  const StyleIcon = style === "outdoor" ? Mountain : Armchair;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:gap-8">
        <Chips
          legend={labels.personaLegend}
          options={PERSONA_ORDER}
          value={persona}
          onChange={setPersona}
          names={labels.personas}
        />
        <Chips
          legend={labels.styleLegend}
          options={STYLE_ORDER}
          value={style}
          onChange={setStyle}
          names={labels.styles}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-[14rem_1fr]">
        <div className="rounded-2xl border border-sun/40 bg-sun-soft p-4 shadow-sm">
          <p className="text-xs text-sun-ink">
            {labels.scoreLabel
              .replace("{persona}", labels.personas[persona])
              .replace("{style}", labels.styles[style])}
          </p>
          <p className="mt-1">
            {value === null ? (
              <span className="text-sm text-ink-soft">{labels.noScore}</span>
            ) : (
              <>
                <strong className="text-3xl font-bold tabular-nums text-ink">
                  {value.toFixed(1)}
                </strong>
                <span className="text-sm text-ink-soft">/5</span>
              </>
            )}
          </p>
          <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">
            {share > 0
              ? labels.weightNote.replace("{commute}", String(share))
              : labels.weightNoteNoCommute}
          </p>
        </div>

        <div className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
          <h3 className="flex items-center gap-1.5 text-sm font-bold text-ink">
            <StyleIcon aria-hidden="true" className="size-4 text-accent" />
            {style === "outdoor" ? labels.destOutdoor : labels.destIndoor}
          </h3>
          <ul className="mt-2 space-y-1.5">
            {dest.map((d) => (
              <li key={d.name} className="flex items-start gap-2 text-sm">
                <TrainFront aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-ink-soft" />
                <span>
                  <span className="font-semibold text-ink">
                    {d.here ? labels.here : d.name}
                  </span>
                  {!d.here && (
                    <span className="ml-1.5 tabular-nums text-ink-soft">
                      {labels.minutes.replace("{minutes}", String(d.minutes))}
                    </span>
                  )}
                  {d.parks && d.parks.length > 0 && (
                    <span className="block text-xs text-ink-soft">{d.parks.join("・")}</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
        <h3 className="flex flex-wrap items-center gap-2 text-base font-bold text-ink">
          {labels.dayTitle.replace("{persona}", labels.personas[persona])}
          <span className="rounded-md bg-fair-soft px-2 py-0.5 text-xs font-semibold text-ink-soft">
            {labels.assumed}
          </span>
        </h3>
        {day ? (
          <>
            <p className="mt-1 text-xs text-ink-soft">
              {day.who} {labels.assumedNote}
            </p>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {(
                [
                  [labels.weekday, day.weekday, Sun],
                  [
                    `${labels.holiday}（${labels.styles[style]}）`,
                    style === "outdoor" ? day.outdoor : day.indoor,
                    CalendarDays,
                  ],
                ] as const
              ).map(([title, lines, Icon]) => (
                <div key={title}>
                  <p className="flex items-center gap-1.5 text-sm font-bold text-ink">
                    <Icon aria-hidden="true" className="size-4 text-sun" />
                    {title}
                  </p>
                  <ul className="mt-1.5 space-y-1.5 border-l-2 border-line pl-3 text-[15px] leading-relaxed text-ink-soft">
                    {lines.map((l) => (
                      <li key={l}>{l}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              <p className="flex gap-2 rounded-xl bg-good-soft p-3 text-sm leading-relaxed text-ink">
                <ThumbsUp aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-good" />
                <span>
                  <span className="font-semibold">{labels.good}: </span>
                  {day.good}
                </span>
              </p>
              <p className="flex gap-2 rounded-xl bg-bad-soft p-3 text-sm leading-relaxed text-ink">
                <TriangleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-bad" />
                <span>
                  <span className="font-semibold">{labels.care}: </span>
                  {day.care}
                </span>
              </p>
            </div>
          </>
        ) : (
          <p className="mt-2 text-sm text-ink-soft">{labels.noDay}</p>
        )}
      </div>

      <p className="text-xs leading-relaxed text-ink-soft">{labels.method}</p>
    </div>
  );
}
