"use client";
import type { Report } from "@/lib/types";
import { short } from "./ui";

type P = { x: number; y: number };

export function ImpactGraph({ report, selected, onSelect, size = 560 }: {
  report: Report; selected?: string | null; onSelect?: (id: string) => void; size?: number }) {
  const c = size / 2;
  const maxD = Math.max(1, ...report.findings.map((f) => f.depth));
  const gap = (c - 64) / maxD;
  const pos: Record<string, P> = {};
  const ch = report.changes;
  ch.forEach((n, i) => { const a = (i / Math.max(1, ch.length)) * Math.PI * 2; const r = ch.length > 1 ? 26 : 0; pos[n.node_id] = { x: c + r * Math.cos(a), y: c + r * Math.sin(a) }; });
  for (let d = 1; d <= maxD; d++) {
    const ring = report.findings.filter((f) => f.depth === d);
    ring.forEach((f, i) => { const a = (i / ring.length) * Math.PI * 2 + d * 0.55 - Math.PI / 2; pos[f.affected_node_id] = { x: c + gap * d * Math.cos(a), y: c + gap * d * Math.sin(a) }; });
  }
  const label = (id: string, p: P) => { const t = short(id); const s = t.length > 20 ? t.slice(0, 19) + "…" : t; return { s, anchor: p.x > c + 4 ? "start" : p.x < c - 4 ? "end" : "middle", dx: p.x > c + 4 ? 12 : p.x < c - 4 ? -12 : 0, dy: p.x >= c - 4 && p.x <= c + 4 ? 24 : 4 }; };

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="h-auto w-full" role="img" aria-label="Dependency impact graph: changed code in the centre, dependents in rings by distance">
      {Array.from({ length: maxD }, (_, i) => <circle key={i} cx={c} cy={c} r={gap * (i + 1)} fill="none" stroke="#25345A" strokeDasharray="3 6" />)}
      <circle cx={c} cy={c} r={26} fill="none" stroke="#4DA3FF" className="ring-pulse" />
      <circle cx={c} cy={c} r={26} fill="none" stroke="#4DA3FF" className="ring-pulse" style={{ animationDelay: "1.6s" }} />
      {report.findings.map((f) => {
        const a = pos[f.affected_node_id]; const b = pos[f.path[0]?.target_id] ?? { x: c, y: c };
        const on = selected === f.affected_node_id;
        return <line key={"e" + f.affected_node_id} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={on ? "#4DA3FF" : "#34508A"} strokeWidth={on ? 2 : 1} strokeDasharray={f.confidence === "low" ? "4 4" : undefined} />;
      })}
      {report.findings.map((f) => {
        const p = pos[f.affected_node_id]; const l = label(f.affected_node_id, p); const on = selected === f.affected_node_id;
        const fill = f.confidence === "high" ? "#4DA3FF" : "#101A30"; const stroke = f.confidence === "low" ? "#F2B35E" : "#4DA3FF";
        return (
          <g key={f.affected_node_id} tabIndex={0} role="button" aria-label={`${f.affected_name}, ${f.confidence} confidence, ${f.depth} hops`}
            className="cursor-pointer" onClick={() => onSelect?.(f.affected_node_id)} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect?.(f.affected_node_id)}>
            {f.is_test ? <rect x={p.x - 7} y={p.y - 7} width={14} height={14} rx={2} fill={fill} stroke={stroke} strokeWidth={on ? 3 : 1.6} />
              : <circle cx={p.x} cy={p.y} r={on ? 9 : 7} fill={fill} stroke={stroke} strokeWidth={on ? 3 : 1.6} strokeDasharray={f.confidence === "low" ? "3 2" : undefined} />}
            <text x={p.x + l.dx} y={p.y + l.dy} textAnchor={l.anchor as any} fontSize="11.5" fill={on ? "#E8EEF9" : "#8C9BBA"} fontFamily="JetBrains Mono, monospace">{l.s}</text>
          </g>
        );
      })}
      {ch.map((n) => { const p = pos[n.node_id]; return (
        <g key={n.node_id}><circle cx={p.x} cy={p.y} r={12} fill="#F2736A" /><text x={p.x} y={p.y + (ch.length > 1 ? -18 : 30)} textAnchor="middle" fontSize="12" fontWeight={600} fill="#E8EEF9" fontFamily="JetBrains Mono, monospace">{short(n.node_id)}</text></g>); })}
    </svg>
  );
}

export function GraphLegend() {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-mute">
      <span><i className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-coral" />changed</span>
      <span><i className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-ripple" />high confidence</span>
      <span><i className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full border border-ripple" />medium</span>
      <span><i className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full border border-dashed border-amber" />low (name match)</span>
      <span><i className="mr-1.5 inline-block h-2.5 w-2.5 rounded-sm border border-ripple" />test</span>
    </div>
  );
}
