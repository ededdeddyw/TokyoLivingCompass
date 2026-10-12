import type { Dictionary } from "@/lib/dictionaries";
import { formatYen } from "@/lib/format";
import type { ActiveLocale } from "@/lib/i18n";
import { RENT_TYPES, type RentBands as RentBandsData, type RentType } from "@/lib/schema";

/** 間取りごとの平均と、平均に使った駅の数。src/lib/stations.ts の RentAverage と同じ形。 */
type Average = Partial<Record<RentType, { mean: number; count: number }>>;

/** 区の平均を出すのに、最低限ほしい駅の数。1〜2駅の平均では区の比較にならない。 */
const MIN_WARD_STATIONS = 3;
/** これより差が小さければ「ほぼ同じ」とする。 */
const SAME_YEN = 2000;

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
  averages,
  wardLabel,
}: {
  data: RentBandsData;
  dict: Dictionary;
  locale: ActiveLocale;
  /** 同じ区の駅と、23区すべての駅の平均。渡されれば、高いか安いかを添える。 */
  averages?: { ward: Average; all: Average };
  wardLabel?: string;
}) {
  const shown = RENT_TYPES.filter((t) => data.bands[t] !== undefined);
  if (shown.length === 0) return null;

  const man = (yen: number) => (yen / 10000).toFixed(0);
  const anyWide = shown.some((t) => data.bands[t]?.wideSpread);
  const ui = dict.stationUi;

  // 差の金額。日本語は「1.2万円」、ほかの言語は千円単位に丸めた実額で出す。
  const diffText = (yen: number) =>
    locale === "ja"
      ? `${(Math.abs(yen) / 10000).toFixed(1)}万円`
      : formatYen(Math.round(Math.abs(yen) / 1000) * 1000, locale);
  const compare = (own: number, avg: number, cont: boolean) => {
    const d = own - avg;
    const tpl =
      Math.abs(d) < SAME_YEN
        ? cont ? ui.cmpSameCont : ui.cmpSame
        : d > 0
          ? cont ? ui.cmpHigherCont : ui.cmpHigher
          : cont ? ui.cmpLowerCont : ui.cmpLower;
    return tpl.replace("{diff}", diffText(d));
  };
  const wardOk = (t: RentType) =>
    wardLabel !== undefined && (averages?.ward[t]?.count ?? 0) >= MIN_WARD_STATIONS;
  // 見出しの一文は、いちばん読まれる1Kで比べる。1Kが無ければワンルーム。
  const headType = (["oneK", "oneRoom"] as const).find(
    (t) => data.bands[t] && averages?.all[t],
  );
  const headline = (() => {
    if (!averages || !headType) return null;
    const own = data.bands[headType]!.mean;
    const cmpA = compare(own, averages.all[headType]!.mean, false);
    const tpl = wardOk(headType) ? ui.rentHead : ui.rentHeadAllOnly;
    return tpl
      .replace("{type}", dict.rentTypes[headType])
      .replace("{ward}", wardLabel ?? "")
      .replace("{cmpW}", wardOk(headType) ? compare(own, averages.ward[headType]!.mean, true) : "")
      .replace("{cmpA}", cmpA);
  })();
  const diffClass = (own: number, avg: number) =>
    Math.abs(own - avg) < SAME_YEN
      ? "bg-fair-soft text-ink-soft"
      : own > avg
        ? "bg-bad-soft text-bad"
        : "bg-good-soft text-good";

  return (
    <div>
      {headline && (
        <p className="mb-3 rounded-xl bg-sun-soft px-4 py-3 text-[15px] leading-relaxed text-ink">
          {headline}
        </p>
      )}
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
              {averages && (
                <dd className="mt-3 space-y-1.5 border-t border-line pt-2.5 text-xs">
                  {(
                    [
                      wardOk(type) ? [ui.rentCompareWard.replace("{ward}", wardLabel ?? ""), averages.ward[type]!.mean] : null,
                      averages.all[type] ? [ui.rentCompareAll, averages.all[type]!.mean] : null,
                    ].filter(Boolean) as [string, number][]
                  ).map(([label, avg]) => (
                    <div key={label}>
                      <div className="text-ink-soft">{label}</div>
                      <div className="flex flex-wrap items-center gap-x-1.5 tabular-nums">
                        <span className="text-ink">{formatYen(avg, locale)}</span>
                        <span className={`rounded px-1.5 py-px font-semibold ${diffClass(b.mean, avg)}`}>
                          {compare(b.mean, avg, false)}
                        </span>
                      </div>
                    </div>
                  ))}
                </dd>
              )}
            </div>
          );
        })}
      </dl>

      {averages && headType && (
        <p className="mt-2 text-xs leading-relaxed text-ink-soft">
          {ui.rentCompareNote
            .replace("{ward}", wardLabel ?? "")
            .replace("{wardCount}", String(averages.ward[headType]?.count ?? 0))
            .replace("{allCount}", String(averages.all[headType]?.count ?? 0))}
        </p>
      )}
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
