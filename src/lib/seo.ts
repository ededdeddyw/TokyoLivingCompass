import { ACTIVE_LOCALES, X_DEFAULT_LOCALE, type ActiveLocale } from "./i18n";
import { SITE_URL } from "./site";

/**
 * 検索結果と生成AIの引用に向けた共通処理（docs/05-seo.md §4）。
 *
 * 駅ページは458駅 × 4言語ある。タイトルと説明文の作り方をページごとに書くと、
 * 長さも語順もばらつくので、ここに集める。
 */

/** 検索結果でタイトルが省略されない長さ。全角でおよそ30字、半角で60字ほど。 */
const TITLE_MAX = 60;
/** 説明文も同じく、途中で切られない長さに収める。 */
const DESCRIPTION_MAX = 155;

/** 全角を2文字、半角を1文字として数える。日本語と英語で同じ関数を使うため。 */
function width(text: string): number {
  let n = 0;
  for (const ch of text) n += /[\x20-\x7e｡-ﾟ]/.test(ch) ? 1 : 2;
  return n;
}

/** 指定の幅に収める。切るときは文の区切りを優先し、無ければ末尾に「…」を付ける。 */
export function clamp(text: string, max: number): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (width(clean) <= max) return clean;

  // 文の区切りで切れるなら、そこで切る。途中で切れた文を見せないため。
  const sentences = clean.split(/(?<=[。．.!?！？])\s*/);
  let built = "";
  for (const s of sentences) {
    if (width(built + s) > max) break;
    built += s;
  }
  if (width(built) >= max * 0.6) return built.trim();

  let cut = "";
  for (const ch of clean) {
    if (width(cut + ch) > max - 1) break;
    cut += ch;
  }
  return cut.trim() + "…";
}

export function pageTitle(text: string): string {
  return clamp(text, TITLE_MAX);
}

export function pageDescription(text: string): string {
  return clamp(text, DESCRIPTION_MAX);
}

/**
 * hreflang。そのロケールに本文がある言語だけを出す（docs/04-i18n.md §4・§5）。
 * x-default は、どの言語にも一致しなかった読み手が最初に見るページを指す。
 */
export function languageAlternates(
  path: (locale: ActiveLocale) => string,
  exists: (locale: ActiveLocale) => boolean = () => true,
): Record<string, string> {
  const languages: Record<string, string> = {};
  for (const locale of ACTIVE_LOCALES) {
    if (exists(locale)) languages[locale] = path(locale);
  }
  if (exists(X_DEFAULT_LOCALE)) {
    languages["x-default"] = path(X_DEFAULT_LOCALE);
  }
  return languages;
}

/** OGP。画像は用意していないので、テキストだけで成立する形にしておく。 */
export function openGraph(args: {
  locale: ActiveLocale;
  title: string;
  description: string;
  path: string;
  siteName: string;
}) {
  return {
    type: "website" as const,
    locale: args.locale,
    siteName: args.siteName,
    title: args.title,
    description: args.description,
    url: `${SITE_URL}${args.path}`,
  };
}

/** JSON-LD を1つの <script> にまとめて出す。 */
export function jsonLdScript(data: unknown) {
  return {
    __html: JSON.stringify(data).replace(/</g, "\\u003c"),
  };
}

export function absoluteUrl(path: string): string {
  return `${SITE_URL}${path}`;
}

/**
 * ページ種別によらず共通の metadata。
 * canonical・hreflang・OGP を書き忘れるページが出ないよう、1か所にまとめる。
 */
export function standardMetadata(args: {
  locale: ActiveLocale;
  siteName: string;
  title: string;
  description: string;
  /** ロケールを受け取ってパスを返す。canonical と hreflang の両方に使う。 */
  path: (locale: ActiveLocale) => string;
  /** その言語にページがあるか。既定はすべての言語にあるものとする。 */
  exists?: (locale: ActiveLocale) => boolean;
  noindex?: boolean;
}) {
  const title = pageTitle(args.title);
  const description = pageDescription(args.description);
  const path = args.path(args.locale);
  return {
    title,
    description,
    alternates: {
      canonical: path,
      languages: languageAlternates(args.path, args.exists),
    },
    openGraph: openGraph({
      locale: args.locale,
      title,
      description,
      path,
      siteName: args.siteName,
    }),
    twitter: { card: "summary" as const, title, description },
    ...(args.noindex ? { robots: { index: false, follow: true } } : {}),
  };
}
