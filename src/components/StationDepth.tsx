import type { Dictionary } from "@/lib/dictionaries";
import type { StationContent } from "@/lib/schema";

/**
 * 「住むと分かること」の表示（docs/12-quality-standard.md）。
 * 既存の不動産まとめ記事が書いていない項目を、ここでまとめて出す。
 * 未記入の項目は表示しない。空欄を並べても価値がないため。
 */

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
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
      <Block key="faces" title={d.faces}>
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
      <Block key="terrain" title={d.terrain}>
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
      <Block key="groceries" title={d.groceries}>
        <ul className="space-y-1.5">
          {content.groceries.map((store) => (
            <li key={store.name} className="flex flex-wrap items-baseline gap-x-2">
              <span className="font-medium text-ink">{store.name}</span>
              <span className="rounded bg-canvas px-1.5 py-0.5 text-xs">
                {d.tier[store.tier]}
              </span>
              <span className="text-xs tabular-nums">
                {d.walkMinutes} {store.walkMinutes}分
              </span>
              {store.note && <span className="w-full">{store.note}</span>}
            </li>
          ))}
        </ul>
      </Block>,
    );
  }

  if (content.exits && content.exits.length > 0) {
    blocks.push(
      <Block key="exits" title={d.exits}>
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
              <dd>{exit.character}</dd>
            </div>
          ))}
        </dl>
      </Block>,
    );
  }

  if (content.rentRange) {
    blocks.push(
      <Block key="rentRange" title={d.rentRange}>
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
      <Block key="noise" title={d.noiseSources}>
        <ul className="list-disc space-y-1 pl-5">
          {content.noiseSources.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </Block>,
    );
  }

  const simple: [string, string | undefined][] = [
    [d.family, content.family],
    [d.medical, content.medical],
    [d.stationNote, content.stationNote],
    [d.nightWalk, content.nightWalk],
    [d.residents, content.residents],
    [d.housingStock, content.housingStock],
    [d.rentReason, content.rentReason],
    [d.outlook, content.outlook],
  ];
  for (const [title, text] of simple) {
    if (text) {
      blocks.push(
        <Block key={title} title={title}>
          <p>{text}</p>
        </Block>,
      );
    }
  }

  // 災害は、書き方ひとつで読み手の受け取り方が大きく変わる。
  // 浸水想定区域が何を意味するのかを毎回そえて、駅ごとの本文が単独で
  // 強く読まれないようにする。
  if (content.hazards) {
    blocks.push(
      <Block key="hazards" title={d.hazards}>
        <p>{content.hazards}</p>
        <p className="mt-2 text-xs leading-relaxed text-ink-soft">
          {dict.hazardNote}
        </p>
      </Block>,
    );
  }

  if (content.neighbours && content.neighbours.length > 0) {
    blocks.push(
      <Block key="neighbours" title={d.neighbours}>
        <ul className="space-y-1.5">
          {content.neighbours.map((n) => (
            <li key={n.slug}>
              <span className="font-medium text-ink">
                {neighbourNames[n.slug] ?? n.slug}
              </span>
              {" — "}
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
