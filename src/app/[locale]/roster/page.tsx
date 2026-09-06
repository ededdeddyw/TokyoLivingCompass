import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getDictionary } from "@/lib/dictionaries";
import { ACTIVE_LOCALES, isActiveLocale, type ActiveLocale } from "@/lib/i18n";
import type { Line, RosterStation } from "@/lib/schema";
import { getAllStations, getLines, getRoster } from "@/lib/stations";

export function generateStaticParams() {
  return ACTIVE_LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  if (!isActiveLocale(locale)) return {};
  const dict = getDictionary(locale);
  return { title: dict.roster.heading, description: dict.roster.lead };
}

const OPERATOR_ORDER: Line["operator"][] = ["jr", "tokyo-metro", "toei", "private"];

function lineName(line: Line, locale: ActiveLocale) {
  return locale === "ja" ? line.nameJa : line.nameEn;
}

export default async function RosterPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ line?: string }>;
}) {
  const { locale } = await params;
  if (!isActiveLocale(locale)) notFound();

  const dict = getDictionary(locale);
  const lines = getLines();
  const { line: lineParam } = await searchParams;
  const activeLine = lineParam && lines.has(lineParam) ? lineParam : null;

  const profiled = new Set(getAllStations().map((s) => s.slug));
  const roster = getRoster().filter(
    (r) => !activeLine || r.lineIds.includes(activeLine),
  );

  // 区ごとにまとめる。並びは区コード順で固定する。
  const byWard = new Map<string, RosterStation[]>();
  for (const station of roster) {
    const list = byWard.get(station.wardCode) ?? [];
    list.push(station);
    byWard.set(station.wardCode, list);
  }

  const sortedLines = [...lines.values()].sort(
    (a, b) =>
      OPERATOR_ORDER.indexOf(a.operator) - OPERATOR_ORDER.indexOf(b.operator) ||
      a.id.localeCompare(b.id),
  );

  const chip = (active: boolean) =>
    active
      ? "rounded-full bg-accent px-3 py-1 text-sm font-medium text-white"
      : "rounded-full border border-line bg-surface px-3 py-1 text-sm text-ink-soft hover:border-accent hover:text-accent";

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">{dict.roster.heading}</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-ink-soft">{dict.roster.lead}</p>
        <p className="text-sm tabular-nums text-ink-soft">
          {roster.length} {dict.roster.stations} · {lines.size} {dict.roster.lines} ·{" "}
          {profiled.size} {dict.roster.profiled}
        </p>
      </header>

      <nav className="space-y-2">
        <p className="text-sm font-medium text-ink">{dict.roster.filterByLine}</p>
        <div className="flex flex-wrap gap-2">
          <Link href={`/${locale}/roster`} className={chip(activeLine === null)}>
            {dict.roster.allLines}
          </Link>
          {sortedLines.map((line) => (
            <Link
              key={line.id}
              href={`/${locale}/roster?line=${line.id}`}
              className={chip(line.id === activeLine)}
            >
              {lineName(line, locale)}
            </Link>
          ))}
        </div>
      </nav>

      <div className="space-y-8">
        {[...byWard.entries()]
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([wardCode, stations]) => (
            <section key={wardCode} className="space-y-3">
              <h2 className="border-b border-line pb-1 text-lg font-semibold text-ink">
                {stations[0].wardNameJa}
                <span className="ml-2 text-sm font-normal tabular-nums text-ink-soft">
                  {stations.length}
                </span>
              </h2>
              <ul className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
                {stations.map((station) => {
                  const hasProfile = profiled.has(station.slug);
                  const label = locale === "ja" ? station.nameJa : station.nameRomaji;
                  return (
                    <li
                      key={station.slug}
                      className="flex flex-wrap items-baseline gap-x-2 border-b border-line py-1.5"
                    >
                      {hasProfile ? (
                        <Link
                          href={`/${locale}/stations/${station.slug}`}
                          className="font-medium text-accent hover:underline"
                        >
                          {label}
                        </Link>
                      ) : (
                        <span className="text-ink">{label}</span>
                      )}
                      {locale !== "ja" && (
                        <span className="text-sm text-ink-soft">{station.nameJa}</span>
                      )}
                      <span className="ml-auto text-right text-sm text-ink-soft">
                        {station.lineIds
                          .map((id) => lines.get(id))
                          .filter((l): l is Line => Boolean(l))
                          .map((l) => lineName(l, locale))
                          .join(" / ")}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
      </div>
    </div>
  );
}
