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

export const lineSchema = z.object({
  nameJa: z.string().min(1),
  nameEn: z.string().min(1),
  operator: z.enum(["jr", "tokyo-metro", "toei", "private"]),
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

export const scoresSchema = z.object(
  Object.fromEntries(SCORE_AXES.map((a) => [a, score])) as Record<
    ScoreAxis,
    typeof score
  >,
);

export const facilitiesSchema = z.object({
  supermarkets: z.array(z.string()),
  commercial: z.array(z.string()),
  notes: z.string().optional(),
});

export const stationSchema = z.object({
  slug: z
    .string()
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "slug はローマ字ケバブケース"),
  nameJa: z.string().min(1),
  nameRomaji: z.string().min(1),
  ward: z.string().min(1),
  wardNameJa: z.string().min(1),
  lines: z.array(lineSchema).min(1),
  hasFirstTrain: z.boolean(),
  /** 朝ラッシュの混雑度。1 = 空いている、5 = 非常に混雑 */
  morningCrowding: z.number().int().min(1).max(5),
  rent: rentSchema,
  commutes: z.array(commuteSchema).min(1),
  scores: scoresSchema,
  facilities: facilitiesSchema,
  similarStations: z.array(z.string()),
  /**
   * seed     = 推定値。公開してはならない（docs/05-seo.md §3）
   * reviewed = 一次データに紐づけ、人間が確認済み
   * verified = 出典つきで検証済み
   */
  dataQuality: z.enum(["seed", "reviewed", "verified"]),
  lastReviewedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

export type Station = z.infer<typeof stationSchema>;
export type Line = z.infer<typeof lineSchema>;
export type Rent = z.infer<typeof rentSchema>;
export type Commute = z.infer<typeof commuteSchema>;
export type Scores = z.infer<typeof scoresSchema>;

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
