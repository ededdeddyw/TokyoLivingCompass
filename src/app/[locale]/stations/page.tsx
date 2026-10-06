import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SegmentPicker } from "@/components/SegmentPicker";
import { SeedNotice } from "@/components/SeedNotice";
import { StationCard } from "@/components/StationCard";
import { getDictionary } from "@/lib/dictionaries";
import { standardMetadata } from "@/lib/seo";
import { ACTIVE_LOCALES, isActiveLocale } from "@/lib/i18n";
import { rankBySegment } from "@/lib/scoring";
import { getLocalizedStations } from "@/lib/stations";
import { isWeightPreset, type WeightPreset } from "@/lib/weights";

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
  return standardMetadata({
    locale,
    siteName: dict.siteName,
    title: dict.list.heading,
    description: dict.home.lead,
    path: (l) => `/${l}/stations`,
  });
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
  // 区分が重く見る軸が下位3割に入る駅は後ろへ回す（docs/14-audience-segments.md §3.1）。
  // スコア未測定の駅は順位が付けられないので、さらに後ろにまとめる。
  const stations = rankBySegment(getLocalizedStations(locale), preset);
  const gatedCount = stations.filter(({ gatedBy }) => gatedBy.length > 0).length;

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

      {/* 区分を変えるとランキングが変わる（docs/14-audience-segments.md §3）。
          状態は URL に載せて共有可能にする。 */}
      <SegmentPicker
        preset={preset}
        dict={dict}
        title={dict.list.perspective}
        href={(key) =>
          key === "balanced" ? `/${locale}/stations` : `/${locale}/stations?view=${key}`
        }
      />

      {gatedCount > 0 && (
        <p className="text-xs text-ink-soft">{dict.list.gateNote}</p>
      )}

      <ol className="grid gap-4 sm:grid-cols-2">
        {stations.map(({ station, overall }, index) => (
          <li key={station.slug}>
            <StationCard
              station={station}
              locale={locale}
              dict={dict}
              overall={overall}
              preset={preset}
              footnote={`#${index + 1}`}
            />
          </li>
        ))}
      </ol>
    </div>
  );
}
