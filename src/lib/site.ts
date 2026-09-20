/** サイト全体の設定。デプロイ先が決まったら NEXT_PUBLIC_SITE_URL を設定する。 */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * 問い合わせ先。運営者情報ページ（/[locale]/about）に出す。
 *
 * ソースに直接書かない。公開したページのアドレスは収集され、迷惑メールが届く。
 * どのアドレスを出すかは運用の判断なので、環境変数で渡す。
 * 未設定のあいだは、運営者情報ページに連絡先の行を出さない。
 */
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? "";
