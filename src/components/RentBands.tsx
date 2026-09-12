import type { Dictionary } from "@/lib/dictionaries";
import { RENT_TYPES, type RentBands as RentBandsData } from "@/lib/schema";

/**
 * 複数サイトの掲載相場を平均した、1万円刻みの帯。
 *
 * 相場を1点の数字で示すと、出典ごとに数万円ちがう値を1つに見せてしまう。
 * 帯で示し、どのサイトをいつ見た値なのかを必ず添える。
 * 出典間の開きが大きい間取りは、帯だけを信じないよう注記する。
 */
export function RentBands({
  data,
  dict,
}: {
  data: RentBandsData;
  dict: Dictionary;
}) {
  const shown = RENT_TYPES.filter((t) => data.bands[t] !== undefined);
  if (shown.length === 0) return null;

  const man = (yen: number) => (yen / 10000).toFixed(0);
  const anyWide = shown.some((t) => data.bands[t]?.wideSpread);

  return (
    <div>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {shown.map((type) => {
          const b = data.bands[type]!;
          return (
            <div key={type} className="rounded-md border border-line bg-surface p-4">
              <dt className="text-sm text-ink-soft">{dict.rentTypes[type]}</dt>
              <dd className="mt-1 tabular-nums text-ink">
                {dict.rentBands.band
                  .replace("{low}", man(b.low))
                  .replace("{high}", man(b.high))}
                {b.wideSpread && (
                  <span className="ml-1 align-middle text-xs text-ink-soft">*</span>
                )}
              </dd>
            </div>
          );
        })}
      </dl>

      <p className="mt-2 text-xs leading-relaxed text-ink-soft">
        {dict.rentBands.attribution
          .replace("{sources}", data.sources.map((s) => s.name).join("、"))
          .replace("{date}", data.retrievedAt)}
      </p>
      {anyWide && (
        <p className="mt-1 text-xs leading-relaxed text-ink-soft">
          {dict.rentBands.wideSpreadNote}
        </p>
      )}
      {!data.verified && (
        <p className="mt-1 text-xs leading-relaxed text-accent">
          {dict.rentBands.provisional}
        </p>
      )}
    </div>
  );
}
