import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { getDictionary } from "@/lib/dictionaries";
import { ACTIVE_LOCALES, isActiveLocale } from "@/lib/i18n";
import { absoluteUrl, jsonLdScript, standardMetadata } from "@/lib/seo";
import { CONTACT_EMAIL } from "@/lib/site";

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
  return standardMetadata({
    locale,
    siteName: dict.siteName,
    title: dict.about.heading,
    description: dict.about.whatThisIs,
    path: (l) => `/${l}/about`,
  });
}

/**
 * 運営者情報。家賃を「当社調べ」として出す以上、その「当社」が誰で、
 * 数字をどこから取っているのかを1ページにまとめて示す必要がある。
 */
export default async function AboutPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isActiveLocale(locale)) notFound();
  const dict = getDictionary(locale);
  const { about } = dict;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    name: about.heading,
    url: absoluteUrl(`/${locale}/about`),
    inLanguage: locale,
    publisher: {
      "@type": "Organization",
      name: about.operatorName,
      url: absoluteUrl(`/${locale}`),
      ...(CONTACT_EMAIL ? { email: CONTACT_EMAIL } : {}),
    },
  };

  return (
    <div className="space-y-10">
      <script type="application/ld+json" dangerouslySetInnerHTML={jsonLdScript(jsonLd)} />

      <header className="space-y-3">
        <h1 className="text-3xl font-bold text-ink">{about.heading}</h1>
        <p className="leading-relaxed text-ink-soft">{about.whatThisIs}</p>
      </header>

      <section className="space-y-3">
        <dl className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-[auto_1fr]">
          <dt className="text-ink-soft">{about.operatorLabel}</dt>
          <dd className="text-ink">{about.operatorName}</dd>
          {CONTACT_EMAIL && (
            <>
              <dt className="text-ink-soft">{about.contactLabel}</dt>
              <dd className="text-ink">
                <a className="underline underline-offset-2" href={`mailto:${CONTACT_EMAIL}`}>
                  {CONTACT_EMAIL}
                </a>
              </dd>
            </>
          )}
        </dl>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-ink">{about.sourcesHeading}</h2>
        <ul className="space-y-2 text-sm leading-relaxed text-ink-soft">
          {about.sources.map((line) => (
            <li key={line} className="border-l-2 border-line pl-3">
              {line}
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-ink">{about.disclaimerHeading}</h2>
        <ul className="space-y-3 text-sm leading-relaxed text-ink-soft">
          {about.disclaimers.map((line) => (
            <li key={line} className="border-l-2 border-line pl-3">
              {line}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
