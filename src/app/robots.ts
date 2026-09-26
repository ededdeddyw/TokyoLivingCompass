import type { MetadataRoute } from "next";

import { IS_CANONICAL_HOST, SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  // 独自ドメインが決まるまでは、仮のアドレスを検索エンジンに登録させない
  // （理由は src/lib/site.ts の IS_CANONICAL_HOST にある）。
  if (!IS_CANONICAL_HOST) {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
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
