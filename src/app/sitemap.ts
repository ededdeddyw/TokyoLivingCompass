import type { MetadataRoute } from "next";

import { ACTIVE_LOCALES } from "@/lib/i18n";
import { getLocalizedStations } from "@/lib/stations";
import { SITE_URL } from "@/lib/site";
import { OFFICE_HUBS } from "@/lib/schema";

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

    entries.push({ url: `${SITE_URL}/${locale}`, priority: 1 });
    entries.push({ url: `${SITE_URL}/${locale}/stations`, priority: 0.8 });
    entries.push({ url: `${SITE_URL}/${locale}/roster`, priority: 0.5 });

    for (const office of OFFICE_HUBS) {
      entries.push({ url: `${SITE_URL}/${locale}/work/${office}`, priority: 0.8 });
    }

    for (const station of publishable) {
      entries.push({
        url: `${SITE_URL}/${locale}/stations/${station.slug}`,
        lastModified: station.lastReviewedAt,
        priority: 0.9,
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
