import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SITE_URL } from "@/lib/site";

import "./globals.css";

/**
 * canonical と hreflang、OGP は絶対URLで出す必要がある。
 * metadataBase を置かないと、各ページで組み立てた相対パスがそのまま出てしまう。
 * 本番のURLは NEXT_PUBLIC_SITE_URL で渡す（src/lib/site.ts）。
 */
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
};

// locale ごとの <html lang> は [locale]/layout.tsx で設定する。
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
