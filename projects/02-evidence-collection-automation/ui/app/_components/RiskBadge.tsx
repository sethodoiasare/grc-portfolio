const colors: Record<string, string> = {
  CRITICAL: "bg-red-500/10 text-red-400 ring-red-500/20",
  HIGH: "bg-orange-500/10 text-orange-400 ring-orange-500/20",
  MEDIUM: "bg-amber-500/10 text-amber-400 ring-amber-500/20",
  LOW: "bg-blue-500/10 text-blue-400 ring-blue-500/20",
  INFORMATIONAL: "bg-slate-500/10 text-slate-400 ring-slate-500/20",
};

export function RiskBadge({ rating }: { rating: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ring-1 ${colors[rating] ?? colors.INFORMATIONAL}`}>
      {rating}
    </span>
  );
}
