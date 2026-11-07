/**
 * 条件に合わない駅を消していく道具（docs/06-roadmap.md Phase 4.5、docs/20-choose.md）。
 *
 * 逆引き検索（rankStations）は、条件を満たす駅を合う順に並べる。
 * こちらは「この条件の駅は困る」を1つずつ足して候補を消していく。
 * 足すたびに残りの駅数を出し、条件ごとに「外すと何駅戻るか」も出す。
 * 0駅になっても、どの条件をゆるめればよいかが分かるようにするためである。
 *
 * データが無くて判定できない駅は消さない。消すと「条件に合わなかった」のか
 * 「データが無かった」のかが読み手に分からなくなる。残したうえで、判定できなかった
 * 条件を駅ごとに示す（地図データの登録が少ない駅の点を「測れていない」としたのと同じ考え方）。
 *
 * ここは純粋な関数だけを置く。データは src/lib/stations.ts の getChooseStations が組み立てる。
 */
import type { OfficeHub, RentType } from "@/lib/schema";
import { OFFICE_HUBS, RENT_TYPES } from "@/lib/schema";

/** 大雨のときの浸水の想定の深さを、比べられる順位にしたもの（0.5m未満が0） */
export const FLOOD_DEPTH_RANK: Record<string, number> = {
  "0.5m未満": 0,
  "0.5〜3m": 1,
  "3〜5m": 2,
  "5〜10m": 3,
  "10〜20m": 4,
  "20m以上": 5,
};
/** 「深い」とみなす境目。3m以上（3〜5m の順位） */
export const DEEP_FLOOD_RANK = 2;

/** 判定に使う、駅ごとの値。ブラウザへ渡すので、使う値だけに絞る */
export type ChooseStation = {
  slug: string;
  name: string;
  ward: string;
  lineCount: number;
  /** オフィス街ごとの所要時間と乗り換え回数 */
  commutes: Partial<Record<OfficeHub, { minutes: number; transfers: number; walk?: boolean }>>;
  /** 間取りごとの家賃相場の帯の上限（円）。帯が無い間取りは入らない */
  rent: Partial<Record<RentType, number>>;
  /** 間取りごとの家賃相場の帯の下限（円）。表示用 */
  rentLow: Partial<Record<RentType, number>>;
  /** 駅の地点の、大雨のときの浸水の想定の深さの順位。区域の外なら null、データが無ければ undefined */
  floodAtStation?: number | null;
  /** 駅の地点が高潮の浸水想定区域に入るか。データが無ければ undefined */
  hightideAtStation?: boolean;
  /** 坂が多いか。データが無ければ undefined */
  hilly?: boolean;
  /** 駅のすぐそば（200m以内）に高速道路が通るか。データが無ければ undefined */
  motorwayNear?: boolean;
  /** 治安の点（0〜100）。データが無ければ undefined */
  safety?: number;
  /** 並べる順に使う総合評価（すべての軸を均等に見たもの）。無ければ null */
  overall: number | null;
};

export type FloodRule = "any" | "deep" | "inZone";
export type AnyOr<T extends string> = "any" | T;

export type Conditions = {
  office: OfficeHub | null;
  /** 通勤時間の上限（分）。null なら問わない */
  maxMinutes: number | null;
  /** 乗り換え回数の上限。null なら問わない */
  maxTransfers: number | null;
  rentType: RentType;
  /** 家賃の上限（円）。null なら問わない */
  maxRent: number | null;
  flood: FloodRule;
  hightide: AnyOr<"inZone">;
  slope: AnyOr<"noHilly">;
  lines: AnyOr<"noSingle">;
  motorway: AnyOr<"noNear">;
  safety: AnyOr<"noLow">;
};

export const DEFAULT_CONDITIONS: Conditions = {
  office: null,
  maxMinutes: null,
  maxTransfers: null,
  rentType: "oneK",
  maxRent: null,
  flood: "any",
  hightide: "any",
  slope: "any",
  lines: "any",
  motorway: "any",
  safety: "any",
};

