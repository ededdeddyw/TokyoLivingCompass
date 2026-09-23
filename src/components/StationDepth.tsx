import type { Dictionary } from "@/lib/dictionaries";
import type { StationContent } from "@/lib/schema";

/**
 * 「住むと分かること」の表示（docs/12-quality-standard.md）。
 * 既存の不動産まとめ記事が書いていない項目を、ここでまとめて出す。
 * 未記入の項目は表示しない。空欄を並べても価値がないため。
 */

/**
 * 節ひとつ。lead は「一言でいうと」で、本文を読む前に結論だけを受け取れるようにする
 * （docs/12-quality-standard.md）。入っていない節では出さない。
 */
function Block({
  title,
  lead,
  children,
}: {
  title: string;
  lead?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-1.5">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {lead && <p className="text-sm font-medium leading-relaxed text-ink">{lead}</p>}
      <div className="text-sm leading-relaxed text-ink-soft">{children}</div>
    </section>
  );
}

export function StationDepth({
  content,
  dict,
  neighbourNames,
}: {
  content: StationContent;
  dict: Dictionary;
  /** 隣接駅 slug → 表示名。解決できない駅は slug のまま出す。 */
  neighbourNames: Record<string, string>;
}) {
  const d = dict.depth;

  const blocks: React.ReactNode[] = [];

  if (content.faces) {
    blocks.push(
      <Block key="faces" title={d.faces} lead={content.leads?.faces}>
        <dl className="space-y-2">
          {(
            [
              [d.morning, content.faces.morning],
              [d.daytime, content.faces.daytime],
              [d.night, content.faces.night],
              [d.weekend, content.faces.weekend],
            ] as const
          ).map(([label, text]) => (
            <div key={label} className="flex gap-3">
              <dt className="w-10 shrink-0 font-medium text-ink">{label}</dt>
              <dd>{text}</dd>
            </div>
          ))}
        </dl>
      </Block>,
    );
  }

  if (content.terrain) {
    blocks.push(
      <Block key="terrain" title={d.terrain} lead={content.leads?.terrain}>
        <p>
          <span className="font-medium text-ink">{d.slope[content.terrain.slope]}</span>
          {" — "}
          {content.terrain.note}
        </p>
      </Block>,
    );
  }

  if (content.groceries && content.groceries.length > 0) {
    blocks.push(
      <Block key="groceries" title={d.groceries} lead={content.leads?.groceries}>
        <ul className="space-y-1.5">
          {content.groceries.map((store) => (
            <li key={store.name} className="flex flex-wrap items-baseline gap-x-2">
              <span className="font-medium text-ink">{store.name}</span>
              <span className="rounded bg-canvas px-1.5 py-0.5 text-xs">
                {d.tier[store.tier]}
              </span>
              {store.walkMinutes !== undefined && (
                <span className="text-xs tabular-nums">
                  {d.walkMinutes} {store.walkMinutes}分
                </span>
              )}
              {store.note && <span className="w-full">{store.note}</span>}
            </li>
          ))}
        </ul>
      </Block>,
    );
  }

  if (content.exits && content.exits.length > 0) {
    blocks.push(
      <Block key="exits" title={d.exits} lead={content.leads?.exits}>
        <dl className="space-y-2">
          {content.exits.map((exit) => (
            <div key={exit.name} className="flex gap-3">
              <dt className="w-28 shrink-0 font-medium text-ink">
                {exit.line && (
                  <span className="block text-xs font-normal text-ink-soft">
                    {exit.line}
                  </span>
                )}
                {exit.name}
              </dt>
              <dd>
                {exit.tags && exit.tags.length > 0 && (
                  <span className="mb-1 flex flex-wrap gap-1">
                    {exit.tags.map((t) => (
                      <span
                        key={t}
                        className="rounded bg-[#f3f4f6] px-1.5 py-0.5 text-xs text-[#5b6472]"
                      >
                        {dict.exitTags[t]}
                      </span>
                    ))}
                  </span>
                )}
                {exit.character}
              </dd>
            </div>
          ))}
        </dl>
      </Block>,
    );
  }

  if (content.rentRange) {
    blocks.push(
      <Block key="rentRange" title={d.rentRange} lead={content.leads?.rentRange}>
        <p>{content.rentRange.note}</p>
        <p className="mt-1.5">
          <span className="font-medium text-ink">{d.rentDrivers}: </span>
          {content.rentRange.drivers.join(" / ")}
        </p>
      </Block>,
    );
  }

  if (content.noiseSources && content.noiseSources.length > 0) {
    blocks.push(
      <Block key="noise" title={d.noiseSources} lead={content.leads?.noiseSources}>
        <ul className="list-disc space-y-1 pl-5">
          {content.noiseSources.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </Block>,
    );
  }

  const simple = [
    "family",
    "medical",
    "stationNote",
    "nightWalk",
    "residents",
    "housingStock",
    "rentReason",
    "outlook",
  ] as const;
  for (const field of simple) {
    const text = content[field];
    if (!text) continue;
    blocks.push(
      <Block key={field} title={d[field]} lead={content.leads?.[field]}>
        <p>{text}</p>
      </Block>,
    );
  }

  // 災害は、書き方ひとつで読み手の受け取り方が大きく変わる。
  // 浸水想定区域が何を意味するのかを毎回そえて、駅ごとの本文が単独で
  // 強く読まれないようにする。
  if (content.hazards) {
    blocks.push(
      <Block key="hazards" title={d.hazards} lead={content.leads?.hazards}>
        <p>{content.hazards}</p>
        <p className="mt-2 text-xs leading-relaxed text-ink-soft">
          {dict.hazardNote}
        </p>
      </Block>,
    );
  }

  // 近くの駅（距離から選ぶ）と、迷いやすい駅（条件が似ていて人が選ぶ）は、
  // 読み手にとって意味が違うため、同じ節にまとめない。
  for (const field of ["neighbours", "alternatives"] as const) {
    const list = content[field];
    if (!list || list.length === 0) continue;
    blocks.push(
      <Block key={field} title={d[field]}>
        <ul className="space-y-1.5">
          {list.map((n) => (
            <li key={n.slug}>
              <span className="font-medium text-ink">
                {neighbourNames[n.slug] ?? n.slug}
              </span>
              {/* 比較の一言。本文を読む前に、どちらが何で上回るのかを渡す。 */}
              {n.lead && (
                <span className="block font-medium text-ink">{n.lead}</span>
              )}
              {n.lead ? "" : " — "}
              {n.note}
            </li>
          ))}
        </ul>
      </Block>,
    );
  }

  if (blocks.length === 0) return null;

  return (
    <section className="space-y-6">
      <h2 className="text-lg font-semibold text-ink">{d.heading}</h2>
      <div className="grid gap-6 sm:grid-cols-2">{blocks}</div>
    </section>
  );
}
