import type { StationPhoto } from "./schema";

/** 駅ページの、写真を差し込める欄。上から順に並ぶ。 */
const PAGE_SLOTS = ["intro", "rent", "commute", "scores"] as const;

/** 1つの欄に並べる写真の数の上限。3枚以上を並べると、本文より写真が目立つ */
const PER_SLOT = 2;

/**
 * 写真を記事の途中に散らして置く（2026-10-25 に利用者と決めた。ブログのように、
 * 本文の該当する箇所の前後に写真を入れる）。
 *
 * - near のある写真（駅と路線、買い物と店）は、その欄のすぐ後ろに置く。欄が無ければ近い欄に回す
 * - Commons の駅舎の写真は「駅の使い勝手」の後ろに置く
 * - それ以外は、まだ写真の無い欄に上から1枚ずつ置き、置ききれない分は記事の最後にまとめる
 *
 * lifeKeys は「暮らしの手ざわり」の欄のうち、この駅で出すもの（StationDepth の順）。
 */
export function placePhotos(
  photos: StationPhoto[],
  lifeKeys: string[],
): { slots: Record<string, StationPhoto[]>; rest: StationPhoto[] } {
  const order = [...PAGE_SLOTS, ...lifeKeys];
  const slots: Record<string, StationPhoto[]> = {};
  const rest: StationPhoto[] = [];
  const room = (key: string) => (slots[key]?.length ?? 0) < PER_SLOT;
  const put = (key: string, p: StationPhoto) => (slots[key] ??= []).push(p);

  const target = (p: StationPhoto): string | null => {
    const near = p.near ?? (p.kind === "station" && p.source !== "flickr" ? "stationNote" : null);
    if (near === "stationNote") return lifeKeys.includes("stationNote") ? "stationNote" : "commute";
    if (near === "groceries") return lifeKeys.includes("groceries") ? "groceries" : "intro";
    return null;
  };

  const loose: StationPhoto[] = [];
  for (const p of photos) {
    const t = target(p);
    if (t === null) {
      loose.push(p);
      continue;
    }
    // 欄が埋まっていたら、その後ろの欄で空いているところへ回す
    const free = order.slice(order.indexOf(t)).find(room);
    if (free) put(free, p);
    else rest.push(p);
  }

  // 街の様子の写真は、冒頭・点数のあと・暮らしの欄・家賃のあと、の順に空いている欄へ
  const spread = ["intro", "scores", ...lifeKeys, "commute", "rent"];
  for (const p of loose) {
    const free = spread.find((k) => !slots[k]);
    if (free) put(free, p);
    else rest.push(p);
  }
  return { slots, rest };
}
