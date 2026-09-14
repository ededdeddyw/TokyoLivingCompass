import { ACTIVE_LOCALES, isActiveLocale } from "../src/lib/i18n";
import { DEPTH_FIELDS, depthFilled, OFFICE_HUBS, SCORE_AXES } from "../src/lib/schema";
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

  // 全オフィス駅への所要時間があるか（欠損があると逆引き検索から漏れる）
  const covered = new Set(station.commutes.map((c) => c.to));
  for (const office of OFFICE_HUBS) {
    if (!covered.has(office)) {
      errors.push(`${station.slug}: 所要時間に "${office}" がありません。`);
    }
  }
  if (station.commutes.length !== new Set(station.commutes.map((c) => c.to)).size) {
    errors.push(`${station.slug}: commutes に重複した行き先があります。`);
  }

  // 家賃の大小関係。部屋が広いほど高いのが普通なので、崩れていたら入力ミスを疑う。
  // ただしワンルームと1Kは広さが近く、実データでは前後が入れ替わる駅がある
  // （六本木・清澄白河など）。ここは順序を求めず、離れすぎたときだけ警告する。
  if (station.rent) {
    const { oneRoom, oneK, oneLDK, twoLDK } = station.rent;
    if (!(oneK <= oneLDK && oneLDK <= twoLDK)) {
      errors.push(
        `${station.slug}: 家賃の大小関係が不自然です (1K ${oneK} / 1LDK ${oneLDK} / 2LDK ${twoLDK})。`,
      );
    }
    if (oneRoom > oneLDK) {
      errors.push(
        `${station.slug}: ワンルームが1LDKより高くなっています (1R ${oneRoom} / 1LDK ${oneLDK})。`,
      );
    }
    if (Math.abs(oneRoom - oneK) > Math.max(oneRoom, oneK) * 0.3) {
      warnings.push(
        `${station.slug}: ワンルームと1Kの差が3割を超えています (1R ${oneRoom} / 1K ${oneK})。集計対象の違いかもしれません。`,
      );
    }
  }

  if (station.dataQuality === "roster") {
    // プロフィール未作成。エラーではない。
  } else if (station.dataQuality === "seed") {
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

    // 公開情報からまとめた在住者コメントは、何をもとにしたかを必ず持たせる。
    // 出典が無いと、読み手も書き手も、あとから裏を取れない。
    if (content.residentCommentBy === "compiled") {
      if (!content.residentCommentSources || content.residentCommentSources.length === 0) {
        errors.push(
          `${locale}/${slug}: residentCommentBy が "compiled" ですが、` +
            `residentCommentSources がありません。もとにした情報を書いてください。`,
        );
      }
    }
    if (content.residentCommentSources && content.residentCommentBy !== "compiled") {
      warnings.push(
        `${locale}/${slug}: residentCommentSources がありますが、` +
          `residentCommentBy が "compiled" ではありません。`,
      );
    }

    // 複数路線が乗り入れる駅では、路線ごとに改札の位置も出口の先の街並みも変わる。
    // 片方の路線の出口しか書いていないと、もう片方を使う人には情報にならない。
    const rosterEntry = rosterBySlug.get(slug);
    if (content.exits && content.exits.length > 0 && rosterEntry && rosterEntry.lineIds.length > 1) {
      const written = content.exits.map((e) => e.line ?? "").join(" ");
      // 出口の説明は、その言語の路線名で書かれる。日本語名と英語名のどちらかが
      // 出ていれば、その路線について書かれているとみなす。
      const missing = rosterEntry.lineIds
        .map((id) => lines.get(id))
        .filter((line): line is NonNullable<typeof line> => Boolean(line))
        .filter(
          (line) =>
            !written.includes(shortLineName(line.nameJa)) &&
            !written.includes(shortLineName(line.nameEn)),
        )
        .map((line) => line.nameJa);
      if (missing.length > 0) {
        warnings.push(
          `${locale}/${slug}: 出口の説明に ${missing.join("・")} が出てきません。` +
            `路線ごとに改札の位置が違うため、路線ごとに書いてください。`,
        );
      }
    }
  }
}

