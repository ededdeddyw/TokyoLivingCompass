import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SeedNotice } from "@/components/SeedNotice";
import { getDictionary } from "@/lib/dictionaries";
import { formatYen } from "@/lib/format";
import { ACTIVE_LOCALES, isActiveLocale } from "@/lib/i18n";
import { OFFICE_HUBS, RENT_TYPES, type OfficeHub, type RentType } from "@/lib/schema";
import { rankStations } from "@/lib/scoring";
import { getLocalizedStations } from "@/lib/stations";
import { isWeightPreset, PRESET_WEIGHTS, WEIGHT_PRESETS, type WeightPreset } from "@/lib/weights";

/** 既定の検索条件。指定がなければこれで結果を出す（空の入力フォームを見せない）。 */
const DEFAULTS = {
  rentType: "oneLDK" as RentType,
  maxRent: 170000,
  maxMinutes: 40,
  maxTransfers: 1,
  preset: "balanced" as WeightPreset,
};

function isOfficeHub(value: string): value is OfficeHub {
  return (OFFICE_HUBS as readonly string[]).includes(value);
}

function isRentType(value: string): value is RentType {
  return (RENT_TYPES as readonly string[]).includes(value);
}

function toInt(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : fallback;
}

export function generateStaticParams() {
  return ACTIVE_LOCALES.flatMap((locale) =>
    OFFICE_HUBS.map((office) => ({ locale, office })),
  );
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; office: string }>;
}): Promise<Metadata> {
  const { locale, office } = await params;
  if (!isActiveLocale(locale) || !isOfficeHub(office)) return {};
  const dict = getDictionary(locale);
  const officeName = dict.offices[office];

  return {
    title:
      locale === "ja"
        ? `${officeName}勤務なら、どこに住むべきか`
        : `Best places to live if you work in ${officeName}`,
    description: dict.find.lead,
    alternates: { canonical: `/${locale}/work/${office}` },
  };
}

type SearchParams = {
  rentType?: string;
  maxRent?: string;
  maxMinutes?: string;
  maxTransfers?: string;
  view?: string;
};

