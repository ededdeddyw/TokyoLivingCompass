import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SeedNotice } from "@/components/SeedNotice";
import { StationCard } from "@/components/StationCard";
import { getDictionary } from "@/lib/dictionaries";
import { ACTIVE_LOCALES, isActiveLocale } from "@/lib/i18n";
import { overallScoreForPreset } from "@/lib/scoring";
import { getLocalizedStations } from "@/lib/stations";
import { isWeightPreset, WEIGHT_PRESETS, type WeightPreset } from "@/lib/weights";

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
  return { title: getDictionary(locale).list.heading };
}

export default async function StationsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ view?: string }>;
}) {
  const { locale } = await params;
  if (!isActiveLocale(locale)) notFound();

  const { view } = await searchParams;
  const preset: WeightPreset = view && isWeightPreset(view) ? view : "balanced";

  const dict = getDictionary(locale);
  const stations = getLocalizedStations(locale)
    .map((station) => ({ station, overall: overallScoreForPreset(station, preset) }))
    .sort((a, b) => b.overall - a.overall);

  const hasSeedData = stations.some(({ station }) => station.dataQuality === "seed");

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-ink">{dict.list.heading}</h1>
        <p className="text-sm text-ink-soft">
          {stations.length} {dict.list.count}
        </p>
      </header>

      {hasSeedData && <SeedNotice dict={dict} />}

      {/* 重みプリセットを変えるとランキングが変わる（docs/03-scoring.md §5）。
          状態は URL に載せて共有可能にする。 */}
      <nav className="space-y-2">
        <p className="text-sm font-medium text-ink">{dict.list.perspective}</p>
        <div className="flex flex-wrap gap-2">
          {WEIGHT_PRESETS.map((p) => (
            <Link
              key={p}
              href={p === "balanced" ? `/${locale}/stations` : `/${locale}/stations?view=${p}`}
              className={
                p === preset
                  ? "rounded-full bg-accent px-3.5 py-1.5 text-sm font-medium text-white"
                  : "rounded-full border border-line bg-surface px-3.5 py-1.5 text-sm text-ink-soft hover:border-accent hover:text-accent"
              }
            >
              {dict.presets[p]}
            </Link>
          ))}
        </div>
      </nav>

      <ol className="grid gap-4 sm:grid-cols-2">
        {stations.map(({ station, overall }, index) => (
          <li key={station.slug}>
            <StationCard
              station={station}
              locale={locale}
              dict={dict}
              overall={overall}
              footnote={`#${index + 1}`}
            />
          </li>
        ))}
      </ol>
    </div>
  );
}