/** 治安の点がこれ以下の駅を「件数が多いほうの2割」として外す（点は23区の駅どうしの順位） */
export const LOW_SAFETY = 20;

/** 条件の種類。結果の画面で1つずつ出し入れする単位 */
export const CONDITION_KEYS = [
  "commute",
  "transfers",
  "rent",
  "flood",
  "hightide",
  "slope",
  "lines",
  "motorway",
  "safety",
] as const;
export type ConditionKey = (typeof CONDITION_KEYS)[number];

export type Verdict = "pass" | "fail" | "unknown";

/** 1つの条件について、駅が残るか消えるか判定できないかを返す。条件が付いていなければ null */
export function judge(station: ChooseStation, c: Conditions, key: ConditionKey): Verdict | null {
  switch (key) {
    case "commute": {
      if (!c.office || c.maxMinutes === null) return null;
      const m = station.commutes[c.office];
      if (!m) return "unknown";
      return m.minutes <= c.maxMinutes ? "pass" : "fail";
    }
    case "transfers": {
      if (!c.office || c.maxTransfers === null) return null;
      const m = station.commutes[c.office];
      if (!m) return "unknown";
      return m.transfers <= c.maxTransfers ? "pass" : "fail";
    }
    case "rent": {
      if (c.maxRent === null) return null;
      const r = station.rent[c.rentType];
      if (r === undefined) return "unknown";
      return r <= c.maxRent ? "pass" : "fail";
    }
    case "flood": {
      if (c.flood === "any") return null;
      if (station.floodAtStation === undefined) return "unknown";
      if (station.floodAtStation === null) return "pass";
      if (c.flood === "inZone") return "fail";
      return station.floodAtStation >= DEEP_FLOOD_RANK ? "fail" : "pass";
    }
    case "hightide":
      if (c.hightide === "any") return null;
      if (station.hightideAtStation === undefined) return "unknown";
      return station.hightideAtStation ? "fail" : "pass";
    case "slope":
      if (c.slope === "any") return null;
      if (station.hilly === undefined) return "unknown";
      return station.hilly ? "fail" : "pass";
    case "lines":
      if (c.lines === "any") return null;
      return station.lineCount <= 1 ? "fail" : "pass";
    case "motorway":
      if (c.motorway === "any") return null;
      if (station.motorwayNear === undefined) return "unknown";
      return station.motorwayNear ? "fail" : "pass";
    case "safety":
      if (c.safety === "any") return null;
      if (station.safety === undefined) return "unknown";
      return station.safety <= LOW_SAFETY ? "fail" : "pass";
  }
}

/** いま付いている条件 */
export function activeKeys(c: Conditions): ConditionKey[] {
  const probe: ChooseStation = {
    slug: "", name: "", ward: "", lineCount: 2, commutes: {}, rent: {}, rentLow: {}, overall: null,
  };
  return CONDITION_KEYS.filter((k) => judge(probe, c, k) !== null);
}

export type Survivor = {
  station: ChooseStation;
  /** 判定できなかった条件 */
  unknown: ConditionKey[];
};

/** 条件のどれにも「消える」と判定されなかった駅。ignore に入れた条件は見ない */
export function survivors(
  stations: ChooseStation[],
  c: Conditions,
  ignore?: ConditionKey,
): Survivor[] {
  const keys = activeKeys(c).filter((k) => k !== ignore);
  const out: Survivor[] = [];
  for (const station of stations) {
    const unknown: ConditionKey[] = [];
    let failed = false;
    for (const k of keys) {
      const v = judge(station, c, k);
      if (v === "fail") {
        failed = true;
        break;
      }
      if (v === "unknown") unknown.push(k);
    }
    if (!failed) out.push({ station, unknown });
  }
  return out;
}

