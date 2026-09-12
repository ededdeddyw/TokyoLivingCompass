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
 * スコアは軸ごとに任意。448駅ぶんのデータは一度に揃わず、
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

/**
 * 家賃の推移。相場を1時点で示すと、上がっているのか下がっているのかが分からない。
 * 「いま高い」と「これから高くなる」は住む判断としてまったく違うため、時系列で持つ。
 * 間取りごとに欠けがあってよい（揃った間取りから埋めていく）。
 */
export const rentPointSchema = z.object({
  /** 集計年。四半期まで分かる場合は quarter も入れる */
  year: z.number().int().min(2000).max(2100),
  quarter: z.number().int().min(1).max(4).optional(),
  rent: z
    .object(
      Object.fromEntries(
        RENT_TYPES.map((t) => [
          t,
          z.number().int().min(10000).max(2000000).optional(),
        ]),
      ) as Record<RentType, z.ZodOptional<z.ZodNumber>>,
    )
    .refine((r) => Object.values(r).some((v) => v !== undefined), {
      message: "1つ以上の間取りに値が必要です",
    }),
});

export const rentHistorySchema = z.object({
  /** 古い順に並べる。2点以上ないと推移にならない */
  points: z.array(rentPointSchema).min(2),
  /** 推移は本文で言い切る材料になるため、出典は必須にする */
  source: rentSourceSchema,
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
  /** 家賃の推移。出典つきでしか持てない（rentHistorySchema） */
  rentHistory: rentHistorySchema.optional(),
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

/** 計算で求めた所要時間（data/computed/commutes.json）。全448駅ぶんある。 */
export const computedCommutesSchema = z.record(
  z.string(),
  z.array(commuteSchema).min(1),
);

/**
 * 複数サイトの掲載相場を平均し、1万円刻みに丸めた帯（data/computed/rent-bands.json）。
 * scripts/build-rent-bands.py が data/rent-survey/ の観測値から生成する。
 *
 * 相場を1点の数字で示すと、出典ごとに数万円ちがう値を1つに見せてしまう。
 * 帯で示したうえで、出典ごとの最小と最大も持たせ、開きが大きければ駅ページで注記する。
 */
export const rentBandSchema = z.object({
  low: z.number().int().min(0),
  high: z.number().int().min(0),
  mean: z.number().int().min(0),
  sourceMin: z.number().int().min(0),
  sourceMax: z.number().int().min(0),
  /** 平均のもとになったサイト数。2未満の間取りは帯にしない */
  sourceCount: z.number().int().min(2),
  /** 出典間の開きが3万円以上か。大きければ、帯だけを信じないよう注記する */
  wideSpread: z.boolean(),
});

export const rentBandsSchema = z.record(
  z.string(),
  z.object({
    bands: z.object(
      Object.fromEntries(
        RENT_TYPES.map((t) => [t, rentBandSchema.optional()]),
      ) as Record<RentType, z.ZodOptional<typeof rentBandSchema>>,
    ),
    sources: z
      .array(
        z.object({
          name: z.string().min(1),
          url: z.string().url().nullable().optional(),
          retrievedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
        }),
      )
      .min(2),
    retrievedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    /** すべての観測値を人がページを開いて確認したか。false なら暫定値として表示する */
    verified: z.boolean(),
  }),
);

export type RentBand = z.infer<typeof rentBandSchema>;
export type RentBands = z.infer<typeof rentBandsSchema>[string];

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
  rentHistory?: RentHistory;
  /** 複数サイトの掲載相場を平均した帯。出典を明示して「弊社調べ」として出す */
  rentBands?: RentBands;
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
export type RentPoint = z.infer<typeof rentPointSchema>;
export type RentHistory = z.infer<typeof rentHistorySchema>;
export type Sources = z.infer<typeof sourcesSchema>;

/**
 * 駅の散文（data/content/{locale}/{slug}.json）。
 *
 * 既存の不動産まとめ記事が答えていない項目を、駅どうしで比較できる形に構造化する。
 * 「駅前にスーパーがあり便利です」で終わらせないための型である。
 * 何を書けば完成なのかは docs/12-quality-standard.md。
 *
 * tagline から notFor までが必須。それ以外は分かったものから足す。
 */

/** 時間帯で街の顔は変わる。夜だけ見て決めて後悔する、が最も多い失敗。 */
export const dayFacesSchema = z.object({
  morning: z.string().min(1),
  daytime: z.string().min(1),
  night: z.string().min(1),
  weekend: z.string().min(1),
});

/** 坂と高低差。自転車が使えるか、ベビーカーを押せるかが変わる。 */
export const terrainSchema = z.object({
  slope: z.enum(["flat", "some", "hilly"]),
  note: z.string().min(1),
});

/**
 * スーパーの価格帯。同じ「スーパーが2軒」でも、
 * 業務スーパーとオオゼキと成城石井では生活コストがまるで違う。
 */
export const groceryStoreSchema = z.object({
  name: z.string().min(1),
  tier: z.enum(["discount", "standard", "premium"]),
  walkMinutes: z.number().int().min(0).max(30),
  note: z.string().optional(),
});

/**
 * 駅の出口ごとの街の違い。
 * 同じ駅でも北口と南口で別の街であることが多く、住む方角の選択に直結する。
 * 既存のまとめ記事が駅を一枚岩として扱うせいで、最も抜け落ちている観点。
 */
export const exitSchema = z.object({
  name: z.string().min(1),
  /**
   * その出口がどの路線の改札につながっているか（「JR中央・総武線」「都営大江戸線」）。
   * 複数路線が乗り入れる駅では、路線ごとに改札の位置も出口の先の街並みも変わる。
   * 1路線しか通っていない駅では省略してよい。
   */
  line: z.string().min(1).optional(),
  character: z.string().min(1),
});

/** 家賃の幅。相場を1点で示すと、同じ駅の中の差が消えてしまう。 */
export const rentRangeSchema = z.object({
  note: z.string().min(1),
  /** 何が家賃差を生んでいるか（徒歩分数、築年、通り沿いかなど） */
  drivers: z.array(z.string()).min(1),
});

/** 隣接駅との使い分け。「この用途なら隣の駅のほうがいい」を正直に書く。 */
export const neighbourNoteSchema = z.object({
  slug: z.string().min(1),
  note: z.string().min(1),
});

export const stationContentSchema = z.object({
  slug: z.string().min(1),
  locale: z.string().min(1),
  name: z.string().min(1),

  // --- 必須 ---
  tagline: z.string().min(1),
  summary: z.string().min(1),
  goodFor: z.array(z.string()).min(1),
  notFor: z.array(z.string()).min(1),

  // --- 深さを作る層。分かったものから足す ---
  /** 時間帯別の街の顔 */
  faces: dayFacesSchema.optional(),
  /** 坂・高低差 */
  terrain: terrainSchema.optional(),
  /** 騒音源。線路沿い、幹線道路、繁華街、学校など */
  noiseSources: z.array(z.string()).optional(),
  /** 日常の買い物先。価格帯と徒歩分数つき */
  groceries: z.array(groceryStoreSchema).optional(),
  /** 住民層 */
  residents: z.string().optional(),
  /** 物件の傾向。築年数、構造、間取りの偏り */
  housingStock: z.string().optional(),
  /** 災害リスク。浸水想定、木造密集など */
  hazards: z.string().optional(),
  /** 駅そのものの使い勝手。ホームの深さ、改札の位置、乗換の実際 */
  stationNote: z.string().optional(),
  /** 夜の帰り道 */
  nightWalk: z.string().optional(),
  /** 家賃が相場より高い／安い理由 */
  rentReason: z.string().optional(),
  /** 隣接駅との使い分け */
  neighbours: z.array(neighbourNoteSchema).optional(),
  /** 5年後の見通し。再開発、路線延伸など */
  outlook: z.string().optional(),
  /** 出口ごとの街の違い */
  exits: z.array(exitSchema).optional(),
  /** 子育て。学区、保育園、公園、ベビーカーでの移動 */
  family: z.string().optional(),
  /** 医療。夜間・休日診療、総合病院、小児科 */
  medical: z.string().optional(),
  /** 家賃の幅と、その幅を生んでいる要因 */
  rentRange: rentRangeSchema.optional(),

  /** 東京在住者コメント。公開版は人間が書く（docs/02-data-model.md §4） */
  residentComment: z.string().min(1),
  /**
   * human            = 人間が書いた（公開できる）
   * ai-localized     = 日本語マスターから AI がローカライズし、人間がレビュー済み
   * seed-placeholder = 開発用の仮テキスト。公開してはならない
   * draft            = 構成は書けているが、事実確認が済んでいない
   */
  authoredBy: z.enum(["human", "ai-localized", "seed-placeholder", "draft"]),
});

/** 深さを作る層のキー。充足率の計測と品質判定に使う。 */
export const DEPTH_FIELDS = [
  "faces",
  "terrain",
  "noiseSources",
  "groceries",
  "residents",
  "housingStock",
  "hazards",
  "stationNote",
  "nightWalk",
  "rentReason",
  "neighbours",
  "outlook",
  "exits",
  "family",
  "medical",
  "rentRange",
] as const;

export type DepthField = (typeof DEPTH_FIELDS)[number];

export type StationContent = z.infer<typeof stationContentSchema>;
export type DayFaces = z.infer<typeof dayFacesSchema>;
export type Terrain = z.infer<typeof terrainSchema>;
export type GroceryStore = z.infer<typeof groceryStoreSchema>;
export type NeighbourNote = z.infer<typeof neighbourNoteSchema>;
export type StationExit = z.infer<typeof exitSchema>;
export type RentRange = z.infer<typeof rentRangeSchema>;

/** その駅の日本語コンテンツが、深さの層をいくつ満たしているか。 */
export function depthFilled(content: StationContent): DepthField[] {
  return DEPTH_FIELDS.filter((field) => {
    const value = content[field];
    if (value === undefined) return false;
    return Array.isArray(value) ? value.length > 0 : true;
  });
}

/** 駅マスタと、あるロケールの散文を結合したもの。ページはこの形で受け取る。 */
export type LocalizedStation = Station & { content: StationContent };
