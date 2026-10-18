import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import type { z } from "zod";

import type { ActiveLocale } from "./i18n";
import {
  computedCommutesSchema,
  computedScoresSchema,
  lineSchema,
  rentBandsSchema,
  rosterStationSchema,
  stationContentSchema,
  stationSchema,
  type Commute,
  type Line,
  type LocalizedStation,
  type RentBands,
  type RentType,
  RENT_TYPES,
  type RosterStation,
  type Station,
  type StationContent,
  type ScoreAxis,
  type StationProfile,
  type TownTraits,
  townTraitsFileSchema,
  stationPhotosFileSchema,
  stationGalleryFileSchema,
  localPhotosFileSchema,
  stationWardsFileSchema,
  wardLinksFileSchema,
  lifestyleFileSchema,
  type Lifestyle,
  type Persona,
  type StationPhoto,
  type WardLinks,
} from "./schema";

/**
 * data/ を読むのはこのファイルだけ（docs/07-architecture.md §3）。
 * DB へ移行するときはここだけを差し替える。
 */

const DATA_DIR = join(process.cwd(), "data");
const STATIONS_DIR = join(DATA_DIR, "stations");
const CONTENT_DIR = join(DATA_DIR, "content");
const ROSTER_FILE = join(DATA_DIR, "roster", "stations.json");
const LINES_FILE = join(DATA_DIR, "reference", "lines.json");
const COMMUTES_FILE = join(DATA_DIR, "computed", "commutes.json");
const COMPUTED_SCORES_FILE = join(DATA_DIR, "computed", "scores.json");
const RENT_BANDS_FILE = join(DATA_DIR, "computed", "rent-bands.json");
const TOWN_TRAITS_DIR = join(DATA_DIR, "town-traits");
const PHOTOS_FILE = join(DATA_DIR, "computed", "station-photos.json");
const LOCAL_PHOTOS_FILE = join(DATA_DIR, "reference", "local-photos.json");
const GALLERY_FILE = join(DATA_DIR, "computed", "station-gallery.json");
const LIFESTYLE_FILE = join(DATA_DIR, "computed", "lifestyle.json");
const STATION_WARDS_FILE = join(DATA_DIR, "computed", "station-wards.json");
const WARD_LINKS_FILE = join(DATA_DIR, "reference", "ward-links.json");
/**
 * 街の特色を重ねる順。住んでいる人の目線の出典（ぶらリハウス）を先に、
 * 全駅の下地にしている Wikipedia を後ろに置く。ここに無いファイルは読まない。
 */
const TOWN_TRAIT_FILES = ["rehouse.json", "wikipedia.json"];

function readJson(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf8"));
}

function listSlugs(dir: string): string[] {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""))
    .sort();
}

let profileCache: Map<string, StationProfile> | null = null;

/** 駅プロフィール。ロースターの部分集合で、家賃・スコア・施設を持つ。 */
function getProfiles(): Map<string, StationProfile> {
  if (profileCache) return profileCache;

  profileCache = new Map(
    listSlugs(STATIONS_DIR).map((slug) => {
      const parsed = stationSchema.safeParse(
        readJson(join(STATIONS_DIR, `${slug}.json`)),
      );
      if (!parsed.success) {
        throw new Error(
          `駅プロフィールが不正です: ${slug}.json\n${JSON.stringify(parsed.error.format(), null, 2)}`,
        );
      }
      if (parsed.data.slug !== slug) {
        throw new Error(
          `ファイル名と slug が一致しません: ${slug}.json は slug="${parsed.data.slug}"`,
        );
      }
      return [slug, parsed.data] as const;
    }),
  );

  return profileCache;
}

let commuteCache: Map<string, Commute[]> | null = null;

/** 計算で求めた所要時間。scripts/build-commutes.py が生成する。 */
function getComputedCommutes(): Map<string, Commute[]> {
  if (commuteCache) return commuteCache;
  const parsed = computedCommutesSchema.safeParse(readJson(COMMUTES_FILE));
  if (!parsed.success) {
    throw new Error(
      `所要時間データが不正です\n${JSON.stringify(parsed.error.format(), null, 2)}`,
    );
  }
  commuteCache = new Map(Object.entries(parsed.data));
  return commuteCache;
}

let computedScoreCache: Map<string, Partial<Record<ScoreAxis, number>>> | null = null;

