import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SeedNotice } from "@/components/SeedNotice";
import { getDictionary } from "@/lib/dictionaries";
import { formatYen } from "@/lib/format";
import { ACTIVE_LOCALES, isActiveLocale, type ActiveLocale } from "@/lib/i18n";
import {
  OFFICE_HUBS,
  RENT_TYPES,
  SCORE_AXES,
  type LocalizedStation,
} from "@/lib/schema";
import { gradeSymbol, overallScoreForPreset, toGrade } from "@/lib/scoring";
import { getLocalizedStation, getLocalizedStations } from "@/lib/stations";

const SEPARATOR = "-vs-";

function parsePair(pair: string): [string, string] | null {
  const index = pair.indexOf(SEPARATOR);
  if (index <= 0) return null;
  const a = pair.slice(0, index);
  const b = pair.slice(index + SEPARATOR.length);
  return a && b && a !== b ? [a, b] : null;
}

/**
 * 全組み合わせは生成しない。実際に比較されうるペア（似ている駅として登録済み）だけを
 * 静的生成し、薄いページの大量生成を避ける（docs/05-seo.md §3）。
 */
export function generateStaticParams() {
  return ACTIVE_LOCALES.flatMap((locale) => {
    const seen = new Set<string>();
    return getLocalizedStations(locale).flatMap((station) =>
      station.similarStations.flatMap((other) => {
        if (!getLocalizedStation(other, locale)) return [];
        const key = [station.slug, other].sort().join(SEPARATOR);
        if (seen.has(key)) return [];
        seen.add(key);
        return [{ locale, pair: `${station.slug}${SEPARATOR}${other}` }];
      }),
    );
  });
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; pair: string }>;
}): Promise<Metadata> {
  const { locale, pair } = await params;
  if (!isActiveLocale(locale)) return {};
  const slugs = parsePair(pair);
  if (!slugs) return {};
  const [a, b] = slugs.map((s) => getLocalizedStation(s, locale));
  if (!a || !b) return {};

  return {
    title: `${a.content.name} vs ${b.content.name}`,
    description: `${a.content.tagline} / ${b.content.tagline}`,
    alternates: { canonical: `/${locale}/compare/${pair}` },
    // 両駅とも reviewed 以上でなければ index させない（docs/05-seo.md §3）。
    robots:
      a.dataQuality === "seed" || b.dataQuality === "seed"
        ? { index: false, follow: true }
        : undefined,
  };
}

function Row({
  label,
  a,
  b,
  highlight,
}: {
  label: string;
  a: React.ReactNode;
  b: React.ReactNode;
  /** -1 = 左が優位、1 = 右が優位、0 = 同等 */
  highlight?: -1 | 0 | 1;
}) {
  const win = "font-semibold text-ink";
  const lose = "text-ink-soft";
  return (
    <tr className="border-b border-line">
      <th scope="row" className="py-2.5 pr-3 text-left text-sm font-normal text-ink-soft">
        {label}
      </th>
      <td
        className={`py-2.5 text-right tabular-nums ${
          highlight === undefined ? "text-ink" : highlight === -1 ? win : lose
        }`}
      >
        {a}
      </td>
      <td
        className={`py-2.5 pl-6 text-right tabular-nums ${
          highlight === undefined ? "text-ink" : highlight === 1 ? win : lose
        }`}
      >
        {b}
      </td>
    </tr>
  );
}

function compare(a: number, b: number, higherIsBetter = true): -1 | 0 | 1 {
  if (a === b) return 0;
  const aWins = higherIsBetter ? a > b : a < b;
  return aWins ? -1 : 1;
}

export default async function ComparePage({
  params,
}: {
  params: Promise<{ locale: string; pair: string }>;
}) {
  const { locale, pair } = await params;
  if (!isActiveLocale(locale)) notFound();

  const slugs = parsePair(pair);
  if (!slugs) notFound();

  const stations = slugs.map((s) => getLocalizedStation(s, locale as ActiveLocale));
  if (!stations[0] || !stations[1]) notFound();
  const [a, b] = stations as [LocalizedStation, LocalizedStation];

  const dict = getDictionary(locale);
  const overallA = overallScoreForPreset(a, "balanced");
  const overallB = overallScoreForPreset(b, "balanced");
  const hasSeedData = a.dataQuality === "seed" || b.dataQuality === "seed";

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="text-sm text-ink-soft">{dict.compare.heading}</p>
        <h1 className="text-3xl font-bold text-ink">
          {a.content.name} <span className="text-ink-soft">vs</span> {b.content.name}
        </h1>
      </header>

      {hasSeedData && <SeedNotice dict={dict} />}

      <div className="grid gap-4 sm:grid-cols-2">
        {[a, b].map((station) => (
          <Link
            key={station.slug}
            href={`/${locale}/stations/${station.slug}`}
            className="rounded-lg border border-line bg-surface p-5 hover:border-accent"
          >
            <h2 className="text-lg font-semibold text-ink">{station.content.name}</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              {station.content.tagline}
            </p>
          </Link>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[34rem] border-collapse">
          <thead>
            <tr className="border-b-2 border-line">
              <th className="py-2 text-left text-sm font-normal text-ink-soft" />
              <th className="py-2 text-right text-sm font-semibold text-ink">
                {a.content.name}
              </th>
              <th className="py-2 pl-6 text-right text-sm font-semibold text-ink">
                {b.content.name}
              </th>
            </tr>
          </thead>
          <tbody>
            <Row
              label={dict.station.overall}
              a={overallA.toFixed(1)}
              b={overallB.toFixed(1)}
              highlight={compare(overallA, overallB)}
            />

            {RENT_TYPES.map((type) => (
              <Row
                key={type}
                label={`${dict.station.rent} ${dict.rentTypes[type]}`}
                a={formatYen(a.rent[type], locale)}
                b={formatYen(b.rent[type], locale)}
                highlight={compare(a.rent[type], b.rent[type], false)}
              />
            ))}

            {OFFICE_HUBS.map((office) => {
              const ca = a.commutes.find((c) => c.to === office);
              const cb = b.commutes.find((c) => c.to === office);
              if (!ca || !cb) return null;
              return (
                <Row
                  key={office}
                  label={`${dict.station.commute} — ${dict.offices[office]}`}
                  a={`${ca.minutes} ${dict.station.minutes}`}
                  b={`${cb.minutes} ${dict.station.minutes}`}
                  highlight={compare(ca.minutes, cb.minutes, false)}
                />
              );
            })}

            {SCORE_AXES.map((axis) => (
              <Row
                key={axis}
                label={dict.axes[axis]}
                a={`${gradeSymbol(toGrade(a.scores[axis]))} ${a.scores[axis]}`}
                b={`${gradeSymbol(toGrade(b.scores[axis]))} ${b.scores[axis]}`}
                highlight={compare(a.scores[axis], b.scores[axis])}
              />
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        {[a, b].map((station) => (
          <section key={station.slug} className="space-y-2">
            <h3 className="text-sm font-semibold text-ink">
              {station.content.name} — {dict.station.residentComment}
            </h3>
            <blockquote className="rounded-md border-l-4 border-accent bg-accent-soft px-4 py-3 text-sm leading-relaxed text-ink">
              {station.content.residentComment}
            </blockquote>
          </section>
        ))}
      </div>
    </div>
  );
}
