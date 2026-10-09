import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  ChevronDown,
  CircleCheck,
  CircleX,
  MapPin,
  Star,
  ThumbsDown,
  ThumbsUp,
  TrainFront,
} from "lucide-react";

import { CommuteBars } from "@/components/station/CommuteBars";
import { KeyFacts, type KeyFact } from "@/components/station/KeyFacts";
import { ScoreHighlights } from "@/components/station/ScoreHighlights";
import { SectionNav } from "@/components/station/SectionNav";
import { RentBands } from "@/components/RentBands";
import { RentHistoryTable } from "@/components/RentHistoryTable";
import { RentSourceNote } from "@/components/RentSourceNote";
import { OverallScore } from "@/components/OverallScore";
import { ScoreGrid } from "@/components/ScoreGrid";
import { StationDepth } from "@/components/StationDepth";
import { SeedNotice } from "@/components/SeedNotice";
import { TownTraits } from "@/components/TownTraits";
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
import { WEIGHT_PRESETS, type WeightPreset } from "@/lib/weights";
import {
  getLocalizedStation,
  getLocalizedStations,
  getStationContent,
  getTownTraits,
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

function Section({
  id,
  title,
  children,
}: {
  id?: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="space-y-4">
      <h2 className="text-xl font-bold text-ink">{title}</h2>
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
  const townTraits = getTownTraits(slug, locale);
  // 総合評価は読み手の区分ごとに変わる。一覧から区分つきのリンクで来た読み手に
  // 別の数字を見せないよう、区分ごとの点数をすべて渡しておく
  // （src/components/OverallScore.tsx）。
  const overallByPreset = Object.fromEntries(
    WEIGHT_PRESETS.map((preset) => [preset, overallScoreForPreset(station, preset)]),
  ) as Record<WeightPreset, number | null>;
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

  // 冒頭の要点。家賃は1Kの帯（無ければワンルーム）、通勤はいちばん近いオフィス街
  const ui = dict.stationUi;
  const rentType = station.rentBands?.bands.oneK
    ? "oneK"
    : station.rentBands?.bands.oneRoom
      ? "oneRoom"
      : null;
  const nearest = [...station.commutes].sort((x, y) => x.minutes - y.minutes)[0];
  const keyFacts: KeyFact[] = [];
  if (rentType && station.rentBands) {
    const b = station.rentBands.bands[rentType]!;
    keyFacts.push({
      icon: "rent",
      label: ui.keyRent.replace(ui.keyRentType, dict.rentTypes[rentType]),
      value: dict.rentBands.band
        .replace("{low}", (b.low / 10000).toFixed(0))
        .replace("{high}", (b.high / 10000).toFixed(0)),
      href: "#rent",
    });
  }
  if (nearest) {
    keyFacts.push({
      icon: "commute",
      label: ui.keyNearest,
      value: ui.keyNearestValue
        .replace("{hub}", dict.offices[nearest.to])
        .replace("{minutes}", String(nearest.minutes)),
      href: "#commute",
    });
  }
  keyFacts.push({
    icon: "lines",
    label: ui.keyLines,
    value: ui.keyLinesValue.replace("{count}", String(lineNames.length)),
    href: "#commute",
  });
  const navItems = [
    ...(townTraits ? [{ id: "traits", label: ui.nav.traits }] : []),
    { id: "rent", label: ui.nav.rent },
    { id: "commute", label: ui.nav.commute },
    { id: "scores", label: ui.nav.scores },
    { id: "life", label: ui.nav.life },
    { id: "compare", label: ui.nav.compare },
  ];

  return (
    <article className="space-y-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={jsonLdScript(
          stationJsonLd(station, locale, dict, lineNames),
        )}
      />
      <header className="overflow-hidden rounded-3xl bg-gradient-to-br from-accent-strong via-accent to-accent-bright p-6 text-white shadow-md sm:p-8">
        <p className="flex flex-wrap items-center gap-1.5 text-xs text-white/90">
          <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1">
            <MapPin aria-hidden="true" className="size-3.5" />
            {station.wardNameJa}
          </span>
          {lineNames.map((l) => (
            <span key={l} className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1">
              <TrainFront aria-hidden="true" className="size-3.5" />
              {l}
            </span>
          ))}
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
          {station.content.name}
          {locale !== "ja" && (
            <span className="ml-3 text-xl font-normal text-white/80">{station.nameJa}</span>
          )}
        </h1>
        {/* 別名で探した人に、ここが同じ駅だと分かるようにする。 */}
        {station.alsoKnownAs && station.alsoKnownAs.length > 0 && (
          <p className="mt-2 text-sm text-white/85">
            {dict.station.alsoKnownAs.replace(
              "{names}",
              station.alsoKnownAs.map((n) => `${n}駅`).join("・"),
            )}
          </p>
        )}
        <p className="mt-4 max-w-3xl text-base leading-relaxed text-white sm:text-lg">
          {station.content.tagline}
        </p>
        {station.content.tags && station.content.tags.length > 0 && (
          // 街の性格タグ。本文を読む前に、どんな街かを掴めるようにする。
          <ul className="mt-4 flex flex-wrap gap-1.5">
            {station.content.tags.map((tag) => (
              <li
                key={tag}
                className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-xs font-semibold text-accent-strong"
              >
                <Star aria-hidden="true" className="size-3 fill-sun text-sun" />
                {dict.tags[tag]}
              </li>
            ))}
          </ul>
        )}
      </header>

      <KeyFacts
        facts={keyFacts}
        extra={
          <OverallScore
            scores={overallByPreset}
            labels={{
              overall: dict.station.overall,
              notAvailable: dict.dataQuality.notAvailable,
              balanced: dict.station.overallBalanced,
              segment: dict.station.overallSegment,
              options: dict.segmentOptions,
            }}
          />
        }
      />

      <SectionNav label={dict.stationUi.nav.traits} items={navItems} />

      {station.dataQuality === "seed" && <SeedNotice dict={dict} />}

      <p className="max-w-3xl text-[17px] leading-loose text-ink">{station.content.summary}</p>

      {townTraits && <TownTraits data={townTraits} dict={dict} />}

      <Section id="rent" title={dict.station.rent}>
        {station.rentBands ? (
          <RentBands data={station.rentBands} dict={dict} locale={locale} />
        ) : (
          <>
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {RENT_TYPES.map((type) => (
                <div key={type} className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
                  <dt className="inline-block rounded-md bg-accent-soft px-2 py-0.5 text-xs font-semibold text-accent-strong">
                    {dict.rentTypes[type]}
                  </dt>
                  <dd className="mt-2 text-lg font-bold tabular-nums text-ink">
                    {station.rent ? (
                      <>
                        {formatYen(station.rent[type], locale)}
                        <span className="text-sm font-normal text-ink-soft">
                          {dict.station.perMonth}
                        </span>
                      </>
                    ) : (
                      dict.dataQuality.notAvailable
                    )}
                  </dd>
                </div>
              ))}
            </dl>
            <RentSourceNote source={station.sources?.rent} dict={dict} />
          </>
        )}
        {/* 家賃がこの水準である理由は、相場の数字のすぐ下に置く。
            ページの後半に離して置くと、数字と理由を読み手が自分でつなぐことになる。 */}
        {station.content.rentReason && (
          <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
            <h3 className="text-base font-bold text-ink">{dict.depth.rentReason}</h3>
            {station.content.leads?.rentReason && (
              <p className="mt-3 border-l-4 border-sun pl-3 text-[15px] font-semibold leading-relaxed text-ink">
                {station.content.leads.rentReason}
              </p>
            )}
            <p className="mt-3 text-[15px] leading-loose text-ink-soft">
              {station.content.rentReason}
            </p>
          </div>
        )}
        {station.rentHistory && (
          <div className="space-y-2">
            <h3 className="text-base font-bold text-ink">{dict.rentHistory.title}</h3>
            <RentHistoryTable history={station.rentHistory} dict={dict} />
          </div>
        )}
      </Section>

      <Section id="commute" title={dict.station.commute}>
        <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
          <CommuteBars commutes={station.commutes} dict={dict} />
        </div>
        {/* 始発と朝の混み方は、データがある駅だけで出す。「—」を並べても読み手に何も渡せない */}
        {(station.hasFirstTrain !== undefined || station.morningCrowding !== undefined) && (
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
        )}
        <p className="text-xs leading-relaxed text-ink-soft">{dict.commuteNote}</p>
      </Section>

      <Section id="scores" title={dict.station.scores}>
        {Object.keys(station.scores).length === 0 ? (
          <p className="text-sm text-ink-soft">{dict.dataQuality.noScoresYet}</p>
        ) : (
          <>
            <ScoreHighlights scores={station.scores} dict={dict} />
            <details className="group rounded-2xl border border-line bg-surface p-5 shadow-sm">
              <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-bold text-accent">
                {dict.stationUi.allScores}
                <ChevronDown
                  aria-hidden="true"
                  className="size-4 transition group-open:rotate-180"
                />
              </summary>
              <div className="mt-3">
                <ScoreGrid scores={station.scores} dict={dict} />
                <p className="mt-3 text-xs leading-relaxed text-ink-soft">
                  {dict.stationUi.neutralNote}
                </p>
              </div>
            </details>
          </>
        )}
      </Section>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="rounded-2xl border border-good/30 bg-good-soft p-5">
          <h2 className="flex items-center gap-2 text-lg font-bold text-good">
            <ThumbsUp aria-hidden="true" className="size-5" />
            {dict.station.goodFor}
          </h2>
          <ul className="mt-3 space-y-2.5 text-[15px] leading-relaxed text-ink">
            {station.content.goodFor.map((item) => (
              <li key={item} className="flex gap-2">
                <CircleCheck aria-hidden="true" className="mt-1 size-4 shrink-0 text-good" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-2xl border border-bad/30 bg-bad-soft p-5">
          <h2 className="flex items-center gap-2 text-lg font-bold text-bad">
            <ThumbsDown aria-hidden="true" className="size-5" />
            {dict.station.notFor}
          </h2>
          <ul className="mt-3 space-y-2.5 text-[15px] leading-relaxed text-ink">
            {station.content.notFor.map((item) => (
              <li key={item} className="flex gap-2">
                <CircleX aria-hidden="true" className="mt-1 size-4 shrink-0 text-bad" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <StationDepth
        content={station.content}
        dict={dict}
        neighbourNames={neighbourNames}
        locale={locale}
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
