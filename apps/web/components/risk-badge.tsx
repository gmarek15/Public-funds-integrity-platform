import { RiskIndicator } from "@/lib/types";

export function RiskBadge({ indicator }: { indicator: RiskIndicator }) {
  const className = indicator.severity === "medium" ? "chip chip-medium" : "chip chip-low";
  return <span className={className}>{indicator.title}</span>;
}
