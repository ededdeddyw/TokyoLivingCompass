import { ACTIVE_LOCALES, isActiveLocale } from "../src/lib/i18n";
import { OFFICE_HUBS } from "../src/lib/schema";
import {
  getAllStations,
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

console.log(`駅: ${stations.length}件 / ロケール: ${ACTIVE_LOCALES.join(", ")}`);

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
