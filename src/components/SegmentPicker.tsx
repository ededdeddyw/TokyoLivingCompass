import Link from "next/link";

import type { Dictionary } from "@/lib/dictionaries";
import {
  BALANCED,
  SEGMENT_AXES,
  splitSegment,
  withOption,
  type WeightPreset,
} from "@/lib/weights";

/**
 * 読み手の区分を選ぶ（docs/14-audience-segments.md）。
 *
 * 8区分をそのまま並べると「子どもなし・夜は街で・家賃を抑える」のような
 * 長い名前のボタンが9個並び、画面の幅に収まらない。
 * 3つの軸をそれぞれ2択で出し、押すとその軸だけが入れ替わる形にする。
 */
export function SegmentPicker({
  preset,
  dict,
  href,
  title,
}: {
  preset: WeightPreset;
  dict: Dictionary;
  /** 区分のキーから、そのリンク先を作る */
  href: (key: WeightPreset) => string;
  title: string;
}) {
  const current = splitSegment(preset);
  const chip = (on: boolean) =>
    on
      ? "rounded-full bg-accent px-3.5 py-1.5 text-sm font-medium text-white"
      : "rounded-full border border-line bg-surface px-3.5 py-1.5 text-sm text-ink-soft hover:border-accent hover:text-accent";

  return (
    <nav className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="text-sm font-medium text-ink">{title}</p>
        <Link href={href(BALANCED)} className={chip(current === null)}>
          {dict.balancedLabel}
        </Link>
      </div>
      <div className="space-y-2">
        {SEGMENT_AXES.map((axis) => (
          <div key={axis.key} className="flex flex-wrap items-center gap-2">
            <span className="w-28 shrink-0 text-xs text-ink-soft">
              {dict.segmentAxes[axis.key]}
            </span>
            {axis.options.map((option) => (
              <Link
                key={option}
                href={href(withOption(preset, axis.key, option))}
                className={chip(current?.[axis.key] === option)}
              >
                {dict.segmentOptions[option]}
              </Link>
            ))}
          </div>
        ))}
      </div>
    </nav>
  );
}
