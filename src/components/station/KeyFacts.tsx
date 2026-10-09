import { Clock, Route, Wallet, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/**
 * 冒頭の要点。家賃・都心への近さ・路線の数のように、誰にとっても向きが同じ数字を
 * 先に見せる（CLAUDE.md ルール40）。数字の出典と前提は、それぞれの節に書いてある。
 */
export type KeyFact = {
  icon: "rent" | "commute" | "lines";
  label: string;
  value: string;
  href: string;
};

const ICONS: Record<KeyFact["icon"], LucideIcon> = {
  rent: Wallet,
  commute: Clock,
  lines: Route,
};

export function KeyFacts({ facts, extra }: { facts: KeyFact[]; extra?: ReactNode }) {
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {facts.map((f) => {
        const Icon = ICONS[f.icon];
        return (
          <a
            key={f.label}
            href={f.href}
            className="group rounded-2xl border border-line bg-surface p-4 shadow-sm transition hover:border-accent-bright"
          >
            <dt className="flex items-center gap-1.5 text-xs text-ink-soft">
              <Icon aria-hidden="true" className="size-4 text-accent" />
              {f.label}
            </dt>
            <dd className="mt-1.5 text-xl font-bold tabular-nums text-ink sm:text-2xl">
              {f.value}
            </dd>
          </a>
        );
      })}
      {extra}
    </dl>
  );
}
