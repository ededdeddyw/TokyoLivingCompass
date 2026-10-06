import type { Metadata } from "next";
import type { ReactNode } from "react";

import { IS_CANONICAL_HOST, SITE_URL } from "@/lib/site";

import "./globals.css";

/**
 * canonical と hreflang、OGP は絶対URLで出す必要がある。
 * metadataBase を置かないと、各ページで組み立てた相対パスがそのまま出てしまう。
 * 本番のURLは NEXT_PUBLIC_SITE_URL で渡す（src/lib/site.ts）。
 *
 * 独自ドメインが決まるまでは noindex を付ける。robots.txt だけでは、
 * 他のページから貼られたリンクをたどって登録されることがある
 * （理由は src/lib/site.ts の IS_CANONICAL_HOST にある）。
 */
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  ...(IS_CANONICAL_HOST ? {} : { robots: { index: false, follow: false } }),
};

// locale ごとの <html lang> は [locale]/layout.tsx で設定する。
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
