import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { RentBands } from "@/components/RentBands";
import { RentHistoryTable } from "@/components/RentHistoryTable";
import { RentSourceNote } from "@/components/RentSourceNote";
import { ScoreGrid } from "@/components/ScoreGrid";
import { StationDepth } from "@/components/StationDepth";
import { SeedNotice } from "@/components/SeedNotice";
import { getDictionary } from "@/lib/dictionaries";
import { formatYen } from "@/lib/format";
import { ACTIVE_LOCALES, isActiveLocale, type ActiveLocale } from "@/lib/i18n";
import {
  absoluteUrl,
  jsonLdScript,
  languageAlternates,
  openGraph,
  pageDescription,
  pageTitle,
} from "@/lib/seo";
import { OFFICE_HUBS, RENT_TYPES } from "@/lib/schema";
import { overallScoreForPreset } from "@/lib/scoring";
import {
  getLocalizedStation,
  getLocalizedStations,
  getStationContent,
  resolveLines,
} from "@/lib/stations";

/** そのロケールでコンテンツがある駅だけを生成する（docs/04-i18n.md §5）。 */
export function generateStaticParams() {
  return ACTIVE_LOCALES.flatMap((locale) =>
    getLocalizedStations(locale).map((station) => ({ locale, slug: station.slug })),
  );
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  if (!isActiveLocale(locale)) return {};
  const station = getLocalizedStation(slug, locale);
  if (!station) return {};

  const dict = getDictionary(locale);
  // 存在するロケールのみ hreflang に出す（docs/04-i18n.md §4）。
  const languages = languageAlternates(
    (l) => `/${l}/stations/${slug}`,
    (l) => Boolean(getStationContent(slug, l)),
  );
  const path = `/${locale}/stations/${slug}`;
  // 見出しは駅名から始める。検索結果で先頭が切られると、どの駅の話か分からなくなる。
  // tagline をそのまま載せると長すぎて途中で切られるので、短い定型に置き換える。
  const title = pageTitle(dict.seoStationTitle.replace("{name}", station.content.name));
  const description = pageDescription(station.content.summary);

  return {
    title,
    description,
    alternates: { canonical: path, languages },
    openGraph: openGraph({ locale, title, description, path, siteName: dict.siteName }),
    twitter: { card: "summary", title, description },
    // seed データは検索結果に出さない（docs/05-seo.md §3）。
    robots: station.dataQuality === "seed" ? { index: false, follow: true } : undefined,
  };
}

/**
 * 構造化データ（docs/05-seo.md §4）。
 *
 * 検索エンジンと生成AIに、このページが「どの場所の、何についての記述か」を
 * 機械可読な形で渡す。本文に書いてあることだけを出し、ここだけの主張は作らない。
 */
function stationJsonLd(
  station: NonNullable<ReturnType<typeof getLocalizedStation>>,
  locale: ActiveLocale,
  dict: ReturnType<typeof getDictionary>,
  lineNames: string[],
) {
  const path = `/${locale}/stations/${station.slug}`;
  const place = {
    "@type": "TrainStation",
    "@id": `${absoluteUrl(path)}#station`,
    name: station.content.name,
    alternateName: station.nameRomaji,
    url: absoluteUrl(path),
    geo: {
      "@type": "GeoCoordinates",
      latitude: station.lat,
      longitude: station.lon,
    },
    address: {
      "@type": "PostalAddress",
      addressCountry: "JP",
      addressRegion: "Tokyo",
      addressLocality: station.wardNameJa,
    },
    ...(lineNames.length > 0 ? { containedInPlace: lineNames.join(", ") } : {}),
  };

  const breadcrumb = {
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: dict.siteName,
        item: absoluteUrl(`/${locale}`),
      },
      {
        "@type": "ListItem",
        position: 2,
        name: dict.list.heading,
        item: absoluteUrl(`/${locale}/stations`),
      },
      { "@type": "ListItem", position: 3, name: station.content.name },
    ],
  };

  const article = {
    "@type": "Article",
    headline: pageTitle(dict.seoStationTitle.replace("{name}", station.content.name)),
    description: pageDescription(station.content.summary),
    inLanguage: locale,
    about: { "@id": `${absoluteUrl(path)}#station` },
    isAccessibleForFree: true,
    ...(station.lastReviewedAt ? { dateModified: station.lastReviewedAt } : {}),
  };

  return { "@context": "https://schema.org", "@graph": [place, breadcrumb, article] };
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}

