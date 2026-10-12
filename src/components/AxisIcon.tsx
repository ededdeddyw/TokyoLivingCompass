import {
  Baby,
  Coffee,
  Dumbbell,
  Globe,
  HeartPulse,
  Moon,
  PiggyBank,
  Route,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Trees,
  TrainFront,
  User,
  UtensilsCrossed,
  Volume1,
  Wallet,
  Waves,
  type LucideIcon,
} from "lucide-react";

import type { ScoreAxis } from "@/lib/schema";

/** 評価軸ごとのアイコン。文字を読む前に、どの軸の話かを見分けられるようにする。 */
const ICONS: Record<ScoreAxis, LucideIcon> = {
  rentValue: PiggyBank,
  rentLow: Wallet,
  commute: TrainFront,
  transitConvenience: Route,
  shopping: ShoppingCart,
  food: UtensilsCrossed,
  cafe: Coffee,
  nightlife: Moon,
  safety: ShieldCheck,
  quietness: Volume1,
  family: Baby,
  singleLife: User,
  internationalFriendliness: Globe,
  style: Sparkles,
  nature: Trees,
  healthcare: HeartPulse,
  fitness: Dumbbell,
  disaster: Waves,
};

export function AxisIcon({ axis, className }: { axis: ScoreAxis; className?: string }) {
  const Icon = ICONS[axis];
  return <Icon aria-hidden="true" className={className} strokeWidth={2} />;
}
