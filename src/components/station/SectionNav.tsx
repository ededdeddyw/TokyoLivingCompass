/**
 * 節への目次。長いページの中で、家賃・通勤・評価などへすぐ飛べるようにする。
 * 画面の上に固定し、スマホでは横にスクロールするチップの列にする。
 */
export function SectionNav({
  items,
  label,
}: {
  items: { id: string; label: string }[];
  label: string;
}) {
  return (
    <nav
      aria-label={label}
      className="sticky top-0 z-20 -mx-5 border-b border-line bg-canvas/90 px-5 py-2.5 backdrop-blur"
    >
      <ul className="flex gap-2 overflow-x-auto [scrollbar-width:none]">
        {items.map((it) => (
          <li key={it.id} className="shrink-0">
            <a
              href={`#${it.id}`}
              className="block rounded-full border border-line bg-surface px-3.5 py-1.5 text-sm text-ink hover:border-accent hover:text-accent"
            >
              {it.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
