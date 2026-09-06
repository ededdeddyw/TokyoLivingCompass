import type { ReactNode } from "react";

import "./globals.css";

// locale ごとの <html lang> は [locale]/layout.tsx で設定する。
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