/** 条件ごとに、それを外すと何駅戻るか */
export function relaxGains(stations: ChooseStation[], c: Conditions): Partial<Record<ConditionKey, number>> {
  const now = survivors(stations, c).length;
  const out: Partial<Record<ConditionKey, number>> = {};
  for (const k of activeKeys(c)) {
    out[k] = survivors(stations, c, k).length - now;
  }
  return out;
}

/** 条件を外す。結果の画面で条件の札を押したときに使う */
export function withoutCondition(c: Conditions, key: ConditionKey): Conditions {
  switch (key) {
    case "commute":
      return { ...c, maxMinutes: null };
    case "transfers":
      return { ...c, maxTransfers: null };
    case "rent":
      return { ...c, maxRent: null };
    case "flood":
      return { ...c, flood: "any" };
    case "hightide":
      return { ...c, hightide: "any" };
    case "slope":
      return { ...c, slope: "any" };
    case "lines":
      return { ...c, lines: "any" };
    case "motorway":
      return { ...c, motorway: "any" };
    case "safety":
      return { ...c, safety: "any" };
  }
}

/** 残った駅の並べ方。勤務先があれば所要時間の短い順、無ければ総合評価の高い順 */
export function sortSurvivors(list: Survivor[], c: Conditions): Survivor[] {
  const office = c.office;
  return [...list].sort((a, b) => {
    if (office) {
      const ma = a.station.commutes[office]?.minutes ?? 999;
      const mb = b.station.commutes[office]?.minutes ?? 999;
      if (ma !== mb) return ma - mb;
    }
    return (b.station.overall ?? -1) - (a.station.overall ?? -1);
  });
}

// ── 条件を URL に載せる（同じ条件を家族に送れるように） ─────────────

const FLOOD_RULES: FloodRule[] = ["any", "deep", "inZone"];

export function toQuery(c: Conditions): string {
  const p = new URLSearchParams();
  if (c.office) p.set("office", c.office);
  if (c.maxMinutes !== null) p.set("min", String(c.maxMinutes));
  if (c.maxTransfers !== null) p.set("tr", String(c.maxTransfers));
  if (c.rentType !== DEFAULT_CONDITIONS.rentType) p.set("type", c.rentType);
  if (c.maxRent !== null) p.set("rent", String(c.maxRent));
  if (c.flood !== "any") p.set("flood", c.flood);
  if (c.hightide !== "any") p.set("tide", c.hightide);
  if (c.slope !== "any") p.set("slope", c.slope);
  if (c.lines !== "any") p.set("lines", c.lines);
  if (c.motorway !== "any") p.set("road", c.motorway);
  if (c.safety !== "any") p.set("safety", c.safety);
  return p.toString();
}

function intOrNull(v: string | null, min: number, max: number): number | null {
  if (v === null) return null;
  const n = Number(v);
  return Number.isInteger(n) && n >= min && n <= max ? n : null;
}

export function fromQuery(query: string): Conditions {
  const p = new URLSearchParams(query);
  const office = p.get("office");
  const type = p.get("type");
  const flood = p.get("flood") as FloodRule | null;
  return {
    office: office && (OFFICE_HUBS as readonly string[]).includes(office) ? (office as OfficeHub) : null,
    maxMinutes: intOrNull(p.get("min"), 5, 120),
    maxTransfers: intOrNull(p.get("tr"), 0, 5),
    rentType: type && (RENT_TYPES as readonly string[]).includes(type) ? (type as RentType) : DEFAULT_CONDITIONS.rentType,
    maxRent: intOrNull(p.get("rent"), 10000, 2000000),
    flood: flood && FLOOD_RULES.includes(flood) ? flood : "any",
    hightide: p.get("tide") === "inZone" ? "inZone" : "any",
    slope: p.get("slope") === "noHilly" ? "noHilly" : "any",
    lines: p.get("lines") === "noSingle" ? "noSingle" : "any",
    motorway: p.get("road") === "noNear" ? "noNear" : "any",
    safety: p.get("safety") === "noLow" ? "noLow" : "any",
  };
}
