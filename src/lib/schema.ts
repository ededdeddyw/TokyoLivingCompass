import { z } from "zod";

/**
 * データ定義の単一の正。
 * ドキュメント（docs/02-data-model.md, docs/03-scoring.md）と食い違った場合はこちらが正。
 */

/** 16 の評価軸。順序が表示順を兼ねる。軸を足す/消すとここだけで全体に波及する。 */
export const SCORE_AXES = [
  "rentValue",
  "commute",
  "transitConvenience",
  "shopping",
  "food",
  "cafe",
  "nightlife",
  "safety",
  "quietness",
  "family",
  "singleLife",
  "internationalFriendliness",
  "style",
  "nature",
  "healthcare",
  "fitness",
] as const;

export type ScoreAxis = (typeof SCORE_AXES)[number];

/** 間取り。逆引き検索の入力と 1:1 で対応する。 */
export const RENT_TYPES = ["oneRoom", "oneK", "oneLDK", "twoLDK"] as const;
export type RentType = (typeof RENT_TYPES)[number];

/** 勤務先起点検索で選べるオフィス駅。全駅がこれら全てへの commutes を持つ。 */
export const OFFICE_HUBS = [
  "shinjuku",
  "shibuya",
  "tokyo",
  "shinagawa",
  "otemachi",
  "toranomon",
  "roppongi",
] as const;
export type OfficeHub = (typeof OFFICE_HUBS)[number];

const score = z.number().int().min(0).max(100);

/** 路線マスタ（data/reference/lines.json）。駅データは id で参照する。 */
export const lineSchema = z.object({
  id: z.string().regex(/^\d+$/),
  nameJa: z.string().min(1),
  nameEn: z.string().min(1),
  operator: z.enum(["jr", "tokyo-metro", "toei", "private"]),
});

/**
 * ロースター: 対象路線の23区内の全駅（data/roster/stations.json）。
 * 詳細プロフィール（data/stations/）を持たない駅も含む「掲載候補の全体像」。
 */
export const rosterStationSchema = z.object({
  slug: z.string().regex(/^[a-z0-9]+(-[a-z0-9]+)*$/),
  nameJa: z.string().min(1),
  nameRomaji: z.string().min(1),
  ward: z.string().min(1),
  wardCode: z.string().regex(/^\d{5}$/),
  wardNameJa: z.string().min(1),
  lat: z.number(),
  lon: z.number(),
  lineIds: z.array(z.string()).min(1),
});

export const rentSchema = z.object(
  Object.fromEntries(
    RENT_TYPES.map((t) => [t, z.number().int().min(10000).max(2000000)]),
  ) as Record<RentType, z.ZodNumber>,
);

export const commuteSchema = z.object({
  to: z.enum(OFFICE_HUBS),
  minutes: z.number().int().min(0).max(180),
  transfers: z.number().int().min(0).max(5),
});

/**
 * スコアは軸ごとに任意。443駅ぶんのデータは一度に揃わず、
 * 計算できる軸・購入した軸・人が判断した軸が順に埋まっていくため。
 */
export const scoresSchema = z.object(
  Object.fromEntries(SCORE_AXES.map((a) => [a, score.optional()])) as Record<
    ScoreAxis,
    z.ZodOptional<typeof score>
  >,
);

/**
 * データの出典（docs/08-data-sources-rent.md）。
 * basis は「何の家賃か」。混同すると出典を揃えても数字が合わない。
 *   asking     = 募集賃料（これから借りる人が直面する額。成約額より高めに出る）
 *   contracted = 成約賃料
 *   paid       = 支払家賃（既存契約を含むため低めに出る）
 */
/**
 * 代表値の算出方法。自由記述にすると多言語で表示できないため ID にする。
 * 表示ラベルは src/lib/dictionaries.ts。
 *   vendor-station-area  = ベンダーが駅の範囲で集計した値をそのまま使う
 *   radius-800m-weighted = 駅から半径800mの町丁を戸数加重平均（docs/08-data-sources-rent.md §4）
 *   manual               = 手集計
 */
export const RENT_METHODS = [
  "vendor-station-area",
  "radius-800m-weighted",
  "manual",
] as const;
export type RentMethod = (typeof RENT_METHODS)[number];

