import type { Dictionary } from "@/lib/dictionaries";
import type { TownTraits as TownTraitsData } from "@/lib/schema";

/**
 * 街の特色。出典の記事から読み取ってまとめ直したもの（docs/16-town-traits.md）。
 * 要約のすぐ下に置き、数字では伝わらない「どんな街か」を先に渡す。
 * 出典は記事ごとにリンクし、ライセンスの表示が要るものはその名前を添える。
 */
export function TownTraits({
  data,
  dict,
}: {
  data: TownTraitsData;
  dict: Dictionary;
}) {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold text-ink">{dict.station.townTraits}</h2>
      <ul className="list-disc space-y-1.5 pl-5 leading-relaxed text-ink">
        {data.traits.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
      <p className="text-xs leading-relaxed text-ink-soft">
        {dict.station.townTraitsSource}:{" "}
        {data.sources.map((src, i) => (
          <span key={src.label}>
            {i > 0 && " / "}
            {src.label}
            {src.articles.map((a) => (
              <span key={a.url}>
                「
                <a
                  href={a.url}
                  className="text-accent hover:underline"
                  rel="noreferrer"
                  target="_blank"
                >
                  {a.title}
                </a>
                」
              </span>
            ))}
            {src.licenseName &&
              (src.license ? (
                <>
                  （
                  <a
                    href={src.license}
                    className="text-accent hover:underline"
                    rel="noreferrer"
                    target="_blank"
                  >
                    {src.licenseName}
                  </a>
                  ）
                </>
              ) : (
                `（${src.licenseName}）`
              ))}
          </span>
        ))}
        。{dict.station.townTraitsNote}
      </p>
    </section>
  );
}
