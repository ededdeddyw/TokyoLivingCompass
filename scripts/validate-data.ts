import { ACTIVE_LOCALES, isActiveLocale } from "../src/lib/i18n";
import { OFFICE_HUBS } from "../src/lib/schema";
import {
  getAllStations,
  getLines,
  getRoster,
  getStationContent,
  listContentLocales,
  listContentSlugs,
} from "../src/lib/stations";

/**
 * ビルド前のデータ検証（docs/07-architecture.md §4）。
 * スキーマ違反はローダーが throw する。ここではファイル間の整合性を見る。
 */

const errors: string[] = [];
const warnings: string[] = [];
/** 公開できない状態のデータ。件数だけを集計して最後にまとめて報告する。 */
const seedStations: string[] = [];
const placeholderContent: string[] = [];

const stations = getAllStations();
const slugs = new Set(stations.map((s) => s.slug));

if (stations.length === 0) {
  errors.push("駅データが1件もありません。");
}

for (const station of stations) {
  // 似ている駅の参照先が実在するか
  for (const similar of station.similarStations) {
    if (!slugs.has(similar)) {
      errors.push(`${station.slug}: similarStations の "${similar}" が存在しません。`);
    }
    if (similar === station.slug) {
      errors.push(`${station.slug}: similarStations が自分自身を参照しています。`);
    }
  }

  // 全オフィス駅への commutes を持つか（欠損があると逆引き検索から漏れる）
  const covered = new Set(station.commutes.map((c) => c.to));
  for (const office of OFFICE_HUBS) {
    if (!covered.has(office)) {
      errors.push(`${station.slug}: commutes に "${office}" がありません。`);
    }
  }
  if (station.commutes.length !== new Set(station.commutes.map((c) => c.to)).size) {
    errors.push(`${station.slug}: commutes に重複した行き先があります。`);
  }

  // 家賃の大小関係（間取りが広いほど高い、が崩れていたら入力ミスの可能性が高い）
  const { oneRoom, oneK, oneLDK, twoLDK } = station.rent;
  if (!(oneRoom <= oneK && oneK <= oneLDK && oneLDK <= twoLDK)) {
    errors.push(
      `${station.slug}: 家賃の大小関係が不自然です (1R ${oneRoom} / 1K ${oneK} / 1LDK ${oneLDK} / 2LDK ${twoLDK})。`,
    );
  }

  if (station.dataQuality === "seed") {
    seedStations.push(station.slug);
  } else if (!station.sources?.rent) {
    // 出典のないデータを "reviewed" 以上に昇格させられない
    // （docs/08-data-sources-rent.md §6）。
    errors.push(
      `${station.slug}: dataQuality="${station.dataQuality}" だが sources.rent がありません。`,
    );
  }
}

// ロースターと路線マスタの検証
const lines = getLines();
const roster = getRoster();
const rosterBySlug = new Map(roster.map((r) => [r.slug, r]));

if (rosterBySlug.size !== roster.length) {
  const seen = new Set<string>();
  for (const r of roster) {
    if (seen.has(r.slug)) errors.push(`ロースターの slug が重複しています: ${r.slug}`);
    seen.add(r.slug);
  }
}

for (const r of roster) {
  for (const id of r.lineIds) {
    if (!lines.has(id)) {
      errors.push(`ロースター ${r.slug}: 未知の路線 id "${id}"`);
    }
  }
}

// 詳細プロフィールはロースターの部分集合でなければならない
for (const station of stations) {
  for (const id of station.lineIds) {
    if (!lines.has(id)) {
      errors.push(`${station.slug}: 未知の路線 id "${id}"`);
    }
  }
  const entry = rosterBySlug.get(station.slug);
  if (!entry) {
    errors.push(`${station.slug}: ロースターに存在しません。`);
    continue;
  }
  if (entry.nameJa !== station.nameJa) {
    errors.push(
      `${station.slug}: 駅名がロースターと一致しません (プロフィール="${station.nameJa}" / ロースター="${entry.nameJa}")`,
    );
  }
  if (entry.ward !== station.ward || entry.wardNameJa !== station.wardNameJa) {
    errors.push(
      `${station.slug}: 所在区がロースターと一致しません (プロフィール="${station.wardNameJa}" / ロースター="${entry.wardNameJa}")`,
    );
  }
}

// コンテンツ側の検証
for (const locale of listContentLocales()) {
  if (!isActiveLocale(locale)) {
    warnings.push(`data/content/${locale} は実運用ロケールではありません（src/lib/i18n.ts）。`);
    continue;
  }

  for (const slug of listContentSlugs(locale)) {
    if (!slugs.has(slug)) {
      errors.push(`data/content/${locale}/${slug}.json に対応する駅データがありません。`);
      continue;
    }
    const content = getStationContent(slug, locale);
    if (!content) continue;
    if (content.slug !== slug) {
      errors.push(`data/content/${locale}/${slug}.json: slug が "${content.slug}" になっています。`);
    }
    if (content.locale !== locale) {
      errors.push(`data/content/${locale}/${slug}.json: locale が "${content.locale}" になっています。`);
    }
    if (content.authoredBy === "seed-placeholder") {
      placeholderContent.push(`${locale}/${slug}`);
    }
  }
}

// 各ロケールのカバレッジ
for (const locale of ACTIVE_LOCALES) {
  const covered = new Set(listContentSlugs(locale));
  const missing = stations.filter((s) => !covered.has(s.slug)).map((s) => s.slug);
  if (missing.length > 0) {
    warnings.push(
      `locale "${locale}" の未翻訳: ${missing.join(", ")}（これらの駅ページは生成されません）`,
    );
  }
}

console.log(
  `ロースター: ${roster.length}駅 / 路線: ${lines.size} / ` +
    `詳細プロフィール: ${stations.length}駅 / ロケール: ${ACTIVE_LOCALES.join(", ")}`,
);

const profiled = new Set(stations.map((s) => s.slug));
warnings.push(
  `ロースター ${roster.length}駅のうち、詳細プロフィールがあるのは ${profiled.size}駅` +
    `（残り ${roster.length - profiled.size}駅は駅名・所在区・路線のみ）`,
);

if (seedStations.length > 0) {
  warnings.push(
    `${seedStations.length}駅が dataQuality="seed"（推定値。公開不可・docs/05-seo.md §3）: ${seedStations.join(", ")}`,
  );
}
if (placeholderContent.length > 0) {
  warnings.push(
    `${placeholderContent.length}件のコンテンツが authoredBy="seed-placeholder"（仮テキスト。公開不可）`,
  );
}

if (warnings.length > 0) {
  console.log(`\n警告 (${warnings.length}):`);
  for (const w of warnings) console.log(`  - ${w}`);
}

if (errors.length > 0) {
  console.error(`\nエラー (${errors.length}):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

console.log("\nデータ検証: OK");
