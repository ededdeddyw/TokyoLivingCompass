import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import type { ActiveLocale } from "./i18n";
import {
  lineSchema,
  rosterStationSchema,
  stationContentSchema,
  stationSchema,
  type Line,
  type LocalizedStation,
  type RosterStation,
  type Station,
  type StationContent,
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

function readJson(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf8"));
}

function listSlugs(dir: string): string[] {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""))
    .sort();
}

let stationCache: Station[] | null = null;

/** 全駅のマスタデータ。日本語駅名の五十音ではなく slug 順で安定させる。 */
export function getAllStations(): Station[] {
  if (stationCache) return stationCache;

  stationCache = listSlugs(STATIONS_DIR).map((slug) => {
    const parsed = stationSchema.safeParse(
      readJson(join(STATIONS_DIR, `${slug}.json`)),
    );
    if (!parsed.success) {
      throw new Error(
        `駅データが不正です: ${slug}.json\n${JSON.stringify(parsed.error.format(), null, 2)}`,
      );
    }
    if (parsed.data.slug !== slug) {
      throw new Error(
        `ファイル名と slug が一致しません: ${slug}.json は slug="${parsed.data.slug}"`,
      );
    }
    return parsed.data;
  });

  return stationCache;
}

export function getStation(slug: string): Station | null {
  return getAllStations().find((s) => s.slug === slug) ?? null;
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