/** 「JR中央線(快速)」と「JR中央線（快速）」のような表記ゆれを避けて突き合わせる。 */
function shortLineName(name: string): string {
  return name.replace(/[(（].*$/, "").trim();
}

// 店名は、実在を確認していないものを載せてはいけない。
// スキーマが sourceUrl と verifiedAt を必須にしているので、ここでは鮮度と件数を見る。
const STORE_STALE_DAYS = 365;
const staleStores: string[] = [];
const noGroceries: string[] = [];
for (const locale of listContentLocales()) {
  if (!isActiveLocale(locale)) continue;
  for (const slug of listContentSlugs(locale)) {
    const content = getStationContent(slug, locale);
    if (!content) continue;
    if (!content.groceries || content.groceries.length === 0) {
      noGroceries.push(slug);
      continue;
    }
    for (const store of content.groceries) {
      const age = (Date.now() - Date.parse(store.verifiedAt)) / 86_400_000;
      if (age > STORE_STALE_DAYS) staleStores.push(`${slug}/${store.name}`);
    }
  }
}
if (noGroceries.length > 0) {
  warnings.push(
    `${noGroceries.length}駅に、実在を確認できた店が1つもありません: ${noGroceries.join("、")}`,
  );
}
if (staleStores.length > 0) {
  warnings.push(
    `${staleStores.length}件の店が、確認から1年以上たっています。閉店していないか見直してください: ` +
      staleStores.join("、"),
  );
}

// 家賃の帯（当社調べ）。出典を明示して出す以上、元の観測値が残っていることを確かめる。
const bandedStations = stations.filter((s) => s.rentBands);
const provisionalBands: string[] = [];
for (const station of bandedStations) {
  const b = station.rentBands!;
  if (b.sources.length < 2) {
    errors.push(
      `${station.slug}: 家賃の帯の出典が ${b.sources.length} 件しかありません。` +
        `「複数サイトの平均」と書く以上、2件以上必要です。`,
    );
  }
  if (!b.verified) provisionalBands.push(station.slug);
}
if (provisionalBands.length > 0) {
  warnings.push(
    `${provisionalBands.length}駅の家賃の帯が未確認です（掲載元のページを開いての確認が済んでいない）。` +
      `駅ページには暫定値と表示されます: ${provisionalBands.join("、")}`,
  );
}

// 充足率レポート。458駅を段階的に埋めていくので、
// 「いま何がどれだけ埋まっているか」が一目で分かる形にする。
const total = stations.length;
const pct = (n: number) => `${Math.round((n / total) * 100)}%`.padStart(4);
const bar = (n: number) => {
  const filled = Math.round((n / total) * 24);
  return "\u2588".repeat(filled) + "\u2591".repeat(24 - filled);
};

const layers: [string, number][] = [
  ["所在区・路線", stations.length],
  ["所要時間（計算）", stations.filter((s) => s.commutes.length === OFFICE_HUBS.length).length],
  ["朝の混雑・始発", stations.filter((s) => s.morningCrowding !== undefined).length],
  ["家賃", stations.filter((s) => s.rent !== undefined).length],
  ["スコア（1軸以上）", stations.filter((s) => Object.keys(s.scores).length > 0).length],
  ["スコア（16軸すべて）", stations.filter((s) => Object.keys(s.scores).length === SCORE_AXES.length).length],
  ["周辺施設", stations.filter((s) => s.facilities !== undefined).length],
];
for (const locale of ACTIVE_LOCALES) {
  layers.push([`コンテンツ（${locale}）`, listContentSlugs(locale).filter((x) => slugs.has(x)).length]);
}

// 日本語コンテンツの「深さ」。既存のまとめ記事に勝てるかはここで決まる
// （docs/12-quality-standard.md）。
const jaContents = listContentSlugs("ja")
  .filter((x) => slugs.has(x))
  .map((slug) => ({ slug, content: getStationContent(slug, "ja")! }))
  .filter((x) => x.content);

const complete = jaContents.filter(
  (x) => depthFilled(x.content).length === DEPTH_FIELDS.length,
);
layers.push([`深さ${DEPTH_FIELDS.length}層すべて（ja）`, complete.length]);

console.log(
  `ロースター: ${total}駅 / 路線: ${lines.size} / ロケール: ${ACTIVE_LOCALES.join(", ")}\n`,
);
console.log("データ充足率");
for (const [label, n] of layers) {
  console.log(`  ${label.padEnd(22)} ${bar(n)} ${String(n).padStart(3)}/${total} ${pct(n)}`);
}
console.log();

if (jaContents.length > 0) {
  console.log(`日本語コンテンツの深さ（${DEPTH_FIELDS.length}層中いくつ書けているか）`);
  const sorted = [...jaContents].sort(
    (a, b) => depthFilled(b.content).length - depthFilled(a.content).length,
  );
  for (const { slug, content } of sorted) {
    const filled = depthFilled(content);
    const missing = DEPTH_FIELDS.filter((f) => !filled.includes(f));
    const mark =
      filled.length === DEPTH_FIELDS.length
        ? "完成"
        : `${filled.length}/${DEPTH_FIELDS.length}`;
    console.log(
      `  ${content.name.padEnd(10)} ${mark.padStart(5)}` +
        (missing.length > 0 && missing.length <= 4 ? `  未: ${missing.join(", ")}` : ""),
    );
  }
  console.log();
}

if (seedStations.length > 0) {
  warnings.push(
    `${seedStations.length}駅が dataQuality="seed"（推定値。公開不可・docs/05-seo.md §3）`,
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
