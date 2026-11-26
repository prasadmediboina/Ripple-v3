import type { Day } from "@/lib/types";

export function Bars({ data, label }: { data: Day[]; label: string }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  const w = 28, h = 96;
  return (
    <figure>
      <svg viewBox={`0 0 ${data.length * w} ${h + 18}`} className="w-full" role="img" aria-label={`${label}: ${data.map((d) => `${d.date} ${d.count}`).join(", ")}`}>
        {data.map((d, i) => { const bh = d.count === 0 ? 2 : Math.max(4, (d.count / max) * h); return (
          <g key={d.date}><rect x={i * w + 5} y={h - bh} width={w - 10} height={bh} rx={3} fill={d.count ? "#4DA3FF" : "#25345A"} opacity={d.count ? 0.9 : 1}><title>{`${d.date}: ${d.count}`}</title></rect>
            {(i === 0 || i === data.length - 1 || i === Math.floor(data.length / 2)) && <text x={i * w + w / 2} y={h + 13} textAnchor="middle" fontSize="9" fill="#8C9BBA">{d.date.slice(5)}</text>}</g>); })}
      </svg>
    </figure>
  );
}

const LEVEL: Record<string, string> = { low: "#58D3A4", moderate: "#4DA3FF", elevated: "#F2B35E", high: "#F2736A" };

export function Gauge({ score, level }: { score: number; level: string }) {
  const r = 52, c = Math.PI * r, color = LEVEL[level] ?? "#4DA3FF";
  return (
    <svg viewBox="0 0 140 84" className="w-40" role="img" aria-label={`Risk ${score} out of 100, ${level}`}>
      <path d="M18 76 A52 52 0 0 1 122 76" fill="none" stroke="#25345A" strokeWidth="12" strokeLinecap="round" />
      <path d="M18 76 A52 52 0 0 1 122 76" fill="none" stroke={color} strokeWidth="12" strokeLinecap="round" strokeDasharray={`${(score / 100) * c} ${c}`} />
      <text x="70" y="66" textAnchor="middle" fontSize="28" fontWeight="700" fill="#E8EEF9">{score}</text>
      <text x="70" y="82" textAnchor="middle" fontSize="10" fill={color}>{level}</text>
    </svg>
  );
}
