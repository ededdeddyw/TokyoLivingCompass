import type { Dictionary } from "@/lib/dictionaries";
import { RENT_TYPES, type RentHistory } from "@/lib/schema";

/**
 * 家賃の推移。
 *
 * 相場を1時点で示すと、上がっているのか下がっているのかが読み手に分からない。
 * 「いま高い」と「これから高くなる」は、住む場所を決める判断としてまったく違う。
 * 出典なしでは表示しない（rentHistorySchema が source を必須にしている）。
 */
export function RentHistoryTable({
  history,
  dict,
}: {
  history: RentHistory;
  dict: Dictionary;
}) {
  const points = [...history.points].sort(
    (a, b) => a.year - b.year || (a.quarter ?? 0) - (b.quarter ?? 0),
  );
  // 値が1つも入っていない間取りの列は出さない。
  const types = RENT_TYPES.filter((t) =>
    points.some((p) => p.rent[t] !== undefined),
  );
  if (types.length === 0) return null;

  const label = (p: (typeof points)[number]) =>
    p.quarter ? `${p.year}年 第${p.quarter}四半期` : `${p.year}年`;
  const man = (yen: number | undefined) =>
    yen === undefined ? "—" : `${(yen / 10000).toFixed(1)}万円`;

  const first = points[0];
  const last = points[points.length - 1];

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-line text-left">
              <th className="py-1.5 pr-4 font-medium">{dict.rentHistory.period}</th>
              {types.map((t) => (
                <th key={t} className="py-1.5 pr-4 text-right font-medium">
                  {dict.rentTypes[t]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {points.map((p) => (
              <tr key={`${p.year}-${p.quarter ?? 0}`} className="border-b border-line/50">
                <td className="py-1.5 pr-4">{label(p)}</td>
                {types.map((t) => (
                  <td key={t} className="py-1.5 pr-4 text-right tabular-nums">
                    {man(p.rent[t])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-ink-soft">
        {dict.rentHistory.range
          .replace("{from}", label(first))
          .replace("{to}", label(last))}
        {" / "}
        {history.source.name}
        {history.source.retrievedAt && `（${history.source.retrievedAt} 取得）`}
      </p>
    </div>
  );
}
