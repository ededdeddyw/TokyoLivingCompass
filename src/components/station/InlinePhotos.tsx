import type { StationPhoto } from "@/lib/schema";

export type PhotoCredits = {
  /** 「写真: {author}（{license}、Wikimedia Commons）」 */
  commons: string;
  /** 「写真: {author}（{license}、Flickr）」 */
  flickr: string;
  /** ぱくたそなど。「写真: {author}」 */
  other: string;
};

/** 写真の出典に合わせたクレジットの文言 */
export function photoCredit(p: StationPhoto, credits: PhotoCredits): string {
  const tpl =
    p.source === "flickr"
      ? credits.flickr
      : p.source === "local" || p.src.startsWith("/")
        ? credits.other
        : credits.commons;
  return tpl.replace("{author}", p.author).replace("{license}", p.license);
}

/**
 * 記事の途中に差し込む写真（1〜2枚）。写真の下に一言と、作者・ライセンスを添える。
 * 一言は写真から読み取れることだけを書いたもので、本文の主張を補う材料にはしない。
 */
export function InlinePhotos({
  photos,
  credits,
}: {
  photos: StationPhoto[];
  credits: PhotoCredits;
}) {
  if (photos.length === 0) return null;
  const two = photos.length > 1;
  return (
    <div className={two ? "grid gap-4 sm:grid-cols-2" : "max-w-2xl"}>
      {photos.map((p) => (
        <figure key={p.file}>
          {/* eslint-disable-next-line @next/next/no-img-element -- 外部の画像を、最適化サーバーを通さずにそのまま出す */}
          <img
            src={p.src}
            alt={p.caption ?? ""}
            loading="lazy"
            className="aspect-[3/2] w-full rounded-2xl object-cover shadow-sm ring-1 ring-line"
          />
          <figcaption className="mt-2 px-1">
            {p.caption && <p className="text-[15px] leading-relaxed text-ink">{p.caption}</p>}
            <a
              href={p.page}
              className="mt-0.5 block text-[11px] leading-snug text-ink-soft hover:underline"
              rel="noreferrer"
              target="_blank"
            >
              {photoCredit(p, credits)}
            </a>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}
