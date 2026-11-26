"use client";
import { useCallback, useEffect, useState } from "react";
import { Meter } from "@/components/ui";
import { api } from "@/lib/api";
import { useWorkspace } from "@/lib/store";
import type { Usage } from "@/lib/types";

type Billing = { configured: boolean; plan: string; can_manage: boolean; subscription: { plan: string; status: string };
  plans: { id: string; name: string; price_inr: number; limits: { repositories: number | null; analyses_per_month: number | null } }[] };

const STATUS: Record<string, string> = { active: "Active", created: "Waiting for payment", cancelling: "Cancels at the end of the billing period",
  past_due: "Payment failed, retrying", cancelled: "Cancelled", halted: "Halted after failed payments", completed: "Completed", expired: "Expired" };

export default function BillingPage() {
  const { token, demo } = useWorkspace();
  const [b, setB] = useState<Billing | null>(null); const [u, setU] = useState<Usage | null>(null);
  const [msg, setMsg] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (demo) { setB({ configured: true, plan: "pro", can_manage: true, subscription: { plan: "pro", status: "active" },
      plans: [{ id: "pro", name: "Developer Pro", price_inr: 799, limits: { repositories: 10, analyses_per_month: 500 } }, { id: "team", name: "Team", price_inr: 4999, limits: { repositories: 50, analyses_per_month: 5000 } }] });
      setU({ plan: "pro", period: "2026-11", analyses: 142, limits: { repositories: 10, analyses_per_month: 500 } }); return; }
    try { setB(await api<Billing>("/billing", token)); setU(await api<Usage>("/usage", token)); } catch (e: any) { setMsg(e.message); }
  }, [demo, token]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (demo || b?.subscription.status !== "created") return; const t = setInterval(load, 4000); return () => clearInterval(t); }, [b, demo, load]);

  async function choose(plan: string) {
    if (demo) return setMsg("Payments are disabled in the sample workspace.");
    setBusy(true); setMsg(null);
    try { const r = await api<{ checkout_url: string }>("/billing/checkout", token, { method: "POST", body: JSON.stringify({ plan }) }); window.location.href = r.checkout_url; }
    catch (e: any) { setMsg(e.message); setBusy(false); }
  }
  async function cancel() {
    if (demo || !confirm("Cancel your subscription? You keep access until the end of the paid period.")) return;
    try { await api("/billing/cancel", token, { method: "POST" }); load(); } catch (e: any) { setMsg(e.message); }
  }

  if (!b) return <p className="text-mute">{msg ?? "Loading…"}</p>;
  const paid = b.plan !== "free";
  return (
    <div className="space-y-8">
      <div><h1 className="text-3xl font-bold tracking-tight">Billing</h1><p className="mt-1 text-mute">Payments are handled by Razorpay. Ripple never sees your card details.</p></div>
      {msg && <p role="alert" className="rounded-md border border-amber/40 bg-amber/10 px-4 py-3 text-sm text-amber">{msg}</p>}
      {!b.configured && <p className="rounded-md border border-line px-4 py-3 text-sm text-mute">Payments are not configured on this deployment yet (see docs/BILLING.md).</p>}

      <section className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="text-sm text-mute">Current plan</div><div className="text-2xl font-semibold capitalize">{b.plan}</div>
          <div className="mt-1 text-sm text-mute">{STATUS[b.subscription.status] ?? b.subscription.status}</div></div>
          {paid && b.can_manage && b.subscription.status === "active" && <button onClick={cancel} className="btn btn-ghost">Cancel subscription</button>}</div>
        {u && <div className="mt-5 max-w-sm"><div className="mb-1 text-sm text-mute">Analyses this month</div><Meter used={u.analyses} limit={u.limits.analyses_per_month} /></div>}
      </section>

      <section className="grid gap-4 md:grid-cols-3" aria-label="Plans">
        {b.plans.map((p) => (
          <div key={p.id} className={`card p-5 ${b.plan === p.id ? "border-ripple" : ""}`}>
            <div className="font-semibold">{p.name}</div>
            <div className="mt-2 text-3xl font-bold">₹{p.price_inr.toLocaleString("en-IN")}<span className="text-sm font-normal text-mute"> / month</span></div>
            <ul className="mt-4 space-y-1 text-sm text-mute"><li>{p.limits.repositories} repositories</li><li>{p.limits.analyses_per_month?.toLocaleString("en-IN")} analyses a month</li></ul>
            <button disabled={busy || !b.can_manage || !b.configured || b.plan === p.id || (paid && b.plan !== p.id)} onClick={() => choose(p.id)} className="btn btn-primary mt-5 w-full disabled:opacity-40">
              {b.plan === p.id ? "Current plan" : `Choose ${p.name}`}</button>
          </div>))}
        <div className="card p-5"><div className="font-semibold">Enterprise</div><div className="mt-2 text-3xl font-bold">Custom</div>
          <ul className="mt-4 space-y-1 text-sm text-mute"><li>Unlimited scale</li><li>Audit logs, private deployment</li></ul>
          <a href="mailto:hello@example.com?subject=Ripple%20Enterprise" className="btn btn-ghost mt-5 w-full">Contact us</a></div>
      </section>
      {paid && <p className="text-sm text-mute">To switch plans, cancel the current subscription first, then choose the new one.</p>}
      {!b.can_manage && <p className="text-sm text-mute">Only the team owner can change the plan.</p>}
    </div>
  );
}
