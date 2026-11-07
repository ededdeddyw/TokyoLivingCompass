"use client";

import { useEffect, useMemo, useState } from "react";

import {
  DEFAULT_CONDITIONS,
  activeKeys,
  fromQuery,
  relaxGains,
  sortSurvivors,
  survivors,
  toQuery,
  withoutCondition,
  type ChooseStation,
  type ConditionKey,
  type Conditions,
} from "@/lib/choose";
import type { ChooseText } from "@/lib/choose-text";
import { OFFICE_HUBS, RENT_TYPES, type OfficeHub, type RentType } from "@/lib/schema";

/**
 * 条件で駅を消していく道具（src/lib/choose.ts）の画面。
 *
 * 質問に1つずつ答える画面と、残った駅の画面の2つを持つ。どちらの画面でも、
 * いまの条件で残る駅の数を上に出し続ける。条件は URL に載せ、同じ条件を人に送れるようにする。
 * 駅のデータはサーバーで組み立てて props で受け取る（CLAUDE.md 設計上の約束3）。
 */

type Props = {
  locale: string;
  stations: ChooseStation[];
  text: ChooseText;
  offices: Record<string, string>;
  rentTypes: Record<RentType, string>;
};

const STEPS = ["office", "minutes", "transfers", "rent", "flood", "hightide", "living"] as const;
type Step = (typeof STEPS)[number];

const MINUTE_OPTIONS = [30, 40, 50, 60];
const TRANSFER_OPTIONS = [0, 1, 2];
/** 間取りごとの家賃の上限の選び方（万円） */
const RENT_OPTIONS: Record<RentType, number[]> = {
  oneRoom: [6, 7, 8, 9, 10, 12, 15],
  oneK: [7, 8, 9, 10, 12, 15, 20],
  oneLDK: [12, 15, 18, 20, 25, 30],
  twoLDK: [15, 18, 20, 25, 30, 40],
};

function fill(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(values[k] ?? ""));
}