export default async function StationPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  if (!isActiveLocale(locale)) notFound();

  const station = getLocalizedStation(slug, locale);
  if (!station) notFound();

  const dict = getDictionary(locale);
  const overall = overallScoreForPreset(station, "balanced");
  const crowding =
    station.morningCrowding === undefined
      ? dict.dataQuality.notAvailable
      : dict.crowdingLevels[station.morningCrowding as 1 | 2 | 3 | 4 | 5];

  // 近くの駅と迷いやすい駅の表示名を先に解決しておく
  // （コンポーネント側でデータを取りに行かせない）。
  const neighbourNames: Record<string, string> = {};
  for (const n of [
    ...(station.content.neighbours ?? []),
    ...(station.content.alternatives ?? []),
  ]) {
    const other = getLocalizedStation(n.slug, locale);
    if (other) neighbourNames[n.slug] = other.content.name;
  }

  const similar = station.similarStations
    .map((s) => getLocalizedStation(s, locale as ActiveLocale))
    .filter((s): s is NonNullable<typeof s> => s !== null);

  const lineNames = resolveLines(station.lineIds).map((l) =>
    locale === "ja" ? l.nameJa : l.nameEn,
  );

  return (
    <article className="space-y-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={jsonLdScript(
          stationJsonLd(station, locale, dict, lineNames),
        )}
      />
      <header className="space-y-3">
        <p className="text-sm text-ink-soft">
          {station.wardNameJa} · {lineNames.join(" / ")}
        </p>
        <h1 className="text-3xl font-bold text-ink">
          {station.content.name}
          {locale !== "ja" && (
            <span className="ml-3 text-xl font-normal text-ink-soft">{station.nameJa}</span>
          )}
        </h1>
        {/* 別名で探した人に、ここが同じ駅だと分かるようにする。 */}
        {station.alsoKnownAs && station.alsoKnownAs.length > 0 && (
          <p className="text-sm text-ink-soft">
            {dict.station.alsoKnownAs.replace(
              "{names}",
              station.alsoKnownAs.map((n) => `${n}駅`).join("・"),
            )}
          </p>
        )}
        {station.content.tags && station.content.tags.length > 0 && (
          // 街の性格タグ。本文を読む前に、どんな街かを掴めるようにする。
          <ul className="flex flex-wrap gap-1.5">
            {station.content.tags.map((tag) => (
              <li
                key={tag}
                className="rounded-full border border-line px-2.5 py-0.5 text-xs text-ink-soft"
              >
                {dict.tags[tag]}
              </li>
            ))}
          </ul>
        )}
        <p className="text-lg text-ink-soft">{station.content.tagline}</p>
        <p className="text-sm text-ink-soft">
          {dict.station.overall}{" "}
          <strong className="text-2xl tabular-nums text-ink">
            {overall === null ? dict.dataQuality.notAvailable : overall.toFixed(1)}
          </strong>
          {overall !== null && <span className="text-ink-soft"> / 10</span>}
        </p>
      </header>

      {station.dataQuality === "seed" && <SeedNotice dict={dict} />}

      <p className="max-w-3xl leading-relaxed text-ink">{station.content.summary}</p>

      <Section title={dict.station.rent}>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {RENT_TYPES.map((type) => (
            <div key={type} className="rounded-md border border-line bg-surface p-4">
              <dt className="text-sm text-ink-soft">{dict.rentTypes[type]}</dt>
              <dd className="mt-1 tabular-nums text-ink">
                {station.rent ? (
                  <>
                    {formatYen(station.rent[type], locale)}
                    <span className="text-sm text-ink-soft">{dict.station.perMonth}</span>
                  </>
                ) : (
                  dict.dataQuality.notAvailable
                )}
              </dd>
            </div>
          ))}
        </dl>
        <RentSourceNote source={station.sources?.rent} dict={dict} />
      </Section>

      {station.rentBands && (
        <Section title={dict.rentBands.title}>
          <RentBands data={station.rentBands} dict={dict} />
        </Section>
      )}

      {station.rentHistory && (
        <Section title={dict.rentHistory.title}>
          <RentHistoryTable history={station.rentHistory} dict={dict} />
        </Section>
      )}

      <Section title={dict.station.commute}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[28rem] border-collapse text-sm">
            <tbody>
              {OFFICE_HUBS.map((office) => {
                const c = station.commutes.find((x) => x.to === office);
                if (!c) return null;
                return (
                  <tr key={office} className="border-b border-line">
                    <th scope="row" className="py-2 text-left font-normal text-ink">
                      {dict.offices[office]}
                    </th>
                    <td className="py-2 text-right tabular-nums text-ink">
                      {c.minutes} {dict.station.minutes}
                    </td>
                    <td className="w-28 py-2 text-right text-ink-soft">
                      {c.transfers === 0
                        ? dict.station.noTransfer
                        : `${dict.station.transfers} ${c.transfers}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-sm text-ink-soft">
          {dict.station.firstTrain}:{" "}
          {station.hasFirstTrain === undefined
            ? dict.dataQuality.notAvailable
            : station.hasFirstTrain
              ? dict.station.yes
              : dict.station.no}
          {" · "}
          {dict.station.crowding}: {crowding}
        </p>
        <p className="text-sm leading-relaxed text-ink-soft">{dict.commuteNote}</p>
      </Section>

      <Section title={dict.station.scores}>
        {Object.keys(station.scores).length === 0 ? (
          <p className="text-sm text-ink-soft">{dict.dataQuality.noScoresYet}</p>
        ) : (
          <ScoreGrid scores={station.scores} dict={dict} />
        )}
      </Section>

      <div className="grid gap-8 sm:grid-cols-2">
        <Section title={dict.station.goodFor}>
          <ul className="space-y-2 text-ink">
            {station.content.goodFor.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden="true" className="text-accent">
                  ◎
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Section>
        <Section title={dict.station.notFor}>
          <ul className="space-y-2 text-ink">
            {station.content.notFor.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden="true" className="text-[#9a3b3b]">
                  ×
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Section>
      </div>

      <StationDepth
        content={station.content}
        dict={dict}
        neighbourNames={neighbourNames}
      />

      {station.content.residentComment && (
        <Section
          title={
            station.content.residentCommentBy === "compiled"
              ? dict.station.compiledComment
              : dict.station.residentComment
          }
        >
          <blockquote className="rounded-md border-l-4 border-accent bg-accent-soft px-5 py-4 leading-relaxed text-ink">
            {station.content.residentComment}
          </blockquote>
          {station.content.residentCommentBy === "compiled" && (
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              {dict.station.compiledCommentNote}
              {station.content.residentCommentSources &&
                station.content.residentCommentSources.length > 0 && (
                  <>
                    {" "}
                    {dict.station.compiledCommentSources}:{" "}
                    {station.content.residentCommentSources.map((src, i) => (
                      <span key={src.url}>
                        {i > 0 && "、"}
                        <a
                          href={src.url}
                          rel="nofollow noopener"
                          target="_blank"
                          className="underline underline-offset-2"
                        >
                          {src.name}
                        </a>
                      </span>
                    ))}
                  </>
                )}
            </p>
          )}
        </Section>
      )}

      {station.facilities && (
        <Section title={dict.station.facilities}>
          <dl className="space-y-2 text-sm">
            <div className="flex gap-3">
              <dt className="w-28 shrink-0 text-ink-soft">{dict.station.supermarkets}</dt>
              <dd className="text-ink">{station.facilities.supermarkets.join(" · ")}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-28 shrink-0 text-ink-soft">{dict.station.commercial}</dt>
              <dd className="text-ink">{station.facilities.commercial.join(" · ")}</dd>
            </div>
          </dl>
          {station.facilities.notes && (
            <p className="text-sm leading-relaxed text-ink-soft">
              {station.facilities.notes}
            </p>
          )}
        </Section>
      )}

      {similar.length > 0 && (
        <Section title={dict.station.similar}>
          <ul className="flex flex-wrap gap-3">
            {similar.map((s) => (
              <li key={s.slug} className="flex flex-wrap items-center gap-2">
                <Link
                  href={`/${locale}/stations/${s.slug}`}
                  className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm text-ink hover:border-accent"
                >
                  {s.content.name}
                </Link>
                <Link
                  href={`/${locale}/compare/${station.slug}-vs-${s.slug}`}
                  className="text-sm text-accent hover:underline"
                >
                  {dict.compare.heading}
                </Link>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <p>
        <Link href={`/${locale}/stations`} className="text-sm text-accent hover:underline">
          ← {dict.station.backToList}
        </Link>
      </p>
    </article>
  );
}
