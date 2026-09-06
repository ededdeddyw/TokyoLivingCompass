import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import { getDictionary } from "@/lib/dictionaries";
import { ACTIVE_LOCALES, isActiveLocale, LOCALE_LABELS } from "@/lib/i18n";

export function generateStaticParams() {
  return ACTIVE_LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  if (!isActiveLocale(locale)) return {};
  const dict = getDictionary(locale);
  return {
    title: { default: dict.siteName, template: `%s | ${dict.siteName}` },
    description: dict.tagline,
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isActiveLocale(locale)) notFound();
  const dict = getDictionary(locale);

  return (
    <html lang={locale}>
      <body className="min-h-screen bg-canvas text-ink antialiased">
        <header className="border-b border-line bg-surface">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-5 py-4">
            <Link href={`/${locale}`} className="text-base font-semibold text-ink">
              {dict.siteName}
            </Link>
            <nav className="flex gap-5 text-sm text-ink-soft">
              <Link href={`/${locale}/stations`} className="hover:text-accent">
                {dict.nav.stations}
              </Link>
              <Link href={`/${locale}/work/toranomon`} className="hover:text-accent">
                {dict.nav.find}
              </Link>
            </nav>
            <div className="ml-auto flex gap-3 text-sm">
              {ACTIVE_LOCALES.map((l) => (
                <Link
                  key={l}
                  href={`/${l}`}
                  className={
                    l === locale ? "font-medium text-ink" : "text-ink-soft hover:text-accent"
                  }
                  hrefLang={l}
                >
                  {LOCALE_LABELS[l]}
                </Link>
              ))}
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-5 py-10">{children}</main>

        <footer className="border-t border-line bg-surface">
          <div className="mx-auto max-w-5xl px-5 py-6 text-sm text-ink-soft">
            {dict.siteName} — {dict.tagline}
          </div>
        </footer>
      </body>
    </html>
  );
}
