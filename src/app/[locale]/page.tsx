import Link from "next/link";
import { notFound } from "next/navigation";

import { SeedNotice } from "@/components/SeedNotice";
import { StationCard } from "@/components/StationCard";
import { getDictionary } from "@/lib/dictionaries";
import { ACTIVE_LOCALES, isActiveLocale } from "@/lib/i18n";
import { overallScoreForPreset } from "@/lib/scoring";
import { getLocalizedStations } from "@/lib/stations";

export function generateStaticParams() {
  return ACTIVE_LOCALES.map((locale) => ({ locale }));
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isActiveLocale(locale)) notFound();

  const dict = getDictionary(locale);
  const stations = getLocalizedStations(locale);
  const hasSeedData = stations.some((s) => s.dataQuality === "seed");

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <h1 className="text-3xl font-bold leading-tight text-ink sm:text-4xl">
          {dict.tagline}
        </h1>
        <p className="max-w-2xl leading-relaxed text-ink-soft">{dict.home.lead}</p>
        <div className="flex flex-wrap gap-3 pt-1">
          <Link
            href={`/${locale}/work/toranomon`}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            {dict.home.findCta}
          </Link>
          <Link
            href={`/${locale}/stations`}
            className="rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink hover:border-accent"
          >
            {dict.home.browseCta}
          </Link>
        </div>
      </section>

      {hasSeedData && <SeedNotice dict={dict} />}

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-ink">
          {dict.home.featuredHeading}（{stations.length}
          {locale === "ja" ? dict.list.count : ` ${dict.list.count}`}）
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {stations.map((station) => (
            <StationCard
              key={station.slug}
              station={station}
              locale={locale}
              dict={dict}
              overall={overallScoreForPreset(station, "balanced")}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