/** 計算で求めたスコア。scripts/build-scores.py が生成する。 */
function getComputedScores(): Map<string, Partial<Record<ScoreAxis, number>>> {
  if (computedScoreCache) return computedScoreCache;
  const parsed = computedScoresSchema.safeParse(readJson(COMPUTED_SCORES_FILE));
  if (!parsed.success) {
    throw new Error(
      `計算スコアが不正です\n${JSON.stringify(parsed.error.format(), null, 2)}`,
    );
  }
  computedScoreCache = new Map(Object.entries(parsed.data));
  return computedScoreCache;
}

let rentBandCache: Map<string, RentBands> | null = null;

/**
 * 複数サイトの掲載相場を平均した帯。scripts/build-rent-bands.py が生成する。
 * まだ調べていない駅は入っていないので、無くても落とさない。
 */
function getRentBands(): Map<string, RentBands> {
  if (rentBandCache) return rentBandCache;
  let raw: unknown;
  try {
    raw = readJson(RENT_BANDS_FILE);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    rentBandCache = new Map();
    return rentBandCache;
  }
  const parsed = rentBandsSchema.safeParse(raw);
  if (!parsed.success) {
    throw new Error(
      `家賃の帯が不正です\n${JSON.stringify(parsed.error.format(), null, 2)}`,
    );
  }
  rentBandCache = new Map(Object.entries(parsed.data));
  return rentBandCache;
}

/** 間取りごとの、駅の帯の平均値をさらに平均したもの。 */
export type RentAverage = Partial<Record<RentType, { mean: number; count: number }>>;

function averageBands(bands: RentBands[]): RentAverage {
  const out: RentAverage = {};
  for (const type of RENT_TYPES) {
    const means = bands.flatMap((b) => (b.bands[type] ? [b.bands[type]!.mean] : []));
    if (means.length === 0) continue;
    out[type] = {
      mean: Math.round(means.reduce((a, b) => a + b, 0) / means.length),
      count: means.length,
    };
  }
  return out;
}

/**
 * 同じ区の駅と、23区すべての駅の家賃の平均。駅ページで「この駅は高いのか安いのか」を示す。
 *
 * 駅ごとの帯の平均値を、駅を1つずつ同じ重みで平均している。物件の数では重みをつけないので、
 * 「区の家賃相場」ではなく「区の駅の平均」として出す。保存せず毎回計算する（設計上の約束4）。
 */
export function getRentAverages(wardCode: string): { ward: RentAverage; all: RentAverage } {
  const bands = getRentBands();
  const roster = getRoster();
  const inWard = roster
    .filter((s) => s.wardCode === wardCode)
    .flatMap((s) => (bands.has(s.slug) ? [bands.get(s.slug)!] : []));
  return { ward: averageBands(inWard), all: averageBands([...bands.values()]) };
}

let stationCache: Station[] | null = null;

/**
 * ロースター（事実）＋計算値（所要時間）＋プロフィール（家賃・スコア）を重ねる。
 * プロフィールが無い駅も返る。その場合 dataQuality は "roster"。
 */
export function getAllStations(): Station[] {
  if (stationCache) return stationCache;

  const profiles = getProfiles();
  const commutes = getComputedCommutes();
  const computedScores = getComputedScores();
  const rentBands = getRentBands();

  stationCache = getRoster().map((base) => {
    const profile = profiles.get(base.slug);
    return {
      ...base,
      commutes: commutes.get(base.slug) ?? [],
      // 計算値が土台で、人が入れた値があればそちらを採る。
      scores: {
        ...(computedScores.get(base.slug) ?? {}),
        ...(profile?.scores ?? {}),
      },
      similarStations: profile?.similarStations ?? [],
      hasFirstTrain: profile?.hasFirstTrain,
      morningCrowding: profile?.morningCrowding,
      rent: profile?.rent,
      rentHistory: profile?.rentHistory,
      rentBands: rentBands.get(base.slug),
      facilities: profile?.facilities,
      sources: profile?.sources,
      dataQuality: profile?.dataQuality ?? "roster",
      lastReviewedAt: profile?.lastReviewedAt,
    };
  });

  return stationCache;
}

export function getStation(slug: string): Station | null {
  return getAllStations().find((s) => s.slug === slug) ?? null;
}

