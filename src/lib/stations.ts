import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

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
  type RosterStation,
  type Station,
  type StationContent,
  type ScoreAxis,
  type StationProfile,
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