export function ChooseTool({ locale, stations, text, offices, rentTypes }: Props) {
  const [c, setC] = useState<Conditions>(DEFAULT_CONDITIONS);
  const [step, setStep] = useState<Step | "results">("office");
  const [copied, setCopied] = useState(false);

  // 共有された URL から条件を読む。条件が付いていれば、結果の画面から始める
  useEffect(() => {
    const q = window.location.search.slice(1);
    if (!q) return;
    const loaded = fromQuery(q);
    setC(loaded);
    if (activeKeys(loaded).length > 0 || loaded.office) setStep("results");
  }, []);

  useEffect(() => {
    const q = toQuery(c);
    const url = `${window.location.pathname}${q ? `?${q}` : ""}`;
    window.history.replaceState(null, "", url);
  }, [c]);

  const left = useMemo(() => survivors(stations, c), [stations, c]);
  const total = stations.length;

  const counter = (
    <p className="text-sm text-ink-soft" aria-live="polite">
      <span className="text-2xl font-bold text-accent-strong">{fill(text.remaining, { n: left.length })}</span>
      {fill(text.of, { total })}
    </p>
  );

  const steps = STEPS.filter((s) => c.office || (s !== "minutes" && s !== "transfers"));
  const go = (dir: 1 | -1) => {
    if (step === "results") return;
    const i = steps.indexOf(step);
    const next = steps[i + dir];
    setStep(next ?? (dir > 0 ? "results" : step));
  };

  if (step === "results") {
    return (
      <Results
        locale={locale}
        stations={stations}
        c={c}
        setC={setC}
        text={text}
        offices={offices}
        rentTypes={rentTypes}
        counter={counter}
        restart={() => setStep("office")}
        copied={copied}
        copy={() => {
          void navigator.clipboard?.writeText(window.location.href).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          });
        }}
      />
    );
  }

  const s = text.steps;
  const option = (label: string, selected: boolean, onClick: () => void) => (
    <button
      key={label}
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`w-full rounded-lg border px-4 py-3 text-left text-sm leading-relaxed transition-colors ${
        selected ? "border-accent bg-accent/10 font-semibold text-ink" : "border-line bg-surface text-ink hover:border-accent"
      }`}
    >
      {label}
    </button>
  );

  let body: React.ReactNode = null;
  let q = "";
  let note = "";
  switch (step) {
    case "office":
      q = s.office.q;
      note = s.office.note;
      body = (
        <div className="grid gap-2 sm:grid-cols-2">
          {OFFICE_HUBS.map((o: OfficeHub) =>
            option(offices[o] ?? o, c.office === o, () => setC({ ...c, office: o })),
          )}
          {option(text.noOffice, c.office === null, () =>
            setC({ ...c, office: null, maxMinutes: null, maxTransfers: null }),
          )}
        </div>
      );
      break;
    case "minutes":
      q = s.minutes.q;
      note = s.minutes.note;
      body = (
        <div className="grid gap-2 sm:grid-cols-2">
          {MINUTE_OPTIONS.map((m) =>
            option(fill(text.minutesOption, { n: m }), c.maxMinutes === m, () => setC({ ...c, maxMinutes: m })),
          )}
          {option(text.any, c.maxMinutes === null, () => setC({ ...c, maxMinutes: null }))}
        </div>
      );
      break;
    case "transfers":
      q = s.transfers.q;
      note = s.transfers.note;
      body = (
        <div className="grid gap-2 sm:grid-cols-2">
          {TRANSFER_OPTIONS.map((t) =>
            option(
              t === 0 ? text.transfersZero : fill(text.transfersOption, { n: t }),
              c.maxTransfers === t,
              () => setC({ ...c, maxTransfers: t }),
            ),
          )}
          {option(text.any, c.maxTransfers === null, () => setC({ ...c, maxTransfers: null }))}
        </div>
      );
      break;
    case "rent":
      q = s.rent.q;
      note = s.rent.note;
      body = (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2" role="radiogroup">
            {RENT_TYPES.map((t) => (
              <button
                key={t}
                type="button"
                role="radio"
                aria-checked={c.rentType === t}
                onClick={() => setC({ ...c, rentType: t, maxRent: null })}
                className={`rounded-full border px-3 py-1 text-sm ${
                  c.rentType === t ? "border-accent bg-accent text-white" : "border-line bg-surface text-ink hover:border-accent"
                }`}
              >
                {rentTypes[t]}
              </button>
            ))}
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {RENT_OPTIONS[c.rentType].map((n) =>
              option(fill(text.rentOption, { n }), c.maxRent === n * 10000, () =>
                setC({ ...c, maxRent: n * 10000 }),
              ),
            )}
            {option(text.any, c.maxRent === null, () => setC({ ...c, maxRent: null }))}
          </div>
        </div>
      );
      break;
    case "flood":
      q = s.flood.q;
      note = s.flood.note;
      body = (
        <div className="space-y-2">
          {option(s.flood.any, c.flood === "any", () => setC({ ...c, flood: "any" }))}
          {option(s.flood.deep, c.flood === "deep", () => setC({ ...c, flood: "deep" }))}
          {option(s.flood.inZone, c.flood === "inZone", () => setC({ ...c, flood: "inZone" }))}
          <p className="pt-1 text-xs leading-relaxed text-ink-soft">{text.hazardNote}</p>
        </div>
      );
      break;
    case "hightide":
      q = s.hightide.q;
      note = s.hightide.note;
      body = (
        <div className="space-y-2">
          {option(s.hightide.any, c.hightide === "any", () => setC({ ...c, hightide: "any" }))}
          {option(s.hightide.inZone, c.hightide === "inZone", () => setC({ ...c, hightide: "inZone" }))}
          <p className="pt-1 text-xs leading-relaxed text-ink-soft">{text.hazardNote}</p>
        </div>
      );
      break;
    case "living":
      q = s.living.q;
      note = s.living.note;
      body = (
        <div className="space-y-2">
          {option(s.living.slope, c.slope === "noHilly", () =>
            setC({ ...c, slope: c.slope === "noHilly" ? "any" : "noHilly" }),
          )}
          {option(s.living.lines, c.lines === "noSingle", () =>
            setC({ ...c, lines: c.lines === "noSingle" ? "any" : "noSingle" }),
          )}
          {option(s.living.motorway, c.motorway === "noNear", () =>
            setC({ ...c, motorway: c.motorway === "noNear" ? "any" : "noNear" }),
          )}
          {option(s.living.safety, c.safety === "noLow", () =>
            setC({ ...c, safety: c.safety === "noLow" ? "any" : "noLow" }),
          )}
        </div>
      );
      break;
  }

  const i = steps.indexOf(step);
  return (
    <div className="space-y-5 rounded-2xl border border-line bg-surface p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        {counter}
        <p className="text-xs text-ink-soft">
          {i + 1} / {steps.length}
        </p>
      </div>
      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-ink">{q}</h2>
        <p className="text-sm leading-relaxed text-ink-soft">{note}</p>
      </div>
      {body}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <button
          type="button"
          onClick={() => go(-1)}
          disabled={i === 0}
          className="rounded-md border border-line px-4 py-2 text-sm text-ink disabled:opacity-40"
        >
          {text.back}
        </button>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setStep("results")}
            className="rounded-md border border-line px-4 py-2 text-sm text-ink hover:border-accent"
          >
            {text.showResults}
          </button>
          <button
            type="button"
            onClick={() => go(1)}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            {i === steps.length - 1 ? text.showResults : text.next}
          </button>
        </div>
      </div>
    </div>
  );
}

type ResultsProps = {
  locale: string;
  stations: ChooseStation[];
  c: Conditions;
  setC: (c: Conditions) => void;
  text: ChooseText;
  offices: Record<string, string>;
  rentTypes: Record<RentType, string>;
  counter: React.ReactNode;
  restart: () => void;
  copied: boolean;
  copy: () => void;
};