/** プロフィール（家賃・スコア）を持つ駅だけ。 */
export function getProfiledStations(): Station[] {
  return getAllStations().filter((s) => s.dataQuality !== "roster");
}

const contentCache = new Map<string, StationContent | null>();

export function getStationContent(
  slug: string,
  locale: ActiveLocale,
): StationContent | null {
  const key = `${locale}/${slug}`;
  const cached = contentCache.get(key);
  if (cached !== undefined) return cached;

  let content: StationContent | null = null;
  try {
    const parsed = stationContentSchema.safeParse(
      readJson(join(CONTENT_DIR, locale, `${slug}.json`)),
    );
    if (!parsed.success) {
      throw new Error(
        `コンテンツが不正です: ${locale}/${slug}.json\n${JSON.stringify(parsed.error.format(), null, 2)}`,
      );
    }
    content = parsed.data;
  } catch (error) {
    // ファイルがない = そのロケールでは未翻訳。ページを生成しない（docs/04-i18n.md §5）。
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }

  contentCache.set(key, content);
  return content;
}

/**
 * そのロケールで公開できる駅だけを返す。
 * 未翻訳の駅は日本語にフォールバックせず、一覧からも除外する（docs/04-i18n.md §5）。
 */
export function getLocalizedStations(locale: ActiveLocale): LocalizedStation[] {
  return getAllStations().flatMap((station) => {
    const content = getStationContent(station.slug, locale);
    return content ? [{ ...station, content }] : [];
  });
}

export function getLocalizedStation(
  slug: string,
  locale: ActiveLocale,
): LocalizedStation | null {
  const station = getStation(slug);
  if (!station) return null;
  const content = getStationContent(slug, locale);
  return content ? { ...station, content } : null;
}

/** 検証スクリプト用。data/content 配下に実在するロケールを列挙する。 */
export function listContentLocales(): string[] {
  return readdirSync(CONTENT_DIR, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort();
}

export function listContentSlugs(locale: string): string[] {
  return listSlugs(join(CONTENT_DIR, locale));
}

let lineCache: Map<string, Line> | null = null;

/** 路線マスタ。駅データは id で参照するので、名前の解決はここに集約する。 */
export function getLines(): Map<string, Line> {
  if (lineCache) return lineCache;
  const parsed = lineSchema.array().safeParse(readJson(LINES_FILE));
  if (!parsed.success) {
    throw new Error(
      `路線マスタが不正です\n${JSON.stringify(parsed.error.format(), null, 2)}`,
    );
  }
  lineCache = new Map(parsed.data.map((l) => [l.id, l]));
  return lineCache;
}

/** 駅の路線を路線マスタから解決する。未知の id は無視せず落とす。 */
export function resolveLines(lineIds: string[]): Line[] {
  const lines = getLines();
  return lineIds.map((id) => {
    const line = lines.get(id);
    if (!line) throw new Error(`未知の路線 id: ${id}`);
    return line;
  });
}

let rosterCache: RosterStation[] | null = null;

/** 対象路線の23区内の全駅。詳細プロフィールの有無は問わない。 */
export function getRoster(): RosterStation[] {
  if (rosterCache) return rosterCache;
  const parsed = rosterStationSchema.array().safeParse(readJson(ROSTER_FILE));
  if (!parsed.success) {
    throw new Error(
      `ロースターが不正です\n${JSON.stringify(parsed.error.format(), null, 2)}`,
    );
  }
  rosterCache = parsed.data;
  return rosterCache;
}

let townTraitCache: Map<string, TownTraits> | null = null;

/**
 * 街の特色。いまは日本語だけで、ほかのロケールでは出さない（訳していないため）。
 * 出典ごとのファイルを重ね、出典ごとに記事へのリンクを残す。
 */
export function getTownTraits(slug: string, locale: ActiveLocale): TownTraits | null {
  if (locale !== "ja") return null;
  if (!townTraitCache) {
    townTraitCache = new Map();
    for (const file of TOWN_TRAIT_FILES) {
      let raw: unknown;
      try {
        raw = readJson(join(TOWN_TRAITS_DIR, file));
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
        continue;
      }
      const parsed = townTraitsFileSchema.safeParse(raw);
      if (!parsed.success) {
        throw new Error(
          `街の特色が不正です: ${file}\n${JSON.stringify(parsed.error.format(), null, 2)}`,
        );
      }
      const { meta, stations } = parsed.data;
      for (const [key, entry] of Object.entries(stations)) {
        if (entry.traits.length === 0) continue;
        const cur = townTraitCache.get(key) ?? { traits: [], sources: [] };
        cur.traits.push(...entry.traits.map((t) => t.text));
        cur.sources.push({
          label: meta.label,
          licenseName: meta.licenseName,
          license: meta.license,
          articles: entry.sources.map(({ title, url }) => ({ title, url })),
        });
        townTraitCache.set(key, cur);
      }
    }
  }
  return townTraitCache.get(slug) ?? null;
}

/** ファイルが無ければ null。あれば zod で確かめる。 */
function readOptional<T>(file: string, schema: { safeParse(v: unknown): { success: true; data: T } | { success: false; error: { format(): unknown } } }, label: string): T | null {
  let raw: unknown;
  try {
    raw = readJson(file);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    return null;
  }
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    throw new Error(`${label}が不正です\n${JSON.stringify(parsed.error.format(), null, 2)}`);
  }
  return parsed.data;
}

