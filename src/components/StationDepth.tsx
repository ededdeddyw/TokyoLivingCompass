import {
  Building2,
  CalendarDays,
  ChevronDown,
  Clock,
  Sun,
  DoorOpen,
  GitCompareArrows,
  HeartPulse,
  House,
  Moon,
  Mountain,
  Baby,
  ShoppingBasket,
  Sunrise,
  TrainFront,
  TrendingUp,
  Users,
  Volume2,
  Wallet,
  Waves,
  type LucideIcon,
  ExternalLink,
} from "lucide-react";

import Link from "next/link";

import type { Dictionary } from "@/lib/dictionaries";
import type { StationContent, WardLinks } from "@/lib/schema";

/**
 * 「住むと分かること」の表示（docs/12-quality-standard.md）。
 * 既存の不動産まとめ記事が書いていない項目を、ここでまとめて出す。
 * 未記入の項目は表示しない。空欄を並べても価値がないため。
 */

/**
 * 節ひとつ。lead は「一言でいうと」で、本文を読む前に結論だけを受け取れるようにする
 * （docs/12-quality-standard.md）。入っていない節では出さない。
 */
function Block({
  icon,
  title,
  lead,
  source,
  children,
  more,
  wide = false,
  footer,
}: {
  /** 畳んだ本文の外に、いつも見える形で置くもの（区の公式ページへのリンクなど） */
  footer?: React.ReactNode;
  /** 2列に並べたときに、横幅いっぱいを使う。朝・昼・夜・週末のように並べて読む節に使う。 */
  wide?: boolean;
  /**
   * 本文を「続きを読む」で畳むときの文言。一言（lead）があるときだけ畳む。
   * スマホで長い本文が十数枚続くと、目当ての節にたどり着けない。
   * 畳んでも本文は HTML に残るので、検索にも読み上げにも届く。
   */
  more?: string;
  /** ICONS のキー。節の種類 */
  icon: string;
  title: string;
  lead?: string;
  /** 出典。どう測ったかの説明は本文に書かず、ここにリンクだけ置く。 */
  source?: { label: string; name: string; url: string };
  children: React.ReactNode;
}) {
  const Icon = ICONS[icon] ?? House;
  return (
    <section
      className={`rounded-2xl border border-line bg-surface p-5 shadow-sm ${wide ? "lg:col-span-2" : ""}`}
    >
      <h3 className="flex items-center gap-2 text-base font-bold text-ink">
        <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-accent">
          <Icon aria-hidden="true" className="size-4" />
        </span>
        {title}
      </h3>
      {lead && (
        <p className="mt-3 border-l-4 border-sun pl-3 text-[15px] font-semibold leading-relaxed text-ink">
          {lead}
        </p>
      )}
      {more && lead ? (
        <details className="group mt-2">
          <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-sm font-semibold text-accent">
            {more}
            <ChevronDown aria-hidden="true" className="size-4 transition group-open:rotate-180" />
          </summary>
          <div className="mt-2 text-[15px] leading-loose text-ink-soft">{children}</div>
        </details>
      ) : (
        <div className="mt-3 text-[15px] leading-loose text-ink-soft">{children}</div>
      )}
      {footer}
      {source && (
        <p className="mt-3 text-xs text-ink-soft">
          {source.label}:{" "}
          <a
            href={source.url}
            className="text-accent hover:underline"
            rel="noreferrer"
            target="_blank"
          >
            {source.name}
          </a>
        </p>
      )}
    </section>
  );
}

/** 節ごとのアイコン。文字を読む前に、どの話かを見分けられるようにする。 */
const ICONS: Record<string, LucideIcon> = {
  faces: Clock,
  terrain: Mountain,
  groceries: ShoppingBasket,
  exits: DoorOpen,
  rentRange: Wallet,
  noise: Volume2,
  family: Baby,
  medical: HeartPulse,
  stationNote: TrainFront,
  congestion: Sunrise,
  nightWalk: Moon,
  residents: Users,
  housingStock: Building2,
  outlook: TrendingUp,
  hazards: Waves,
  neighbours: GitCompareArrows,
  alternatives: GitCompareArrows,
};

