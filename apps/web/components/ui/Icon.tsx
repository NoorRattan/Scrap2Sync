import {
  ArrowRight,
  Check,
  Copy,
  Plus,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
const icons = {
  arrow: ArrowRight,
  copy: Copy,
  check: Check,
  plus: Plus,
  close: X,
  shield: ShieldCheck,
  warning: TriangleAlert,
  spark: Sparkles,
};
export function Icon({ name }: { name: keyof typeof icons }) {
  const Component = icons[name];
  return (
    <Component
      size={18}
      strokeWidth={1.6}
      aria-hidden="true"
      focusable="false"
    />
  );
}