let photoCache: Record<string, StationPhoto | null> | null = null;

let galleryCache: Record<string, StationPhoto[]> | null = null;

/**
 * 駅の写真。1枚目が駅舎か駅前で、2枚目以降が街並みや周辺の施設。
 * 複数枚の写真（station-gallery.json）があればそれを使い、無ければ1枚だけの写真を使う。
 * Commons で自由に使える写真が見つからなかった駅は空。
 */
let localPhotoCache: Record<string, (StationPhoto & { first: boolean })[]> | null = null;

export function getStationPhotos(slug: string): StationPhoto[] {
  galleryCache ??= readOptional(GALLERY_FILE, stationGalleryFileSchema, "駅の写真（複数枚）") ?? {};
  localPhotoCache ??=
    readOptional(LOCAL_PHOTOS_FILE, localPhotosFileSchema, "人が選んだ写真")?.stations ?? {};
  photoCache ??= readOptional(PHOTOS_FILE, stationPhotosFileSchema, "駅の写真") ?? {};
  const many = galleryCache[slug];
  const one = photoCache[slug];
  const commons: StationPhoto[] = many && many.length > 0 ? many : one ? [one] : [];
  const local = localPhotoCache[slug] ?? [];
  return [
    ...local.filter((p) => p.first),
    ...commons,
    ...local.filter((p) => !p.first),
  ];
}

let wardLinkCache: { stationWards: Record<string, string[]>; links: Record<string, Omit<WardLinks, "wardCode">> } | null = null;

/**
 * 駅のまわりにかかる区ごとの、公式ページへのリンク。所在地の区が先頭。
 * 区の境にある駅（目黒駅は品川区にあり、西側は目黒区）では2つ以上になる。
 */
export function getWardLinks(station: { slug: string; wardCode: string }): WardLinks[] {
  wardLinkCache ??= {
    stationWards: readOptional(STATION_WARDS_FILE, stationWardsFileSchema, "駅のまわりの区") ?? {},
    links: readOptional(WARD_LINKS_FILE, wardLinksFileSchema, "区のリンク")?.wards ?? {},
  };
  const codes = wardLinkCache.stationWards[station.slug] ?? [station.wardCode];
  return codes.flatMap((code) => {
    const l = wardLinkCache!.links[code];
    return l ? [{ ...l, wardCode: code }] : [];
  });
}

let lifestyleCache: z.infer<typeof lifestyleFileSchema> | null = null;

function lifestyleFile() {
  lifestyleCache ??= readOptional(LIFESTYLE_FILE, lifestyleFileSchema, "層ごとの点") ?? {
    meta: { note: "", commuteShare: { single: 0, dinks: 0, family: 0, senior: 0 }, rentShare: 0 },
    stations: {},
  };
  return lifestyleCache;
}

/** 層と休日の過ごし方ごとの点と、電車で行きやすい行き先。 */
export function getLifestyle(slug: string): Lifestyle | null {
  return lifestyleFile().stations[slug] ?? null;
}

/** 公開用の点に含めた通勤の割合（層ごと） */
export function getLifestyleCommuteShare(): Record<Persona, number> {
  return lifestyleFile().meta.commuteShare as Record<Persona, number>;
}
