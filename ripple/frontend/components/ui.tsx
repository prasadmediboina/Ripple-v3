import { ReactNode } from "react";

export function ConfBadge({ c }: { c: "high" | "medium" | "low" }) {
  const s = { high: "bg-ripple text-ink", medium: "border border-ripple text-ripple", low: "border border-dashed border-amber text-amber" }[c];
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${s}`}>{c} confidence</span>;
}
export function Status({ s }: { s: string }) {
  const m: Record<string, string> = { complete: "text-mint", running: "text-ripple", queued: "text-mute", failed: "text-coral" };
  return <span className={`inline-flex items-center gap-1.5 text-sm ${m[s] ?? "text-mute"}`}>
    <span className={`h-1.5 w-1.5 rounded-full bg-current ${s === "running" ? "animate-pulse" : ""}`} />{s}</span>;
}
export function Kpi({ label, value, note }: { label: string; value: ReactNode; note?: string }) {
  return (
    <div className="card p-4">
      <div className="text-sm text-mute">{label}</div>
      <div className="mt-1 text-3xl font-semibold tabular-nums">{value}</div>
      {note && <div className="mt-1 text-xs text-mute">{note}</div>}
    </div>
  );
}
export function Meter({ used, limit }: { used: number; limit: number | null }) {
  const pct = limit ? Math.min(100, (used / limit) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm"><span>{used} used</span><span className="text-mute">{limit ? `of ${limit}` : "unlimited"}</span></div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-raised" role="progressbar" aria-valuenow={used} aria-valuemax={limit ?? undefined}>
        <div className={`h-full ${pct > 85 ? "bg-amber" : "bg-ripple"}`} style={{ width: `${limit ? pct : 8}%` }} />
      </div>
    </div>
  );
}
export const short = (id: string) => (id.includes("::") ? id.split("::")[1] : id);
export const fmtDate = (s: string) => new Date(s).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
