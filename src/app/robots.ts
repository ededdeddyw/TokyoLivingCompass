import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // 条件をクエリで指定したページは index させない（docs/05-seo.md §2.4）。
      disallow: ["/*?*"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
