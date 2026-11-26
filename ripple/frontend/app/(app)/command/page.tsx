"use client";
import { useCallback, useEffect, useState } from "react";
import { Bars } from "@/components/charts";
import { Kpi, fmtDate } from "@/components/ui";
import { api } from "@/lib/api";
import { demoAdmin, demoAudit, demoLeads, demoOrgs } from "@/lib/demo";
import { useWorkspace } from "@/lib/store";
import type { AdminOverview, AuditRow, LeadRow, OrgRow } from "@/lib/types";

const STAGES = ["identified", "contacted", "interviewed", "pilot", "paying", "lost"];
const inr = (n: number) => "₹" + n.toLocaleString("en-IN");
const field = "rounded-md border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-ripple";

export default function Command() {
  const { token, demo } = useWorkspace();
  const [o, setO] = useState<AdminOverview | null>(null); const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [leads, setLeads] = useState<LeadRow[]>([]); const [audit, setAudit] = useState<AuditRow[]>([]);
  const [err, setErr] = useState<string | null>(null); const [nl, setNl] = useState({ name: "", company: "", contact: "" });

  const load = useCallback(async () => {
    if (demo) { setO(demoAdmin); setOrgs(demoOrgs); setLeads(demoLeads); setAudit(demoAudit); return; }
    try {
      const [a, b, c, d] = await Promise.all([api<AdminOverview>("/admin/overview", token), api<OrgRow[]>("/admin/organizations", token),
        api<{ leads: LeadRow[] }>("/admin/leads", token), api<AuditRow[]>("/admin/audit", token)]);
      setO(a); setOrgs(b); setLeads(c.leads); setAudit(d); setErr(null);
    } catch (e: any) { setErr(e.message); }
  }, [demo, token]);
  useEffect(() => { load(); }, [load]);

  async function plan(id: string, p: string) {
    if (demo) return setOrgs(orgs.map((x) => (x.id === id ? { ...x, plan: p } : x)));
    await api(`/admin/organizations/${id}/plan`, token, { method: "PATCH", body: JSON.stringify({ plan: p }) }); load();
  }
  async function move(l: LeadRow, dir: number) {
    const stage = STAGES[Math.max(0, Math.min(STAGES.length - 1, STAGES.indexOf(l.stage) + dir))];
    if (demo) return setLeads(leads.map((x) => (x.id === l.id ? { ...x, stage } : x)));
    await api(`/admin/leads/${l.id}`, token, { method: "PATCH", body: JSON.stringify({ stage }) }); load();
  }
  async function remove(l: LeadRow) {
    if (demo) return setLeads(leads.filter((x) => x.id !== l.id));
    await api(`/admin/leads/${l.id}`, token, { method: "DELETE" }); load();
  }
  async function addLead(e: React.FormEvent) {
    e.preventDefault();
    if (demo) setLeads([...leads, { id: "n" + Date.now(), ...nl, stage: "identified", note: "" }]);
    else { await api("/admin/leads", token, { method: "POST", body: JSON.stringify(nl) }); load(); }
    setNl({ name: "", company: "", contact: "" });
  }

  if (err) return <div role="alert" className="card border-amber/40 p-6"><h1 className="text-xl font-semibold text-amber">{err === "Founder access only" ? "Founder access only" : "Could not load"}</h1>
    <p className="mt-2 text-mute">{err === "Founder access only" ? "Start the backend with ADMIN_EMAILS set to your login email, for example ADMIN_EMAILS=you@example.com, then reload." : err}</p></div>;
  if (!o) return <p className="text-mute">Loading…</p>;
  const next = o.milestones.find((m) => !m.reached)?.target;
  const funnel = STAGES.map((s) => ({ s, n: leads.filter((l) => l.stage === s).length }));

  return (
    <div className="space-y-10">
      <div><h1 className="text-3xl font-bold tracking-tight">Command center</h1><p className="mt-1 text-mute">Everything you need to run Ripple as a business, from real data.</p></div>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-5" aria-label="Business figures">
        <Kpi label="Users" value={o.users} note={`${o.organizations} teams`} />
        <Kpi label="Paying teams" value={o.paying_teams} note={`${o.comped_teams} comped or pilot · ${next ? `next milestone: ${next}` : "all milestones reached"}`} />
        <Kpi label="Billed MRR" value={inr(o.mrr_inr)} note="active subscriptions only" />
        <Kpi label="Analyses run" value={o.analyses_total} note={`${o.repositories} repositories`} />
        <Kpi label="Measured precision" value={o.measured_precision === null ? "–" : `${Math.round(o.measured_precision * 100)}%`} note={o.measured_precision === null ? "needs feedback" : "from rated findings"} />
      </section>

      <section className="card p-5"><h2 className="font-semibold">Paying-team milestones</h2>
        <ol className="mt-4 grid grid-cols-5 gap-2">{o.milestones.map((m) => (<li key={m.target} className="text-center">
          <div className={`mx-auto flex h-10 w-10 items-center justify-center rounded-full border text-sm font-semibold ${m.reached ? "border-mint bg-mint text-ink" : "border-line text-mute"}`}>{m.target}</div>
          <div className="mt-1 text-xs text-mute">{m.reached ? "reached" : "target"}</div></li>))}</ol>
        <p className="mt-4 text-xs text-mute">{o.mrr_note}</p></section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="card p-5"><h2 className="font-semibold">Signups, last 14 days</h2><div className="mt-4"><Bars data={o.signups} label="Signups per day" /></div></section>
        <section className="card p-5"><h2 className="font-semibold">Analyses, last 14 days</h2><div className="mt-4"><Bars data={o.analyses_daily} label="Analyses per day" /></div></section>
      </div>

      <section className="card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-semibold">Customer pipeline</h2>
        <div className="flex flex-wrap gap-3 text-xs text-mute">{funnel.map((f) => <span key={f.s}>{f.s} <b className="text-fog">{f.n}</b></span>)}</div></div>
        <div className="mt-4 grid gap-3 overflow-x-auto md:grid-cols-3 xl:grid-cols-6">
          {STAGES.map((s) => (<div key={s} className="min-w-[160px] rounded-md bg-ink/60 p-2"><div className="px-1 pb-2 text-xs font-medium capitalize text-mute">{s}</div>
            <ul className="space-y-2">{leads.filter((l) => l.stage === s).map((l) => (<li key={l.id} className="rounded-md border border-line bg-panel p-2 text-sm">
              <div className="font-medium">{l.name}</div><div className="text-xs text-mute">{l.company}</div>{l.note && <div className="mt-1 text-xs">{l.note}</div>}
              <div className="mt-2 flex gap-1"><button aria-label={`Move ${l.name} back`} onClick={() => move(l, -1)} className="rounded border border-line px-2 text-xs hover:bg-raised">←</button>
                <button aria-label={`Move ${l.name} forward`} onClick={() => move(l, 1)} className="rounded border border-line px-2 text-xs hover:bg-raised">→</button>
                <button aria-label={`Remove ${l.name}`} onClick={() => remove(l)} className="ml-auto rounded px-2 text-xs text-mute hover:text-coral">remove</button></div></li>))}</ul></div>))}
        </div>
        <form onSubmit={addLead} className="mt-4 grid gap-3 border-t border-line pt-4 md:grid-cols-4">
          <input required aria-label="Name" placeholder="Contact name" className={field} value={nl.name} onChange={(e) => setNl({ ...nl, name: e.target.value })} />
          <input aria-label="Company" placeholder="Company" className={field} value={nl.company} onChange={(e) => setNl({ ...nl, company: e.target.value })} />
          <input aria-label="Contact" placeholder="Email or LinkedIn" className={field} value={nl.contact} onChange={(e) => setNl({ ...nl, contact: e.target.value })} />
          <button className="btn btn-primary">Add to pipeline</button></form></section>

      <section className="card overflow-hidden"><div className="border-b border-line px-5 py-4"><h2 className="font-semibold">Teams</h2><p className="mt-1 text-xs text-mute">Changing a plan here grants access without charging (comp or pilot). Revenue only counts real Razorpay subscriptions.</p></div>
        <table className="w-full text-left text-sm"><thead className="text-mute"><tr><th className="px-5 py-2 font-normal">Team</th><th className="font-normal">Plan</th><th className="font-normal">Members</th><th className="font-normal">Repos</th><th className="px-5 font-normal">Analyses this month</th></tr></thead>
          <tbody>{orgs.map((t) => (<tr key={t.id} className="border-t border-line"><td className="px-5 py-3 font-medium">{t.name}</td>
            <td><select aria-label={`Plan for ${t.name}`} value={t.plan} onChange={(e) => plan(t.id, e.target.value)} className={field}>{["free", "pro", "team", "enterprise"].map((p) => <option key={p}>{p}</option>)}</select></td>
            <td className="tabular-nums">{t.members}</td><td className="tabular-nums">{t.repositories}</td><td className="px-5 tabular-nums">{t.analyses_this_month}</td></tr>))}</tbody></table></section>

      <section className="card p-5"><h2 className="font-semibold">Recent activity</h2>
        <ul className="mt-3 divide-y divide-line text-sm">{audit.map((a) => (<li key={a.id} className="flex flex-wrap justify-between gap-2 py-2"><span><span className="font-mono">{a.action}</span> <span className="text-mute">{a.detail}</span></span><span className="text-mute">{fmtDate(a.created_at)}</span></li>))}
          {audit.length === 0 && <li className="py-2 text-mute">Nothing yet.</li>}</ul></section>
    </div>
  );
}
