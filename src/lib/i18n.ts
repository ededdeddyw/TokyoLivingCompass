/** ロケール定義の単一の正（docs/04-i18n.md）。 */

/**
 * 実運用中のロケール。ページ生成とサイトマップの対象になる。
 *
 * まず日本語で458駅を作り切り、そのうえで英語・簡体字中国語・韓国語を開いた。
 * 在留外国人の数が多い順に3言語を選んでいる（docs/04-i18n.md §0）。
 * 残る言語は構造としては対応済みで、コンテンツが揃った順に開く。
 */
export const ACTIVE_LOCALES = ["ja", "en", "zh-Hans", "ko"] as const;

/** 構造として対応済みで、コンテンツ整備を待っているロケール。 */
export const PLANNED_LOCALES = [
  "zh-Hant",
  "vi",
  "th",
  "id",
  "ne",
  "tl",
  "fr",
  "es",
  "de",
  "pt",
] as const;

export const LOCALES = [...ACTIVE_LOCALES, ...PLANNED_LOCALES] as const;

export type Locale = (typeof LOCALES)[number];
export type ActiveLocale = (typeof ACTIVE_LOCALES)[number];

export const DEFAULT_LOCALE: ActiveLocale = "ja";

/** hreflang の x-default が指すロケール。多言語展開時に en へ戻す。 */
export const X_DEFAULT_LOCALE: ActiveLocale = "ja";

export const LOCALE_LABELS: Record<Locale, string> = {
  ja: "日本語",
  en: "English",
  "zh-Hans": "简体中文",
  "zh-Hant": "繁體中文",
  ko: "한국어",
  vi: "Tiếng Việt",
  th: "ไทย",
  id: "Bahasa Indonesia",
  ne: "नेपाली",
  tl: "Tagalog",
  fr: "Français",
  es: "Español",
  de: "Deutsch",
  pt: "Português",
};

export function isActiveLocale(value: string): value is ActiveLocale {
  return (ACTIVE_LOCALES as readonly string[]).includes(value);
}

/** Accept-Language ヘッダから最も近い実運用ロケールを選ぶ。 */
export function pickLocale(acceptLanguage: string | null): ActiveLocale {
  if (!acceptLanguage) return DEFAULT_LOCALE;

  const ranked = acceptLanguage
    .split(",")
    .map((part) => {
      const [tag, ...params] = part.trim().split(";");
      const q = params
        .map((p) => p.trim())
        .find((p) => p.startsWith("q="))
        ?.slice(2);
      return { tag: tag.trim().toLowerCase(), q: q ? Number(q) : 1 };
    })
    .filter((entry) => entry.tag.length > 0 && !Number.isNaN(entry.q))
    .sort((a, b) => b.q - a.q);

  for (const { tag } of ranked) {
    const exact = ACTIVE_LOCALES.find((l) => l.toLowerCase() === tag);
    if (exact) return exact;
    const base = tag.split("-")[0];
    const partial = ACTIVE_LOCALES.find(
      (l) => l.toLowerCase().split("-")[0] === base,
    );
    if (partial) return partial;
  }

  return DEFAULT_LOCALE;
}
