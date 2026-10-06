/**
 * サイト全体の設定。
 *
 * 本番のアドレスは `NEXT_PUBLIC_SITE_URL` で渡す。
 * 未設定のときは Vercel が用意する環境変数から組み立てるので、
 * デプロイしただけで sitemap.xml と canonical が正しいアドレスを指す。
 * どちらも無いときだけ localhost にする（手元で開発しているとき）。
 */
const vercelHost =
  process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (vercelHost ? `https://${vercelHost}` : "http://localhost:3000");

/**
 * 独自ドメインが決まっているか。
 *
 * `NEXT_PUBLIC_SITE_URL` を設定するまでは、vercel.app の仮のアドレスで動いている。
 * 仮のアドレスを検索エンジンに登録させると、独自ドメインに移したあとも
 * 同じ内容のページが2つある状態になり、どちらを正とするかで検索順位を損なう。
 * また、本文をまだ見直している途中なので、読み手に見つかる状態にはしたくない。
 * そのため、設定するまでは検索エンジンに登録させない。
 */
export const IS_CANONICAL_HOST = Boolean(process.env.NEXT_PUBLIC_SITE_URL);

/**
 * 問い合わせ先。運営者情報ページ（/[locale]/about）に出す。
 *
 * ソースに直接書かない。公開したページのアドレスは収集され、迷惑メールが届く。
 * どのアドレスを出すかは運用の判断なので、環境変数で渡す。
 * 未設定のあいだは、運営者情報ページに連絡先の行を出さない。
 */
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? "";
