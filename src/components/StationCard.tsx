import Link from "next/link";

import type { Dictionary } from "@/lib/dictionaries";
import type { ActiveLocale } from "@/lib/i18n";
import type { LocalizedStation, RentType } from "@/lib/schema";
import { formatYen } from "@/lib/format";

export function StationCard({
  station,
  locale,
  dict,
  overall,
  rentType = "oneK",
  footnote,
}: {
  station: LocalizedStation;
  locale: ActiveLocale;
  dict: Dictionary;
  overall: number | null;
  rentType?: RentType;
  footnote?: string;
}) {
  return (
    <Link
      href={`/${locale}/stations/${station.slug}`}
      className="block rounded-lg border border-line bg-surface p-5 transition hover:border-accent hover:shadow-sm"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-lg font-semibold text-ink">
          {station.content.name}
          {locale !== "ja" && (
            <span className="ml-2 text-sm font-normal text-ink-soft">
              {station.nameJa}
            </span>
          )}
        </h3>
        <span className="shrink-0 text-sm tabular-nums text-ink-soft">
          {dict.station.overall}{" "}
          <strong className="text-ink">
            {overall === null ? dict.dataQuality.notAvailable : overall.toFixed(1)}
          </strong>
        </span>
      </div>

      <p className="mt-2 text-sm leading-relaxed text-ink-soft">
        {station.content.tagline}
      </p>

      <p className="mt-3 text-sm tabular-nums text-ink-soft">
        {dict.rentTypes[rentType]}{" "}
        {station.rent
          ? `${formatYen(station.rent[rentType], locale)}${dict.station.perMonth}`
          : dict.dataQuality.notAvailable}
      </p>

      {footnote && <p className="mt-2 text-sm text-accent">{footnote}</p>}
    </Link>
  );
}
