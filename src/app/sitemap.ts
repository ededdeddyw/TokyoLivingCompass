import type { MetadataRoute } from "next";

import { ACTIVE_LOCALES, X_DEFAULT_LOCALE } from "@/lib/i18n";
import { getLocalizedStations, getStationContent } from "@/lib/stations";
import { SITE_URL } from "@/lib/site";
import { OFFICE_HUBS } from "@/lib/schema";

/**
 * 同じページの各言語版を、サイトマップ側でも示す。
 * hreflang を HTML に出すだけでなくここにも書くと、
 * 検索エンジンが言語版の対応を取り違えにくくなる（docs/05-seo.md §4）。
 */
function alternates(path: (locale: string) => string, locales: readonly string[]) {
  const languages: Record<string, string> = {};
  for (const l of locales) languages[l] = `${SITE_URL}${path(l)}`;
  if (locales.includes(X_DEFAULT_LOCALE)) {
    languages["x-default"] = `${SITE_URL}${path(X_DEFAULT_LOCALE)}`;
  }
  return { languages };
}

/**
 * noindex のページは含めない（docs/05-seo.md §4）。
 * 全駅が dataQuality="seed" のあいだ、駅ページと比較ページは出力されない。
 * これは想定どおりの挙動で、実データに差し替えれば自動的に載る。
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const entries: MetadataRoute.Sitemap = [];

  for (const locale of ACTIVE_LOCALES) {
    const stations = getLocalizedStations(locale);
    const publishable = stations.filter((s) => s.dataQuality !== "seed");

    entries.push({
      url: `${SITE_URL}/${locale}`,
      priority: 1,
      changeFrequency: "weekly",
      alternates: alternates((l) => `/${l}`, ACTIVE_LOCALES),
    });
    entries.push({
      url: `${SITE_URL}/${locale}/stations`,
      priority: 0.8,
      changeFrequency: "weekly",
      alternates: alternates((l) => `/${l}/stations`, ACTIVE_LOCALES),
    });
    entries.push({
      url: `${SITE_URL}/${locale}/roster`,
      priority: 0.5,
      changeFrequency: "monthly",
      alternates: alternates((l) => `/${l}/roster`, ACTIVE_LOCALES),
    });

    for (const office of OFFICE_HUBS) {
      entries.push({
        url: `${SITE_URL}/${locale}/work/${office}`,
        priority: 0.8,
        changeFrequency: "weekly",
        alternates: alternates((l) => `/${l}/work/${office}`, ACTIVE_LOCALES),
      });
    }

    for (const station of publishable) {
      // 本文がある言語だけを言語版として挙げる（docs/04-i18n.md §5）。
      const written = ACTIVE_LOCALES.filter((l) => getStationContent(station.slug, l));
      entries.push({
        url: `${SITE_URL}/${locale}/stations/${station.slug}`,
        lastModified: station.lastReviewedAt,
        priority: 0.9,
        changeFrequency: "monthly",
        alternates: alternates((l) => `/${l}/stations/${station.slug}`, written),
      });
    }

    // 比較ページは両駅とも公開可能な場合のみ
    const publishableSlugs = new Set(publishable.map((s) => s.slug));
    const seen = new Set<string>();
    for (const station of publishable) {
      for (const other of station.similarStations) {
        if (!publishableSlugs.has(other)) continue;
        const key = [station.slug, other].sort().join("-vs-");
        if (seen.has(key)) continue;
        seen.add(key);
        entries.push({ url: `${SITE_URL}/${locale}/compare/${key}`, priority: 0.6 });
      }
    }
  }

  return entries;
}
