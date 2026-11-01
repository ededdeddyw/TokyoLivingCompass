import Link from "next/link";
import { Building2 } from "lucide-react";

import type { Dictionary } from "@/lib/dictionaries";

/**
 * まわりに住宅がほとんどない駅（空港・倉庫街・官庁街など）の案内。
 * 駅ページは残すが、住む場所を探している読み手には、近くの住宅のある駅を示す。
 */
export function NonResidentialNotice({
  note,
  nearby,
  locale,
  dict,
}: {
  note: string;
  nearby: { slug: string; name: string }[];
  locale: string;
  dict: Dictionary;
}) {
  return (
    <section className="rounded-2xl border border-sun/40 bg-sun-soft p-5">
      <h2 className="flex items-center gap-2 text-base font-bold text-ink">
        <Building2 aria-hidden="true" className="size-5 text-ink-soft" />
        {dict.station.nonResidentialTitle}
      </h2>
      <p className="mt-2 text-[15px] leading-relaxed text-ink">{note}</p>
      {nearby.length > 0 && (
        <p className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-ink-soft">{dict.station.nonResidentialNearby}:</span>
          {nearby.map((n) => (
            <Link
              key={n.slug}
              href={`/${locale}/stations/${n.slug}`}
              className="inline-flex items-center rounded-full bg-accent-soft px-3 py-0.5 font-bold text-accent-strong hover:bg-accent hover:text-white"
            >
              {n.name}
            </Link>
          ))}
        </p>
      )}
    </section>
  );
}