export default async function WorkPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; office: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { locale, office } = await params;
  if (!isActiveLocale(locale) || !isOfficeHub(office)) notFound();

  const query = await searchParams;
  const dict = getDictionary(locale);

  const rentType =
    query.rentType && isRentType(query.rentType) ? query.rentType : DEFAULTS.rentType;
  const maxRent = toInt(query.maxRent, DEFAULTS.maxRent);
  const maxMinutes = toInt(query.maxMinutes, DEFAULTS.maxMinutes);
  const maxTransfers = Number.isFinite(Number(query.maxTransfers))
    ? Math.max(0, Math.floor(Number(query.maxTransfers)))
    : DEFAULTS.maxTransfers;
  const preset =
    query.view && isWeightPreset(query.view) ? query.view : DEFAULTS.preset;

  const stations = getLocalizedStations(locale);
  const results = rankStations(stations, {
    office,
    maxRent,
    rentType,
    maxMinutes,
    maxTransfers,
    weights: PRESET_WEIGHTS[preset],
  });

  const officeName = dict.offices[office];
  const hasSeedData = stations.some((s) => s.dataQuality === "seed");

  const link = (overrides: Partial<Record<keyof SearchParams, string>>) => {
    const next = new URLSearchParams({
      rentType,
      maxRent: String(maxRent),
      maxMinutes: String(maxMinutes),
      maxTransfers: String(maxTransfers),
      view: preset,
      ...overrides,
    });
    return `/${locale}/work/${office}?${next.toString()}`;
  };

  const chip = (active: boolean) =>
    active
      ? "rounded-full bg-accent px-3 py-1.5 text-sm font-medium text-white"
      : "rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-ink-soft hover:border-accent hover:text-accent";

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">
          {locale === "ja"
            ? `${officeName}勤務なら、どこに住むべきか`
            : `Where to live if you work in ${officeName}`}
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-ink-soft">{dict.find.lead}</p>
      </header>

      {hasSeedData && <SeedNotice dict={dict} />}

      {/* 条件は全て URL に載せる。共有でき、SEO 上も条件別ページとして扱える。 */}
      <form className="space-y-4 rounded-lg border border-line bg-surface p-5">
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">{dict.find.office}</legend>
          <div className="flex flex-wrap gap-2">
            {OFFICE_HUBS.map((o) => (
              <Link
                key={o}
                href={`/${locale}/work/${o}?${new URLSearchParams({
                  rentType,
                  maxRent: String(maxRent),
                  maxMinutes: String(maxMinutes),
                  maxTransfers: String(maxTransfers),
                  view: preset,
                }).toString()}`}
                className={chip(o === office)}
              >
                {dict.offices[o]}
              </Link>
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">{dict.find.rentType}</legend>
          <div className="flex flex-wrap gap-2">
            {RENT_TYPES.map((t) => (
              <Link key={t} href={link({ rentType: t })} className={chip(t === rentType)}>
                {dict.rentTypes[t]}
              </Link>
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">{dict.find.maxRent}</legend>
          <div className="flex flex-wrap gap-2">
            {[100000, 130000, 150000, 170000, 200000, 250000, 350000].map((v) => (
              <Link key={v} href={link({ maxRent: String(v) })} className={chip(v === maxRent)}>
                {formatYen(v, locale)}
              </Link>
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">{dict.find.maxMinutes}</legend>
          <div className="flex flex-wrap gap-2">
            {[15, 20, 30, 40, 60].map((v) => (
              <Link
                key={v}
                href={link({ maxMinutes: String(v) })}
                className={chip(v === maxMinutes)}
              >
                {v} {dict.station.minutes}
              </Link>
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">{dict.find.maxTransfers}</legend>
          <div className="flex flex-wrap gap-2">
            {[0, 1, 2].map((v) => (
              <Link
                key={v}
                href={link({ maxTransfers: String(v) })}
                className={chip(v === maxTransfers)}
              >
                {v === 0 ? dict.station.noTransfer : `${v}`}
              </Link>
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">{dict.find.priority}</legend>
          <div className="flex flex-wrap gap-2">
            {WEIGHT_PRESETS.map((p) => (
              <Link key={p} href={link({ view: p })} className={chip(p === preset)}>
                {dict.presets[p]}
              </Link>
            ))}
          </div>
        </fieldset>
      </form>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-ink">
          {dict.find.results}（{results.length}）
        </h2>

        {results.length === 0 ? (
          <p className="rounded-md border border-line bg-surface px-5 py-6 text-sm leading-relaxed text-ink-soft">
            {dict.find.noResults}
          </p>
        ) : (
          <ol className="space-y-3">
            {results.map((result, index) => {
              const station = result.station as (typeof stations)[number];
              return (
                <li key={station.slug}>
                  <Link
                    href={`/${locale}/stations/${station.slug}`}
                    className="block rounded-lg border border-line bg-surface p-5 transition hover:border-accent hover:shadow-sm"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                      <h3 className="text-lg font-semibold text-ink">
                        <span className="mr-2 text-ink-soft">{index + 1}.</span>
                        {station.content.name}
                      </h3>
                      <span className="text-sm tabular-nums text-ink-soft">
                        {dict.find.fit}{" "}
                        <strong className="text-ink">{result.fit}%</strong>
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-ink-soft">{station.content.tagline}</p>

                    <p className="mt-3 text-sm tabular-nums text-ink-soft">
                      {officeName} {result.minutes} {dict.station.minutes}
                      {" · "}
                      {result.transfers === 0
                        ? dict.station.noTransfer
                        : `${dict.station.transfers} ${result.transfers}`}
                      {" · "}
                      {dict.rentTypes[rentType]} {formatYen(result.rent, locale)}
                    </p>

                    {/* なぜ推すのか / 弱点を必ず添える（docs/01-requirements.md F5）。 */}
                    <dl className="mt-3 grid gap-1 text-sm sm:grid-cols-2">
                      <div className="flex gap-2">
                        <dt className="shrink-0 text-ink-soft">{dict.find.why}:</dt>
                        <dd className="text-ink">
                          {result.strengths.map((axis) => dict.axes[axis]).join(" · ")}
                        </dd>
                      </div>
                      <div className="flex gap-2">
                        <dt className="shrink-0 text-ink-soft">{dict.find.weakness}:</dt>
                        <dd className="text-ink">
                          {result.weaknesses.map((axis) => dict.axes[axis]).join(" · ")}
                        </dd>
                      </div>
                    </dl>
                  </Link>
                </li>
              );
            })}
          </ol>
        )}
      </section>
    </div>
  );
}
