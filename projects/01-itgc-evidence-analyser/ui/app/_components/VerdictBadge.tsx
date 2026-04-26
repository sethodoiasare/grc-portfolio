import { CheckCircle, XCircle, AlertTriangle, ShieldAlert } from "lucide-react";

const config = {
  PASS: { icon: CheckCircle, label: "Pass", className: "bg-[var(--pass)]/10 text-[var(--pass)] ring-[var(--pass)]/20" },
  PARTIAL: { icon: AlertTriangle, label: "Partial", className: "bg-[var(--partial)]/10 text-[var(--partial)] ring-[var(--partial)]/20" },
  FAIL: { icon: XCircle, label: "Fail", className: "bg-[var(--fail)]/10 text-[var(--fail)] ring-[var(--fail)]/20" },
  INSUFFICIENT_EVIDENCE: { icon: ShieldAlert, label: "Insufficient", className: "bg-[var(--insufficient)]/10 text-[var(--insufficient)] ring-[var(--insufficient)]/20" },
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const c = config[verdict as keyof typeof config] ?? config.INSUFFICIENT_EVIDENCE;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold ring-1 ${c.className}`}>
      <Icon className="w-3.5 h-3.5" />
      {c.label}
    </span>
  );
}
