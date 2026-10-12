import { ArrowRightLeft, CircleCheck } from "lucide-react";

import type { Dictionary } from "@/lib/dictionaries";
import type { Commute } from "@/lib/schema";

/**
 * 主なオフィス街への所要時間を、短い順に横棒で並べる。
 * 棒の長さは、いちばん遠いオフィス街を基準にした相対の長さである。
 * 乗り換えの有無はアイコンと文字で示す。
 */
export function CommuteBars({ commutes, dict }: { commutes: Commute[]; dict: Dictionary }) {
  const sorted = [...commutes].sort((a, b) => a.minutes - b.minutes);
  const max = Math.max(...sorted.map((c) => c.minutes), 1);
  return (
    <ul className="space-y-2.5">
      {sorted.map((c) => (
        <li key={c.to} className="grid grid-cols-[4.5rem_1fr_auto] items-center gap-3">
          <span className="text-sm font-medium text-ink">{dict.offices[c.to]}</span>
          <span className="h-3 overflow-hidden rounded-full bg-accent-soft">
            <span
              className="block h-full rounded-full bg-gradient-to-r from-accent to-accent-bright"
              style={{ width: `${Math.max(8, (c.minutes / max) * 100)}%` }}
            />
          </span>
          <span className="flex items-center gap-2 text-sm tabular-nums">
            <span className="w-12 text-right font-semibold text-ink">
              {c.minutes}
              <span className="text-xs font-normal text-ink-soft"> {dict.station.minutes}</span>
            </span>
            {c.transfers === 0 ? (
              <span className="flex w-16 items-center gap-1 text-xs text-good">
                <CircleCheck aria-hidden="true" className="size-3.5" />
                {dict.station.noTransfer}
              </span>
            ) : (
              <span className="flex w-16 items-center gap-1 text-xs text-ink-soft">
                <ArrowRightLeft aria-hidden="true" className="size-3.5" />
                {dict.station.transfers} {c.transfers}
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}
