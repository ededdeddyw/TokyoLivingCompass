import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { pickLocale } from "@/lib/i18n";

/** ルートは言語判定して locale つき URL へ送る（docs/04-i18n.md §3）。 */
export default async function RootPage() {
  const headerList = await headers();
  redirect(`/${pickLocale(headerList.get("accept-language"))}`);
}
