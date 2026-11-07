import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ChooseTool } from "@/components/choose/ChooseTool";
import type { ChooseStation } from "@/lib/choose";
import { CHOOSE_TEXT } from "@/lib/choose-text";
import { getDictionary } from "@/lib/dictionaries";
import { ACTIVE_LOCALES, isActiveLocale } from "@/lib/i18n";
import { RENT_TYPES, type OfficeHub, type RentType } from "@/lib/schema";
import { overallScoreForPreset } from "@/lib/scoring";
import { standardMetadata } from "@/lib/seo";
import { getChooseFacts, getLocalizedStations } from "@/lib/stations";

/**
 * 条件に合わない駅を消していくページ（docs/20-choose.md）。
 * 判定に使う値だけを全駅ぶん組み立てて、画面の部品に渡す。判定と数え直しはブラウザで行う。
 */
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
  const text = CHOOSE_TEXT[locale];
  return standardMetadata({
    locale,
    siteName: dict.siteName,
    title: text.title,
    description: text.lead,
    path: (l) => `/${l}/choose`,
  });
}

export default async function ChoosePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isActiveLocale(locale)) notFound();
  const dict = getDictionary(locale);
  const text = CHOOSE_TEXT[locale];
  const facts = getChooseFacts();

  // 住宅がほとんどない駅（空港・倉庫街など）は、住む駅の候補として出さない
  const stations: ChooseStation[] = getLocalizedStations(locale)
    .filter((s) => !s.nonResidential)
    .map((s) => {
      const rent: Partial<Record<RentType, number>> = {};
      const rentLow: Partial<Record<RentType, number>> = {};
      for (const t of RENT_TYPES) {
        const b = s.rentBands?.bands[t];
        if (b) {
          rent[t] = b.high;
          rentLow[t] = b.low;
        }
      }
      const commutes: ChooseStation["commutes"] = {};
      for (const c of s.commutes) {
        commutes[c.to as OfficeHub] = { minutes: c.minutes, transfers: c.transfers, ...(c.walk ? { walk: true } : {}) };
      }
      const f = facts[s.slug] ?? {};
      return {
        slug: s.slug,
        name: s.content.name,
        ward: locale === "ja" ? s.wardNameJa : s.ward.charAt(0).toUpperCase() + s.ward.slice(1),
        lineCount: s.lineIds.length,
        commutes,
        rent,
        rentLow,
        ...(f.floodAtStation !== undefined ? { floodAtStation: f.floodAtStation } : {}),
        ...(f.hightideAtStation !== undefined ? { hightideAtStation: f.hightideAtStation } : {}),
        ...(f.hilly !== undefined ? { hilly: f.hilly } : {}),
        ...(f.motorwayNear !== undefined ? { motorwayNear: f.motorwayNear } : {}),
        ...(s.scores.safety !== undefined ? { safety: s.scores.safety } : {}),
        overall: overallScoreForPreset(s, "balanced"),
      };
    });

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold leading-tight text-ink">{text.title}</h1>
        <p className="max-w-2xl leading-relaxed text-ink-soft">{text.lead}</p>
      </header>
      <ChooseTool
        locale={locale}
        stations={stations}
        text={text}
        offices={dict.offices}
        rentTypes={dict.rentTypes}
      />
    </div>
  );
}
