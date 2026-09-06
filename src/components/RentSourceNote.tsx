import type { Dictionary } from "@/lib/dictionaries";
import type { RentSource } from "@/lib/schema";

/**
 * 家賃の出典表示（docs/08-data-sources-rent.md §3）。
 * 「何の家賃か」を示さないと数字が誤解される。
 */
export function RentSourceNote({
  source,
  dict,
}: {
  source: RentSource | undefined;
  dict: Dictionary;
}) {
  if (!source) {
    return <p className="text-sm text-ink-soft">{dict.rentSource.missing}</p>;
  }

  const parts = [
    dict.rentSource.basis[source.basis],
    dict.rentSource.statistic[source.statistic],
  ];

  return (
    <p className="text-sm leading-relaxed text-ink-soft">
      {parts.join(" · ")}
      {" — "}
      {source.url ? (
        <a
          href={source.url}
          className="text-accent hover:underline"
          rel="noreferrer"
          target="_blank"
        >
          {source.name}
        </a>
      ) : (
        source.name
      )}
      {` (${source.retrievedAt})`}
      {source.sampleSize !== undefined && ` · n=${source.sampleSize}`}
      {source.method && (
        <span className="block">{dict.rentSource.method[source.method]}</span>
      )}
      {source.basis === "asking" && (
        <span className="block">{dict.rentSource.askingCaveat}</span>
      )}
    </p>
  );
}