function chipLabel(key: ConditionKey, c: Conditions, text: ChooseText, offices: Record<string, string>, rentTypes: Record<RentType, string>): string {
  const ch = text.chips;
  switch (key) {
    case "commute":
      return fill(ch.commute, { n: c.maxMinutes ?? "", office: c.office ? offices[c.office] ?? c.office : "" });
    case "transfers":
      return c.maxTransfers === 0 ? ch.transfersZero : fill(ch.transfers, { n: c.maxTransfers ?? "" });
    case "rent":
      return fill(ch.rent, { type: rentTypes[c.rentType], n: (c.maxRent ?? 0) / 10000 });
    case "flood":
      return c.flood === "deep" ? ch.floodDeep : ch.floodInZone;
    case "hightide":
      return ch.hightide;
    case "slope":
      return ch.slope;
    case "lines":
      return ch.lines;
    case "motorway":
      return ch.motorway;
    case "safety":
      return ch.safety;
  }
}

function Results({ locale, stations, c, setC, text, offices, rentTypes, counter, restart, copied, copy }: ResultsProps) {
  const r = text.results;
  const keys = activeKeys(c);
  const gains = useMemo(() => relaxGains(stations, c), [stations, c]);
  const list = useMemo(() => sortSurvivors(survivors(stations, c), c), [stations, c]);

  return (
    <div className="space-y-6">
      <section className="space-y-3 rounded-2xl border border-line bg-surface p-5 sm:p-6">
        {counter}
        <h2 className="text-base font-semibold text-ink">{r.conditionsHeading}</h2>
        {keys.length === 0 ? (
          <p className="text-sm text-ink-soft">{r.noConditions}</p>
        ) : (
          <ul className="space-y-2">
            {keys.map((k) => (
              <li key={k} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line px-3 py-2">
                <span className="text-sm text-ink">{chipLabel(k, c, text, offices, rentTypes)}</span>
                <span className="flex items-center gap-3">
                  <span className="text-xs text-ink-soft">
                    {gains[k] ? fill(r.relax, { n: gains[k] as number }) : r.relaxNone}
                  </span>
                  <button
                    type="button"
                    onClick={() => setC(withoutCondition(c, k))}
                    className="rounded-md border border-line px-2 py-1 text-xs text-ink hover:border-accent"
                  >
                    {r.remove}
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}
        <div className="flex flex-wrap gap-2 pt-1">
          <button type="button" onClick={restart} className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:opacity-90">
            {r.edit}
          </button>
          <button type="button" onClick={() => setC(DEFAULT_CONDITIONS)} className="rounded-md border border-line px-3 py-1.5 text-sm text-ink hover:border-accent">
            {r.reset}
          </button>
          <button type="button" onClick={copy} className="rounded-md border border-line px-3 py-1.5 text-sm text-ink hover:border-accent">
            {copied ? r.copied : r.copy}
          </button>
        </div>
        {(c.flood !== "any" || c.hightide !== "any") && (
          <p className="text-xs leading-relaxed text-ink-soft">{text.hazardNote}</p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-ink">{r.heading}</h2>
        <p className="text-sm text-ink-soft">{c.office ? r.sortedByCommute : r.sortedByOverall}</p>
        {list.length === 0 ? (
          <p className="rounded-lg border border-line bg-surface p-4 text-sm leading-relaxed text-ink">{r.empty}</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {list.map(({ station, unknown }) => {
              const m = c.office ? station.commutes[c.office] : undefined;
              const high = station.rent[c.rentType];
              const low = station.rentLow[c.rentType];
              return (
                <li key={station.slug}>
                  <a
                    href={`/${locale}/stations/${station.slug}`}
                    className="block h-full space-y-1 rounded-xl border border-line bg-surface p-4 hover:border-accent"
                  >
                    <p className="flex flex-wrap items-baseline gap-2">
                      <span className="text-base font-semibold text-ink">{station.name}</span>
                      <span className="text-xs text-ink-soft">{station.ward}</span>
                    </p>
                    {m && c.office && (
                      <p className="text-sm text-ink">
                        {m.walk
                          ? fill(r.walkValue, { office: offices[c.office] ?? c.office, minutes: m.minutes })
                          : fill(r.commuteValue, {
                              office: offices[c.office] ?? c.office,
                              minutes: m.minutes,
                              transfers: m.transfers,
                            })}
                      </p>
                    )}
                    <p className="text-sm text-ink">
                      {high !== undefined && low !== undefined
                        ? fill(r.rentValue, { type: rentTypes[c.rentType], low: low / 10000, high: high / 10000 })
                        : fill(r.rentMissing, { type: rentTypes[c.rentType] })}
                    </p>
                    {unknown.length > 0 && (
                      <p className="text-xs text-ink-soft">
                        {r.unknownLabel}: {unknown.map((k) => text.unknownNames[k]).join(locale === "en" ? ", " : "・")}
                      </p>
                    )}
                  </a>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
