"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Gauge } from "@/components/charts";
import { GraphLegend, ImpactGraph } from "@/components/ImpactGraph";
import { ConfBadge, Kpi, Status, short } from "@/components/ui";
import { api } from "@/lib/api";
import { demoReport } from "@/lib/demo";
import { useWorkspace } from "@/lib/store";
import type { Report } from "@/lib/types";

type Detail = { id: string; status: string; error: string | null; report: Report | null };

function markdown(r: Report) {
  const l = [`## Ripple change-impact report`, ``, `${r.summary.changed_elements} changed · ${r.summary.potentially_affected} potentially affected · ${r.summary.recommended_tests} tests to run`, ``];
  r.findings.forEach((f) => l.push(`- \`${f.affected_name}\` (${f.confidence}): ${f.path[0].evidence}`));
  l.push(``, `_Potential impacts, not confirmed defects._`); return l.join("\n");
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const { token, demo } = useWorkspace();
  const [a, setA] = useState<Detail | null>(null); const [err, setErr] = useState<string | null>(null);
  const [sel, setSel] = useState<string | null>(null); const [conf, setConf] = useState<string>("all");
  const [ids, setIds] = useState<Record<string, string>>({}); const [rated, setRated] = useState<Record<string, string>>({}); const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (demo) { setA({ id, status: "complete", error: null, report: demoReport }); return; }
    let stop = false;
    const tick = async () => {
      try {
        const d = await api<Detail>(`/analyses/${id}`, token); if (stop) return; setA(d);
        if (d.status === "complete") { const f = await api<any[]>(`/analyses/${id}/findings`, token); setIds(Object.fromEntries(f.map((x) => [x.affected, x.id]))); }
        else if (d.status !== "failed") setTimeout(tick, 2000);
      } catch (e: any) { setErr(e.message); }
    };
    tick(); return () => { stop = true; };
  }, [id, token, demo]);

  const r = a?.report; const findings = useMemo(() => (r?.findings ?? []).filter((f) => conf === "all" || f.confidence === conf), [r, conf]);
  const cur = r?.findings.find((f) => f.affected_node_id === sel) ?? null;

  async function rate(outcome: string) {
    if (!cur) return;
    setRated({ ...rated, [cur.affected_node_id]: outcome });
    if (!demo) await api("/feedback", token, { method: "POST", body: JSON.stringify({ analysis_id: id, finding_id: ids[cur.affected_node_id], outcome }) }).catch(() => {});
  }

  if (err) return <p role="alert" className="text-coral">{err}</p>;
  if (!a) return <p className="text-mute">Loading report…</p>;
  if (a.status === "failed") return <p role="alert" className="text-coral">Analysis failed: {a.error}</p>;
  if (!r) return <div className="card p-8"><Status s={a.status} /><p className="mt-2 text-mute">Ripple is parsing both versions and tracing dependencies. This page updates itself.</p></div>;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><Link href="/dashboard" className="text-sm text-mute hover:text-fog">← Overview</Link><h1 className="mt-2 text-3xl font-bold tracking-tight">Change-impact report</h1>
          <p className="mt-1 text-mute">{r.changes.map((c) => `${c.kind} ${c.name}`).join(", ") || "No code elements changed"}</p></div>
        <button className="btn btn-ghost" onClick={() => { navigator.clipboard.writeText(markdown(r)); setCopied(true); setTimeout(() => setCopied(false), 1800); }}>{copied ? "Copied" : "Copy as PR comment"}</button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label="Changed elements" value={r.summary.changed_elements} /><Kpi label="Potential impacts" value={r.summary.potentially_affected} />
        <Kpi label="Tests to run" value={r.summary.recommended_tests} /><Kpi label="Code no test reaches" value={r.summary.coverage_gaps} />
      </div>

      {r.risk && (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <section className="card p-5">
            <div className="flex flex-wrap items-center gap-6">
              <Gauge score={r.risk.score} level={r.risk.level} />
              <div className="min-w-0 flex-1"><h2 className="font-semibold">Pull request risk</h2>
                <p className="mt-1 text-sm text-mute">Every point comes from a named factor below. This is a transparent heuristic, not a prediction of bugs.</p></div>
            </div>
            <ul className="mt-4 space-y-3">{r.risk.factors.length === 0 && <li className="text-sm text-mute">No risk factors found.</li>}
              {r.risk.factors.map((f) => (<li key={f.label}><div className="flex justify-between text-sm"><span>{f.label}</span><span className="tabular-nums text-mute">+{f.points}</span></div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-raised" aria-hidden><div className="h-full bg-ripple" style={{ width: `${Math.min(100, f.points * 3.4)}%` }} /></div>
                <div className="mt-1 text-xs text-mute">{f.detail}</div></li>))}</ul>
          </section>
          <section className="card p-5"><h2 className="font-semibold">Suggested reviewers</h2>
            {(r.reviewers ?? []).length === 0 ? <p className="mt-3 text-sm text-mute">Needs git history. Available with the CLI and local repositories; GitHub history lookup is on the roadmap.</p> :
              <ul className="mt-3 space-y-3">{r.reviewers!.map((v) => (<li key={v.author}><div className="font-medium">{v.author}</div>
                <div className="text-xs text-mute">Recently changed {v.files_covered} of the affected files ({v.commits} commits)</div></li>))}</ul>}
          </section>
        </div>)}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <section className="card p-4"><ImpactGraph report={r} selected={sel} onSelect={setSel} /><GraphLegend /></section>
        <section className="card p-5" aria-live="polite">
          {!cur ? <p className="text-mute">Select a node in the graph or a row below to see the dependency path and evidence behind it.</p> : (
            <div>
              <div className="flex flex-wrap items-center gap-3"><h2 className="font-mono text-lg">{cur.affected_name}</h2><ConfBadge c={cur.confidence} /></div>
              <p className="mt-1 font-mono text-xs text-mute">{cur.affected_file}</p>
              <h3 className="mt-5 text-sm font-semibold">Dependency path</h3>
              <ol className="mt-2 space-y-2 border-l border-line pl-4">
                {cur.path.map((s, i) => (<li key={i} className="text-sm"><span className="font-mono">{short(s.source_id)}</span> <span className="text-mute">{s.relation}</span> <span className="font-mono">{short(s.target_id)}</span>
                  <div className="font-mono text-xs text-mute">{s.evidence}{s.resolution === "heuristic" && <span className="ml-2 text-amber">matched by name only</span>}</div></li>))}
              </ol>
              <p className="mt-5 text-sm">{r.explanations[cur.affected_node_id] ?? cur.reason}</p>
              <div className="mt-5 border-t border-line pt-4"><div className="text-sm text-mute">Was this finding useful?</div>
                <div className="mt-2 flex gap-2">{[["confirmed", "Real impact"], ["false_positive", "False positive"]].map(([o, l]) => (
                  <button key={o} onClick={() => rate(o)} aria-pressed={rated[cur.affected_node_id] === o} className={`btn btn-ghost ${rated[cur.affected_node_id] === o ? "!border-ripple" : ""}`}>{l}</button>))}</div></div>
            </div>)}
        </section>
      </div>

      <section className="card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4"><h2 className="font-semibold">All potential impacts</h2>
          <div className="flex gap-1" role="group" aria-label="Filter by confidence">{["all", "high", "medium", "low"].map((c) => (
            <button key={c} onClick={() => setConf(c)} aria-pressed={conf === c} className={`rounded-md px-3 py-1 text-sm ${conf === c ? "bg-raised" : "text-mute hover:text-fog"}`}>{c}</button>))}</div></div>
        <table className="w-full text-left text-sm"><thead className="text-mute"><tr><th className="px-5 py-2 font-normal">Affected</th><th className="font-normal">Hops</th><th className="font-normal">Confidence</th><th className="hidden px-5 font-normal md:table-cell">Evidence</th></tr></thead>
          <tbody>{findings.map((f) => (
            <tr key={f.affected_node_id} onClick={() => { setSel(f.affected_node_id); window.scrollTo({ top: 0, behavior: "smooth" }); }} className="cursor-pointer border-t border-line hover:bg-raised">
              <td className="px-5 py-3 font-mono">{f.affected_name}{f.is_test && <span className="ml-2 text-xs text-mint">test</span>}<div className="text-xs text-mute">{f.affected_file}</div></td>
              <td className="tabular-nums">{f.depth}</td><td><ConfBadge c={f.confidence} /></td><td className="hidden px-5 font-mono text-xs text-mute md:table-cell">{f.path[0].evidence}</td></tr>))}
            {findings.length === 0 && <tr><td className="px-5 py-6 text-mute" colSpan={4}>Nothing at this confidence level.</td></tr>}</tbody></table>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="card p-5"><h2 className="font-semibold">Tests to run</h2>
          {r.tests.length === 0 ? <p className="mt-3 text-sm text-mute">No existing test statically reaches the changed code.</p> :
            <ul className="mt-3 space-y-3">{r.tests.map((t) => <li key={t.test_node_id}><div className="font-mono text-sm">{t.file_path}::{t.test_name}</div><div className="text-xs text-mute">{t.reason}</div></li>)}</ul>}</section>
        <section className="card p-5"><h2 className="font-semibold">No test reaches these</h2>
          {r.coverage_gaps.length === 0 ? <p className="mt-3 text-sm text-mute">Every changed or affected function is reachable from a test.</p> :
            <ul className="mt-3 space-y-2">{r.coverage_gaps.map((g) => <li key={g} className="font-mono text-sm">{short(g)}<span className="ml-2 text-xs text-mute">{g.split("::")[0]}</span></li>)}</ul>}
          <p className="mt-3 text-xs text-mute">Based on static reachability, not runtime coverage.</p></section>
      </div>

      {(r.unknowns.length > 0 || r.not_analyzed.length > 0) && (
        <section className="card border-amber/40 p-5"><h2 className="font-semibold text-amber">What remains unknown</h2>
          <ul className="mt-3 space-y-2 text-sm">{r.unknowns.map((u) => <li key={u}>{u}</li>)}{r.not_analyzed.map((p) => <li key={p}><span className="font-mono">{p}</span> changed but is in a language Ripple does not analyze yet.</li>)}</ul></section>)}
      <p className="text-xs text-mute">{r.limitations.join(" ")}</p>
    </div>
  );
}
