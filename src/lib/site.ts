/** サイト全体の設定。デプロイ先が決まったら NEXT_PUBLIC_SITE_URL を設定する。 */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/** 問い合わせ先。運営者情報ページ（/[locale]/about）に出す。 */
export const CONTACT_EMAIL = "mercibeaucoup.leon@gmail.com";
