"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";
import { ImpactGraph, GraphLegend } from "@/components/ImpactGraph";
import { demoReport } from "@/lib/demo";
import { useWorkspace } from "@/lib/store";

const plans = [
  { name: "Free", price: "₹0", items: ["1 repository", "20 analyses a month", "Dependency graph", "Community support"] },
  { name: "Developer Pro", price: "₹799", items: ["10 repositories", "500 analyses a month", "PR impact reports", "Test recommendations", "Analysis history"], hot: true },
  { name: "Team", price: "₹4,999", items: ["50 repositories", "5,000 analyses a month", "Organization dashboard", "Usage reports", "Shared repository intelligence"] },
  { name: "Enterprise", price: "Custom", items: ["Unlimited scale", "Audit logs", "Private deployment", "Custom integrations", "Dedicated support"] },
];

export default function Landing() {
  const { enterDemo } = useWorkspace();
  const router = useRouter();
  const demo = () => { enterDemo(); router.push("/dashboard"); };
  return (
    <main>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Logo />
        <nav className="flex items-center gap-5 text-sm text-mute">
          <a href="#how" className="hover:text-fog">How it works</a><a href="#trust" className="hover:text-fog">Security</a><a href="#pricing" className="hover:text-fog">Pricing</a>
          <Link href="/login" className="btn btn-ghost">Sign in</Link>
        </nav>
      </header>

      <section className="mx-auto grid max-w-6xl items-center gap-10 px-6 pb-20 pt-10 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <h1 className="text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl">Know what a pull request will touch before you merge it.</h1>
          <p className="mt-6 max-w-xl text-lg text-mute">Ripple traces every change through your code, shows the exact dependency path behind each warning, and tells you which tests to run and which areas no test reaches.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/login?mode=register" className="btn btn-primary">Start free</Link>
            <button onClick={demo} className="btn btn-ghost">Explore a sample workspace</button>
          </div>
          <p className="mt-4 text-sm text-mute">Findings are labelled potential impacts. A dependency is not a defect, and Ripple never says otherwise.</p>
        </div>
        <div className="card p-4">
          <ImpactGraph report={demoReport} size={520} />
          <div className="mt-2 flex items-center justify-between gap-4"><GraphLegend /><span className="text-xs text-mute">Illustrative example</span></div>
        </div>
      </section>

      <section id="how" className="border-y border-line bg-panel/50">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 py-16 lg:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Every finding shows its work</h2>
            <p className="mt-4 max-w-lg text-mute">Analysis is deterministic first. Ripple parses your code, builds the call graph and walks it backwards from what changed. AI only explains results; it cannot add findings.</p>
            <ol className="mt-8 space-y-4">
              {["A pull request opens or updates", "Ripple compares the syntax trees of both versions, so formatting and comment edits are ignored", "It follows callers outward and records the line of code behind every hop", "It picks tests that reach the change and lists code that no test reaches", "The report lands in Ripple and as a pull request comment"].map((t, i) => (
                <li key={i} className="flex gap-4"><span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-ripple text-xs text-ripple">{i + 1}</span><span>{t}</span></li>))}
            </ol>
          </div>
          <div className="card p-5 font-mono text-sm leading-7">
            <div className="text-coral">modified  process_payment()</div>
            <div className="text-mute">shop/orders.py:9 calls process_payment</div>
            <div>↳ create_order <span className="text-ripple">· high confidence</span></div>
            <div className="text-mute">shop/orders.py:15 calls create_order</div>
            <div>↳ checkout <span className="text-ripple">· medium confidence</span></div>
            <div className="text-mute">shop/tests/test_orders.py:5 calls checkout</div>
            <div>↳ test_checkout_paid <span className="text-mint">· run this test</span></div>
            <div className="mt-3 text-amber">unknown: handler() in send_marketing is resolved at runtime</div>
          </div>
        </div>
      </section>

      <section id="trust" className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-3xl font-bold tracking-tight">Built for private repositories</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[["Your code is read, never run", "Analysis reads git objects and archives with size limits. Repository code is never executed on Ripple servers."],
            ["Runs in your own CI", "The open CLI and GitHub Action analyze pull requests inside your pipeline, so source never leaves your infrastructure."],
            ["No numbers we can’t back up", "Dashboard metrics come from stored data. Precision appears only after your team gives feedback on real findings."]].map(([h, p]) => (
            <div key={h} className="card p-5"><h3 className="font-semibold">{h}</h3><p className="mt-2 text-sm text-mute">{p}</p></div>))}
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-6xl px-6 pb-20">
        <h2 className="text-3xl font-bold tracking-tight">Pricing</h2>
        <p className="mt-2 text-mute">Launch pricing, subject to validation with early teams.</p>
        <div className="mt-8 grid gap-4 md:grid-cols-4">
          {plans.map((p) => (
            <div key={p.name} className={`card p-5 ${p.hot ? "border-ripple" : ""}`}>
              <div className="font-semibold">{p.name}</div>
              <div className="mt-2 text-3xl font-bold">{p.price}<span className="text-sm font-normal text-mute">{p.price.startsWith("₹") && p.price !== "₹0" ? " / month" : ""}</span></div>
              <ul className="mt-4 space-y-2 text-sm text-mute">{p.items.map((i) => <li key={i}>{i}</li>)}</ul>
            </div>))}
        </div>
      </section>
      <footer className="flex flex-wrap items-center justify-center gap-6 border-t border-line py-8 text-sm text-mute"><span>© 2026 Ripple. Understand every change.</span><Link href="/terms" className="hover:text-fog">Terms</Link><Link href="/privacy" className="hover:text-fog">Privacy</Link></footer>
    </main>
  );
}
