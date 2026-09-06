/** サイト全体の設定。デプロイ先が決まったら NEXT_PUBLIC_SITE_URL を設定する。 */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
