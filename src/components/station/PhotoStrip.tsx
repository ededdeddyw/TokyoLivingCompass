import { Camera } from "lucide-react";

import type { StationPhoto } from "@/lib/schema";

/**
 * 駅と街の写真を横に並べる。1枚目は駅名の帯に出すので、ここには2枚目以降を渡す。
 *
 * 地下鉄の駅は、基本情報欄の写真が出口だけのことが多く、街の様子が伝わらなかった。
 * 駅前・街並み・周辺の施設の写真を並べ、どんな街かを目で確かめられるようにする。
 * どの写真にも、何が写っているかと、作者・ライセンスを添える（Commons の利用条件）。
 */
export function PhotoStrip({
  photos,
  title,
  credit,
  creditOther,
}: {
  /** Commons 以外（ぱくたそなど）の写真の表示。「写真: {author}」 */
  creditOther: string;
  photos: StationPhoto[];
  title: string;
  /** 「写真: {author}（{license}、Wikimedia Commons）」 */
  credit: string;
}) {
  if (photos.length === 0) return null;
  return (
    <section>
      <h2 className="flex items-center gap-2 text-xl font-bold text-ink">
        <Camera aria-hidden="true" className="size-5 text-accent" />
        {title}
      </h2>
      <ul className="-mx-4 mt-3 flex snap-x gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0">
        {photos.map((p) => (
          <li
            key={p.file}
            className="w-64 shrink-0 snap-start overflow-hidden rounded-2xl border border-line bg-surface shadow-sm sm:w-72"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- 外部の画像を、最適化サーバーを通さずにそのまま出す */}
            <img
              src={p.src.replace("width=1200", "width=640")}
              alt={p.caption ?? ""}
              loading="lazy"
              className="aspect-[4/3] w-full object-cover"
            />
            <div className="p-3">
              {p.caption && <p className="text-sm font-semibold text-ink">{p.caption}</p>}
              <a
                href={p.page}
                className="mt-1 block text-[11px] leading-snug text-ink-soft hover:underline"
                rel="noreferrer"
                target="_blank"
              >
                {(p.src.startsWith("/") ? creditOther : credit)
                  .replace("{author}", p.author)
                  .replace("{license}", p.license)}
              </a>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
