"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Bars } from "@/components/charts";
import { Kpi, Meter, Status, fmtDate } from "@/components/ui";
import { api } from "@/lib/api";
import { demoAnalyses, demoDashboard, demoRepos, demoUsage } from "@/lib/demo";
import { useWorkspace } from "@/lib/store";
import type { AnalysisRow, DashboardData, Repo, Usage } from "@/lib/types";

export default function Dashboard() {
  const { token, demo } = useWorkspace();
  const [d, setD] = useState<DashboardData | null>(null); const [rows, setRows] = useState<AnalysisRow[]>([]);
  const [repos, setRepos] = useState<Repo[]>([]); const [usage, setUsage] = useState<Usage | null>(null);
  const [err, setErr] = useState<string | null>(null); const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", full_name: "", installation_id: "" });

  const load = useCallback(async () => {
    if (demo) { setD(demoDashboard); setRows(demoAnalyses); setRepos(demoRepos); setUsage(demoUsage); return; }
    try {
      const [a, b, c, u] = await Promise.all([api<DashboardData>("/dashboard", token), api<AnalysisRow[]>("/analyses", token),
        api<Repo[]>("/repositories", token), api<Usage>("/usage", token)]);
      setD(a); setRows(b); setRepos(c); setUsage(u); setErr(null);
    } catch (e: any) { setErr(e.message); }
  }, [demo, token]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (demo || !rows.some((r) => r.status === "queued" || r.status === "running")) return; const t = setInterval(load, 3000); return () => clearInterval(t); }, [rows, demo, load]);

  async function addRepo(e: React.FormEvent) {
    e.preventDefault(); setMsg(null);
    try { await api("/repositories", token, { method: "POST", body: JSON.stringify({ name: form.name, full_name: form.full_name || null, installation_id: form.installation_id || null }) });
      setForm({ name: "", full_name: "", installation_id: "" }); load(); } catch (x: any) { setMsg(x.message); }
  }
  const [gh, setGh] = useState<{ installation_id: string | null; repositories: { id: string; name: string; full_name: string }[] } | null>(null);
  async function connectGithub() {
    if (demo) return setMsg("GitHub connection is disabled in the sample workspace.");
    try { const r = await api<{ url: string }>("/integrations/github/install-url", token); window.location.href = r.url; } catch (x: any) { setMsg(x.message); }
  }
  async function listGithub() {
    try { setGh(await api("/integrations/github/available-repos", token)); } catch (x: any) { setMsg(x.message); }
  }
  async function importRepo(r: { id: string; name: string; full_name: string }) {
    try { await api("/repositories", token, { method: "POST", body: JSON.stringify({ name: r.name, full_name: r.full_name, github_id: r.id, installation_id: gh?.installation_id }) });
      setMsg(`Added ${r.full_name}. Open a pull request and Ripple will analyze it automatically.`); load(); } catch (x: any) { setMsg(x.message); }
  }
  async function index(id: string) {
    if (demo) return setMsg("Indexing is disabled in the sample workspace.");
    setMsg("Indexing…");
    try { const r = await api<any>(`/repositories/${id}/index`, token, { method: "POST", body: JSON.stringify({ ref: "HEAD" }) }); setMsg(`Indexed ${r.nodes} code elements and ${r.edges} dependencies.`); load(); }
    catch (x: any) { setMsg(x.message); }
  }

  if (err) return <p role="alert" className="text-coral">{err === "Failed to fetch" ? "Can’t reach the Ripple API. Check that the backend is running." : err}</p>;
  if (!d || !usage) return <p className="text-mute">Loading…</p>;
  const maxImpact = Math.max(1, ...rows.map((r) => r.summary?.potentially_affected ?? 0));
  const fb = d.feedback; const judged = (fb.confirmed ?? 0) + (fb.false_positive ?? 0);
  const done = rows.filter((r) => r.status === "complete").length;

  return (
    <div className="space-y-10">
      <div><h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="mt-1 text-mute">What changed, what it may affect, and how much you can trust it.</p></div>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-5" aria-label="Key figures">
        <Kpi label="Repositories" value={d.repositories} />
        <Kpi label="Analyses completed" value={d.analyses_completed} />
        <Kpi label="Potential impacts found" value={d.potentially_affected} note={`across ${d.changed_elements} changed elements`} />
        <Kpi label="Code no test reaches" value={d.coverage_gaps} note="static reachability" />
        <Kpi label="Measured precision" value={d.measured_precision === null ? "–" : `${Math.round(d.measured_precision * 100)}%`}
          note={d.measured_precision === null ? "Appears after your team rates findings" : `from ${judged} rated findings`} />
      </section>

      {d.timeline && <section className="card p-5"><div className="flex items-center justify-between"><h2 className="font-semibold">Analysis activity</h2><span className="text-sm text-mute">last 14 days</span></div><div className="mt-4"><Bars data={d.timeline} label="Analyses per day" /></div></section>}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <section id="analyses" className="card scroll-mt-6 overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-5 py-4"><h2 className="font-semibold">Pull request analyses</h2><span className="text-sm text-mute">{done} of {rows.length} complete</span></div>
          {rows.length === 0 ? <p className="p-6 text-mute">No analyses yet. Add a repository, connect your GitHub App, and open a pull request. Ripple analyzes it automatically.</p> : (
            <ul className="divide-y divide-line">
              {rows.map((r) => (
                <li key={r.id}>
                  <Link href={`/analyses/${r.id}`} className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-4 hover:bg-raised">
                    <div className="min-w-0">
                      <div className="truncate font-medium">#{r.pr_number} {r.title || "Untitled pull request"}</div>
                      <div className="mt-0.5 text-sm text-mute">{r.repository} · {fmtDate(r.created_at)}</div>
                      {r.summary && <div className="mt-3 flex items-center gap-3">
                        <div className="h-1.5 w-40 overflow-hidden rounded-full bg-raised" aria-hidden><div className="h-full bg-ripple" style={{ width: `${(r.summary.potentially_affected / maxImpact) * 100}%` }} /></div>
                        <span className="text-xs text-mute">{r.summary.potentially_affected} potential impacts · {r.summary.recommended_tests} tests · {r.summary.coverage_gaps} untested</span></div>}
                    </div>
                    <Status s={r.status} />
                  </Link>
                </li>))}
            </ul>)}
        </section>

        <div className="space-y-6">
          <section id="usage" className="card scroll-mt-6 p-5">
            <div className="flex items-center justify-between"><h2 className="font-semibold">Usage this month</h2><span className="rounded border border-line px-2 py-0.5 text-xs">{usage.plan}</span></div>
            <div className="mt-4"><Meter used={usage.analyses} limit={usage.limits.analyses_per_month} /></div>
            <p className="mt-3 text-xs text-mute">Repository limit: {usage.limits.repositories ?? "unlimited"}</p>
          </section>
          <section className="card p-5">
            <h2 className="font-semibold">Finding quality</h2>
            {judged === 0 ? <p className="mt-3 text-sm text-mute">Mark findings as confirmed or false positive on a report. Ripple turns that into a measured precision.</p> : (
              <div className="mt-4">
                <div className="flex h-2 overflow-hidden rounded-full bg-raised"><div className="bg-mint" style={{ width: `${((fb.confirmed ?? 0) / judged) * 100}%` }} /><div className="bg-coral" style={{ width: `${((fb.false_positive ?? 0) / judged) * 100}%` }} /></div>
                <div className="mt-2 flex justify-between text-sm"><span className="text-mint">{fb.confirmed ?? 0} confirmed</span><span className="text-coral">{fb.false_positive ?? 0} false positive</span></div>
                {(fb.missed_impact ?? 0) > 0 && <p className="mt-2 text-xs text-amber">{fb.missed_impact} reported missed impacts</p>}
              </div>)}
          </section>
        </div>
      </div>

      <section id="repositories" className="card scroll-mt-6 p-5">
        <h2 className="font-semibold">Repositories</h2>
        {msg && <p className="mt-2 text-sm text-ripple" role="status">{msg}</p>}
        <ul className="mt-4 divide-y divide-line">
          {repos.map((r) => (
            <li key={r.id} className="flex items-center justify-between gap-4 py-3">
              <div><div className="font-medium">{r.name}</div><div className="font-mono text-xs text-mute">{r.full_name ?? r.source} · {r.last_indexed_sha ? `indexed ${r.last_indexed_sha.slice(0, 7)}` : "not indexed yet"}</div></div>
              <button onClick={() => index(r.id)} className="btn btn-ghost">Index now</button>
            </li>))}
          {repos.length === 0 && <li className="py-3 text-mute">No repositories connected.</li>}
        </ul>
        {!demo && <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-line pt-4">
          <button onClick={connectGithub} className="btn btn-primary">Connect GitHub</button>
          <button onClick={listGithub} className="btn btn-ghost">Import connected repositories</button>
          <span className="text-xs text-mute">Read-only access through the Ripple GitHub App.</span></div>}
        {gh && <ul className="mt-3 divide-y divide-line">{gh.repositories.length === 0 && <li className="py-2 text-sm text-mute">No repositories found. Connect GitHub first and grant access to at least one repository.</li>}
          {gh.repositories.map((r) => (<li key={r.id} className="flex items-center justify-between py-2"><span className="font-mono text-sm">{r.full_name}</span><button onClick={() => importRepo(r)} className="btn btn-ghost">Add</button></li>))}</ul>}
        {!demo && <form onSubmit={addRepo} className="mt-4 grid gap-3 border-t border-line pt-4 md:grid-cols-4">
          {(["name", "full_name", "installation_id"] as const).map((k) => (
            <input key={k} required={k === "name"} value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} aria-label={k}
              placeholder={{ name: "Display name", full_name: "owner/repo", installation_id: "GitHub App installation ID" }[k]}
              className="rounded-md border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-ripple" />))}
          <button className="btn btn-primary">Add repository</button>
        </form>}
      </section>
    </div>
  );
}