/** 出典のアドレス。言語によって変わらないので定数で持つ。 */
const GSI_ELEVATION_URL = "https://maps.gsi.go.jp/development/elevation_s.html";
const MLIT_CONGESTION_URL =
  "https://www.mlit.go.jp/report/press/tetsudo04_hh_000139.html";
const MLIT_HAZARD_URL = "https://disaportal.gsi.go.jp/maps/";
const OSM_URL = "https://www.openstreetmap.org/copyright";

/** 区の公式ページへのリンクの一覧。区の境の駅では、区ごとに並べる。 */
function WardLinkList({
  items,
  heading,
}: {
  items: { key: string; label: string; url: string }[];
  heading: string;
}) {
  if (items.length === 0) return null;
  return (
    <div className="mt-4 rounded-xl bg-canvas p-3.5">
      <p className="text-xs font-semibold text-ink-soft">{heading}</p>
      <ul className="mt-2 space-y-1.5">
        {items.map((it) => (
          <li key={it.key}>
            <a
              href={it.url}
              className="inline-flex items-start gap-1.5 text-sm font-medium text-accent hover:underline"
              rel="noreferrer"
              target="_blank"
            >
              <ExternalLink aria-hidden="true" className="mt-0.5 size-3.5 shrink-0" />
              {it.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function StationDepth({
  content,
  dict,
  neighbourNames,
  locale,
  wardLinks = [],
}: {
  /** 駅のまわりにかかる区の公式ページ。所在地の区が先頭 */
  wardLinks?: WardLinks[];
  content: StationContent;
  dict: Dictionary;
  locale: string;
  /** 隣接駅 slug → 表示名。解決できない駅は slug のまま出す。 */
  neighbourNames: Record<string, string>;
}) {
  const d = dict.depth;

  const blocks: React.ReactNode[] = [];
  const ui = dict.stationUi;
  const wardOnly = wardLinks.length === 1;
  const linkLabel = (tpl: string, ward: string) =>
    tpl.replace("{ward}", ward).replace(/^\s+/, "");
  const childcareLinks = wardLinks.flatMap((w) =>
    (
      [
        ["childcare", w.childcare, ui.wardChildcare],
        ["school", w.school, ui.wardSchool],
      ] as const
    ).flatMap(([kind, link, tpl]) =>
      link ? [{ key: `${w.wardCode}-${kind}`, url: link.url, label: linkLabel(tpl, w.nameJa) }] : [],
    ),
  );
  const hazardLinks = wardLinks.flatMap((w) =>
    w.hazard
      ? [{ key: `${w.wardCode}-hazard`, url: w.hazard.url, label: linkLabel(ui.wardHazard, w.nameJa) }]
      : [],
  );
  const childcareFooter = (
    <WardLinkList items={childcareLinks} heading={wardOnly ? ui.wardLinksHeading : ui.wardLinksHeadingMulti} />
  );
  const hazardFooter = (
    <WardLinkList items={hazardLinks} heading={wardOnly ? ui.wardLinksHeading : ui.wardLinksHeadingMulti} />
  );

  if (content.faces) {
    blocks.push(
      <Block key="faces" icon="faces" title={d.faces} lead={content.leads?.faces} wide>
        {/*
          4つを2列のカードにすると、半分の幅の中でさらに半分になり、1行が10字ほどで折り返して
          読みにくかった。時間の順に1列で並べ、見出しを左、本文を右に置く。
        */}
        <dl className="mt-1 divide-y divide-line">
          {(
            [
              [d.morning, content.faces.morning, Sunrise],
              [d.daytime, content.faces.daytime, Sun],
              [d.night, content.faces.night, Moon],
              [d.weekend, content.faces.weekend, CalendarDays],
            ] as const
          ).map(([label, text, Icon]) => (
            <div key={label} className="grid gap-1 py-3 sm:grid-cols-[6rem_1fr] sm:gap-4">
              <dt className="flex items-center gap-1.5 text-sm font-bold text-ink sm:items-start sm:pt-0.5">
                <Icon aria-hidden="true" className="size-4 text-sun" />
                {label}
              </dt>
              <dd className="max-w-3xl text-[15px] leading-relaxed">{text}</dd>
            </div>
          ))}
        </dl>
      </Block>,
    );
  }

  if (content.terrain) {
    blocks.push(
      <Block
        key="terrain"
        icon="terrain"
        title={d.terrain}
        lead={content.leads?.terrain}
        source={{ label: d.source, name: d.terrainSource, url: GSI_ELEVATION_URL }}
      >
        <p>
          <span className="font-medium text-ink">{d.slope[content.terrain.slope]}</span>
          {" — "}
          {content.terrain.note}
        </p>
      </Block>,
    );
  }

  if (content.groceries && content.groceries.length > 0) {
    blocks.push(
      <Block key="groceries" icon="groceries" title={d.groceries} lead={content.leads?.groceries}>
        <ul className="space-y-1.5">
          {content.groceries.map((store) => (
            <li key={store.name} className="flex flex-wrap items-baseline gap-x-2">
              <span className="font-medium text-ink">{store.name}</span>
              <span className="rounded bg-canvas px-1.5 py-0.5 text-xs">
                {d.tier[store.tier]}
              </span>
              {store.walkMinutes !== undefined && (
                <span className="text-xs tabular-nums">
                  {d.walkMinutes} {store.walkMinutes}分
                </span>
              )}
              {store.note && <span className="w-full">{store.note}</span>}
            </li>
          ))}
        </ul>
        {content.dailyShops && content.dailyShops.length > 0 && (
          <>
            <h4 className="mt-3 text-xs font-semibold text-ink">{d.dailyShops}</h4>
            <ul className="mt-1.5 space-y-1.5">
              {content.dailyShops.map((shop) => (
                <li key={shop.name} className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-medium text-ink">{shop.name}</span>
                  <span className="rounded bg-canvas px-1.5 py-0.5 text-xs">
                    {d.shopKind[shop.kind]}
                  </span>
                  {shop.walkMinutes !== undefined && (
                    <span className="text-xs tabular-nums">
                      {d.walkMinutes} {shop.walkMinutes}分
                    </span>
                  )}
                  {shop.note && <span className="w-full">{shop.note}</span>}
                </li>
              ))}
            </ul>
          </>
        )}
      </Block>,
    );
  }

  if (content.exits && content.exits.length > 0) {
    blocks.push(
      <Block key="exits" icon="exits" title={d.exits} lead={content.leads?.exits}>
        <dl className="space-y-2">
          {content.exits.map((exit) => (
            <div key={exit.name} className="flex gap-3">
              <dt className="w-28 shrink-0 font-medium text-ink">
                {exit.line && (
                  <span className="block text-xs font-normal text-ink-soft">
                    {exit.line}
                  </span>
                )}
                {exit.name}
              </dt>
              <dd>
                {exit.tags && exit.tags.length > 0 && (
                  <span className="mb-1 flex flex-wrap gap-1">
                    {exit.tags.map((t) => (
                      <span
                        key={t}
                        className="rounded bg-[#f3f4f6] px-1.5 py-0.5 text-xs text-[#5b6472]"
                      >
                        {dict.exitTags[t]}
                      </span>
                    ))}
                  </span>
                )}
                {exit.character}
              </dd>
            </div>
          ))}
        </dl>
      </Block>,
    );
  }

  if (content.rentRange) {
    blocks.push(
      <Block
        key="rentRange"
        icon="rentRange"
        title={d.rentRange}
        lead={content.leads?.rentRange}
        more={dict.stationUi.readMore}
      >
        <p>{content.rentRange.note}</p>
        <p className="mt-1.5">
          <span className="font-medium text-ink">{d.rentDrivers}: </span>
          {content.rentRange.drivers.join(" / ")}
        </p>
      </Block>,
    );
  }

  if (content.noiseSources && content.noiseSources.length > 0) {
    blocks.push(
      <Block key="noise" icon="noise" title={d.noiseSources} lead={content.leads?.noiseSources}>
        <ul className="list-disc space-y-1 pl-5">
          {content.noiseSources.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </Block>,
    );
  }

  const simple = [
    "family",
    "medical",
    "stationNote",
    // 混雑率は「駅の使い勝手」のすぐ後ろに置く。毎朝どの電車に乗るかの話なので、
    // 路線の説明を読んだ直後に見えたほうが読み手がつなげやすい。
    "congestion",
    "nightWalk",
    "residents",
    "housingStock",
    "outlook",
  ] as const;
  for (const field of simple) {
    const text = content[field];
    if (!text) continue;
    blocks.push(
      <Block
        key={field}
        icon={field}
        title={d[field]}
        lead={content.leads?.[field]}
        more={dict.stationUi.readMore}
        footer={field === "family" ? childcareFooter : undefined}
        source={
          field === "congestion"
            ? { label: d.source, name: d.congestionSource, url: MLIT_CONGESTION_URL }
            : field === "medical"
              ? { label: d.source, name: d.medicalSource, url: OSM_URL }
              : undefined
        }
      >
        <p>{text}</p>
      </Block>,
    );
  }

  // 子育ての本文がまだ無い駅でも、区の保育園と学区のページへは案内する。
  if (!content.family && childcareLinks.length > 0) {
    blocks.push(
      <Block key="family" icon="family" title={d.family}>
        <p>{ui.wardChildcareOnly}</p>
        {childcareFooter}
      </Block>,
    );
  }

  // 災害は、書き方ひとつで読み手の受け取り方が大きく変わる。
  // 浸水想定区域が何を意味するのかを毎回そえて、駅ごとの本文が単独で
  // 強く読まれないようにする。
  if (content.hazards) {
    blocks.push(
      <Block
        key="hazards"
        icon="hazards"
        title={d.hazards}
        lead={content.leads?.hazards}
        source={{ label: d.source, name: d.hazardSource, url: MLIT_HAZARD_URL }}
      >
        <p>{content.hazards}</p>
        <p className="mt-2 text-xs leading-relaxed text-ink-soft">
          {dict.hazardNote}
        </p>
        {hazardFooter}
      </Block>,
    );
  } else if (hazardLinks.length > 0) {
    blocks.push(
      <Block key="hazards" icon="hazards" title={d.hazards}>
        <p>{ui.wardHazardOnly}</p>
        {hazardFooter}
      </Block>,
    );
  }

  // 近くの駅（距離から選ぶ）と、迷いやすい駅（条件が似ていて人が選ぶ）は、
  // 読み手にとって意味が違うため、同じ節にまとめない。
  // 近くの駅（距離から選ぶ）と、迷いやすい駅（条件が似ていて人が選ぶ）は、
  // 読み手にとって意味が違うため、同じカードにまとめない。
  const compare: React.ReactNode[] = [];
  for (const field of ["neighbours", "alternatives"] as const) {
    const list = content[field];
    if (!list || list.length === 0) continue;
    compare.push(
      <Block key={field} icon={field} title={d[field]}>
        <ul className="divide-y divide-line">
          {list.map((n) => (
            <li key={n.slug} className="py-3 first:pt-0 last:pb-0">
              <Link
                href={`/${locale}/stations/${n.slug}`}
                className="inline-flex items-center rounded-full bg-accent-soft px-3 py-0.5 text-sm font-bold text-accent-strong hover:bg-accent hover:text-white"
              >
                {neighbourNames[n.slug] ?? n.slug}
              </Link>
              {/* 比較の一言。本文を読む前に、どちらが何で上回るのかを渡す。 */}
              {n.lead && (
                <p className="mt-2 font-semibold leading-relaxed text-ink">{n.lead}</p>
              )}
              {n.lead ? (
                <details className="group mt-1">
                  <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-sm font-semibold text-accent">
                    {dict.stationUi.readMore}
                    <ChevronDown
                      aria-hidden="true"
                      className="size-4 transition group-open:rotate-180"
                    />
                  </summary>
                  <p className="mt-1">{n.note}</p>
                </details>
              ) : (
                <p className="mt-1">{n.note}</p>
              )}
            </li>
          ))}
        </ul>
      </Block>,
    );
  }

  if (blocks.length === 0 && compare.length === 0) return null;

  return (
    <>
      {blocks.length > 0 && (
        <section id="life" className="space-y-4">
          <h2 className="text-xl font-bold text-ink">{d.heading}</h2>
          <div className="grid items-start gap-4 lg:grid-cols-2">{blocks}</div>
        </section>
      )}
      {compare.length > 0 && (
        <section id="compare" className="space-y-4">
          <h2 className="text-xl font-bold text-ink">{dict.stationUi.nav.compare}</h2>
          <div className="grid items-start gap-4 lg:grid-cols-2">{compare}</div>
        </section>
      )}
    </>
  );
}
