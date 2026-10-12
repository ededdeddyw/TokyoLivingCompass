import { MapPinned } from "lucide-react";

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
    <section
      id="traits"
      className="rounded-2xl border border-line bg-surface p-5 shadow-sm sm:p-6"
    >
      <h2 className="flex items-center gap-2 text-xl font-bold text-ink">
        <span className="grid size-9 place-items-center rounded-full bg-sun-soft text-sun-ink">
          <MapPinned aria-hidden="true" className="size-5" />
        </span>
        {dict.station.townTraits}
      </h2>
      <ul className="mt-4 space-y-3">
        {data.traits.map((t) => (
          <li key={t} className="flex gap-3 text-[15px] leading-relaxed text-ink">
            <span aria-hidden="true" className="mt-2.5 size-1.5 shrink-0 rounded-full bg-sun" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t border-line pt-3 text-xs leading-relaxed text-ink-soft">
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
