import type { ActiveLocale } from "./i18n";

/** 家賃の表示。日本語は「8.5万円」ではなく実額のままにする（比較のため）。 */
export function formatYen(amount: number, locale: ActiveLocale): string {
  return new Intl.NumberFormat(locale === "ja" ? "ja-JP" : "en-US", {
    style: "currency",
    currency: "JPY",
    maximumFractionDigits: 0,
  }).format(amount);
}
