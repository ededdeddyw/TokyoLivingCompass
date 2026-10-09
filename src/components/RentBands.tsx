import type { Dictionary } from "@/lib/dictionaries";
import { formatYen } from "@/lib/format";
import type { ActiveLocale } from "@/lib/i18n";
import { RENT_TYPES, type RentBands as RentBandsData } from "@/lib/schema";

/**
 * 複数サイトの掲載相場を平均した、1万円刻みの帯。
 *
 * 相場を1点の数字で示すと、出典ごとに数万円ちがう値を1つに見せてしまう。
 * 帯で示し、どのサイトをいつ見た値なのかを必ず添える。
 * 出典間の開きが大きい間取りは、帯だけを信じないよう注記する。
 *
 * 帯のもとになった平均値も、同じカードに小さく添える。以前は「家賃相場」と
 * 「家賃の目安」の2つの節に同じ出典の数字を別々に出しており、読み手が
 * どちらを見ればよいか迷った。平均は帯の中身として、1つの節にまとめる。
 */
export function RentBands({
  data,
  dict,
  locale,
}: {
  data: RentBandsData;
  dict: Dictionary;
  locale: ActiveLocale;
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
            <div key={type} className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
              <dt className="inline-block rounded-md bg-accent-soft px-2 py-0.5 text-xs font-semibold text-accent-strong">
                {dict.rentTypes[type]}
              </dt>
              <dd className="mt-2 text-lg font-bold tabular-nums text-ink sm:text-xl">
                {dict.rentBands.band
                  .replace("{low}", man(b.low))
                  .replace("{high}", man(b.high))}
                {b.wideSpread && (
                  <span className="ml-1 align-middle text-xs font-normal text-ink-soft">*</span>
                )}
              </dd>
              <dd className="mt-0.5 text-xs tabular-nums text-ink-soft">
                {dict.stationUi.meanRent.replace("{yen}", formatYen(b.mean, locale))}
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