export const rentSourceSchema = z.object({
  name: z.string().min(1),
  url: z.string().url().optional(),
  basis: z.enum(["asking", "contracted", "paid"]),
  statistic: z.enum(["median", "mean"]),
  retrievedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  method: z.enum(RENT_METHODS).optional(),
  sampleSize: z.number().int().positive().optional(),
});

export const sourcesSchema = z.object({
  rent: rentSourceSchema.optional(),
});

export const facilitiesSchema = z.object({
  supermarkets: z.array(z.string()),
  commercial: z.array(z.string()),
  notes: z.string().optional(),
});

/**
 * 駅プロフィール（data/stations/{slug}.json）。
 * 駅名・所在区・路線はロースターが持つので、ここには書かない。
 * 家賃・スコア・施設は、揃った順に埋めていく任意項目。
 */
export const stationSchema = z.object({
  slug: z
    .string()
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "slug はローマ字ケバブケース"),
  hasFirstTrain: z.boolean().optional(),
  /** 朝ラッシュの混雑度。1 = 空いている、5 = 非常に混雑 */
  morningCrowding: z.number().int().min(1).max(5).optional(),
  rent: rentSchema.optional(),
  scores: scoresSchema.default({}),
  facilities: facilitiesSchema.optional(),
  similarStations: z.array(z.string()).default([]),
  /**
   * 出典。dataQuality を "seed" から上げるには sources.rent が必須
   * （scripts/validate-data.ts で検証）。
   */
  sources: sourcesSchema.optional(),
  /**
   * seed     = 推定値。公開してはならない（docs/05-seo.md §3）
   * reviewed = 一次データに紐づけ、人間が確認済み
   * verified = 出典つきで検証済み
   */
  dataQuality: z.enum(["seed", "reviewed", "verified"]),
  lastReviewedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

export type StationProfile = z.infer<typeof stationSchema>;

/** 計算で求めた所要時間（data/computed/commutes.json）。全443駅ぶんある。 */
export const computedCommutesSchema = z.record(
  z.string(),
  z.array(commuteSchema).min(1),
);

/** 計算で求めたスコア（data/computed/scores.json）。埋まっている軸だけ入る。 */
export const computedScoresSchema = z.record(z.string(), scoresSchema);

/**
 * ロースター（全駅の事実）＋計算値＋プロフィール（あれば）を重ねたもの。
 * ページはこの形で受け取る。プロフィールが無い駅は dataQuality が "roster"。
 */
export type Station = RosterStation & {
  commutes: Commute[];
  scores: Partial<Record<ScoreAxis, number>>;
  similarStations: string[];
  hasFirstTrain?: boolean;
  morningCrowding?: number;
  rent?: Rent;
  facilities?: Facilities;
  sources?: Sources;
  dataQuality: "roster" | "seed" | "reviewed" | "verified";
  lastReviewedAt?: string;
};
export type Line = z.infer<typeof lineSchema>;
export type RosterStation = z.infer<typeof rosterStationSchema>;
export type Rent = z.infer<typeof rentSchema>;
export type Commute = z.infer<typeof commuteSchema>;
export type Scores = z.infer<typeof scoresSchema>;
export type Facilities = z.infer<typeof facilitiesSchema>;
export type RentSource = z.infer<typeof rentSourceSchema>;
export type Sources = z.infer<typeof sourcesSchema>;

export const stationContentSchema = z.object({
  slug: z.string().min(1),
  locale: z.string().min(1),
  name: z.string().min(1),
  tagline: z.string().min(1),
  summary: z.string().min(1),
  goodFor: z.array(z.string()).min(1),
  notFor: z.array(z.string()).min(1),
  /** 東京在住者コメント。公開版は人間が書く（docs/02-data-model.md §4） */
  residentComment: z.string().min(1),
  /**
   * human           = 人間が書いた（公開できる）
   * ai-localized    = 日本語マスターから AI がローカライズし、人間がレビュー済み
   * seed-placeholder = 開発用の仮テキスト。公開してはならない
   */
  authoredBy: z.enum(["human", "ai-localized", "seed-placeholder"]),
});

export type StationContent = z.infer<typeof stationContentSchema>;

/** 駅マスタと、あるロケールの散文を結合したもの。ページはこの形で受け取る。 */
export type LocalizedStation = Station & { content: StationContent };
