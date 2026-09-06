import type { Dictionary } from "@/lib/dictionaries";

/**
 * 推定値であることの明示。
 * dataQuality が "seed" のあいだは必ず出す（docs/01-requirements.md §6）。
 */
export function SeedNotice({ dict }: { dict: Dictionary }) {
  return (
    <p className="rounded-md border border-[#e5d5a8] bg-[#fdf8ea] px-4 py-3 text-sm text-[#6b5620]">
      {dict.dataQuality.seedWarning}
    </p>
  );
}
