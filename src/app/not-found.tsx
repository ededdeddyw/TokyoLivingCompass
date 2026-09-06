import Link from "next/link";

import "./globals.css";

/** ルートレイアウトは <html> を持たないため、404 側で用意する。 */
export default function NotFound() {
  return (
    <html lang="en">
      <body className="min-h-screen bg-canvas text-ink antialiased">
        <main className="mx-auto max-w-2xl px-5 py-24 text-center">
          <h1 className="text-2xl font-bold">404</h1>
          <p className="mt-3 text-ink-soft">
            This page does not exist. / このページは存在しません。
          </p>
          <Link href="/" className="mt-6 inline-block text-accent hover:underline">
            Tokyo Living Compass
          </Link>
        </main>
      </body>
    </html>
  );
}
