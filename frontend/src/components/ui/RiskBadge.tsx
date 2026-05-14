import { Badge } from "./Badge";
import { normalizeRisk, riskCopy, riskStyles } from "../../utils/risk";

export function RiskBadge({ level }: { level: unknown }) {
  const risk = normalizeRisk(level);
  return <Badge className={riskStyles[risk]}>{riskCopy[risk]}</Badge>;
}
