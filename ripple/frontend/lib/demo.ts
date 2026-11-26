// SAMPLE DATA ONLY. Shown in the clearly-labelled demo workspace, never mixed with real metrics.
import type { AnalysisRow, DashboardData, Report, Repo, Usage } from "./types";

const P = "shop/payments.py::process_payment";
const step = (s: string, t: string, ev: string, rel = "calls") => ({ source_id: s, target_id: t, relation: rel, evidence: ev, resolution: "exact" });
const f = (id: string, name: string, file: string, path: any[], conf: "high" | "medium" | "low", test = false) => ({
  changed_node_id: P, affected_node_id: id, affected_name: name, affected_file: file, depth: path.length, path, confidence: conf,
  reason: `${name} reaches process_payment through ${path.length} dependency hop(s)`, is_test: test, status: "potential_impact" });

const co = "shop/orders.py::create_order", ck = "shop/orders.py::checkout", rf = "shop/refunds.py::refund";
const gc = "shop/payments.py::Gateway.charge", sub = "shop/subscriptions.py::renew", tc = "shop/tests/test_orders.py::test_checkout_paid";
const api_ = "shop/api.py::post_checkout";

export const demoReport: Report = {
  summary: { changed_elements: 1, potentially_affected: 7, recommended_tests: 1, coverage_gaps: 3 },
  changes: [{ node_id: P, kind: "modified", node_type: "function", file_path: "shop/payments.py", name: "process_payment" }],
  findings: [
    f(co, "create_order", "shop/orders.py", [step(co, P, "shop/orders.py:9 calls process_payment")], "high"),
    f(rf, "refund", "shop/refunds.py", [step(rf, P, "shop/refunds.py:5 calls process_payment")], "high"),
    f(gc, "Gateway.charge", "shop/payments.py", [step(gc, P, "shop/payments.py:9 calls process_payment")], "high"),
    f(sub, "renew", "shop/subscriptions.py", [step(sub, P, "shop/subscriptions.py:14 calls process_payment")], "high"),
    f(ck, "checkout", "shop/orders.py", [step(ck, co, "shop/orders.py:15 calls create_order"), step(co, P, "shop/orders.py:9 calls process_payment")], "medium"),
    f(tc, "test_checkout_paid", "shop/tests/test_orders.py", [step(tc, ck, "shop/tests/test_orders.py:5 calls checkout"), step(ck, co, "shop/orders.py:15 calls create_order"), step(co, P, "shop/orders.py:9 calls process_payment")], "medium", true),
    f(api_, "post_checkout", "shop/api.py", [step(api_, ck, "shop/api.py:22 calls checkout"), step(ck, co, "shop/orders.py:15 calls create_order"), step(co, P, "shop/orders.py:9 calls process_payment")], "medium"),
  ],
  explanations: {
    [co]: "create_order (shop/orders.py) may be affected by a change to process_payment. Evidence: shop/orders.py:9 calls process_payment. Confidence: high. This is a potential impact, not a confirmed defect.",
    [rf]: "refund passes a negative total into process_payment; the changed validation could alter refund behaviour. Confidence: high. Potential impact, not a confirmed defect.",
  },
  tests: [{ test_node_id: tc, test_name: "test_checkout_paid", file_path: "shop/tests/test_orders.py", reason: "Reaches changed code in 3 dependency hop(s)", covers: ["process_payment"] }],
  coverage_gaps: ["shop/refunds.py::refund", "shop/subscriptions.py::renew", "shop/payments.py::Gateway.charge"],
  unknowns: ["send_marketing line 9: `handler` — target could not be resolved statically (local variable, dynamic or missing)"],
  not_analyzed: ["web/checkout.ts"],
  limitations: ["Only Python is analyzed in this version.", "Test recommendations use static reachability, not runtime coverage."],
};

export const demoAnalyses: AnalysisRow[] = [
  { id: "demo-1", status: "complete", created_at: "2026-11-24T10:12:00Z", pr_number: 482, title: "Tighten payment validation", repository: "shop-backend", summary: demoReport.summary },
  { id: "demo-2", status: "complete", created_at: "2026-11-23T16:40:00Z", pr_number: 479, title: "Add retry to webhook sender", repository: "shop-backend", summary: { changed_elements: 2, potentially_affected: 3, recommended_tests: 2, coverage_gaps: 0 } },
  { id: "demo-3", status: "complete", created_at: "2026-11-22T09:05:00Z", pr_number: 31, title: "Refactor inventory reservation", repository: "inventory-svc", summary: { changed_elements: 5, potentially_affected: 11, recommended_tests: 4, coverage_gaps: 2 } },
  { id: "demo-4", status: "running", created_at: "2026-11-25T08:50:00Z", pr_number: 486, title: "Switch invoice numbering", repository: "shop-backend", summary: null },
];
export const demoRepos: Repo[] = [
  { id: "r1", name: "shop-backend", full_name: "acme/shop-backend", last_indexed_sha: "9f3c2ab", source: "github" },
  { id: "r2", name: "inventory-svc", full_name: "acme/inventory-svc", last_indexed_sha: "41be07d", source: "github" },
];
export const demoDashboard: DashboardData = { repositories: 2, analyses_completed: 3, changed_elements: 8, potentially_affected: 21, coverage_gaps: 5,
  feedback: { confirmed: 14, false_positive: 3 }, measured_precision: 14 / 17 };
export const demoUsage: Usage = { plan: "pro", period: "2026-11", analyses: 142, limits: { repositories: 10, analyses_per_month: 500 } };

// ---- Risk, reviewers, charts and founder data (SAMPLE ONLY) ----
import type { AdminOverview, AuditRow, Day, LeadRow, OrgRow } from "./types";
demoReport.risk = { score: 54, level: "elevated", note: "Transparent heuristic, not a trained predictor. Calibrate with team feedback.", factors: [
  { label: "Breadth of impact", points: 14, detail: "7 production elements may be affected" },
  { label: "Code no test reaches", points: 18, detail: "3 changed or affected element(s) lack a test path" },
  { label: "Unresolved references", points: 3, detail: "1 reference(s) could not be resolved statically" },
  { label: "Changes in unanalyzed files", points: 5, detail: "1 file(s) in languages Ripple can't read yet" },
  { label: "Weak evidence links", points: 0, detail: "" }].filter((f) => f.points > 0) };
demoReport.reviewers = [
  { author: "Meera Nair", files_covered: 3, commits: 21, files: ["shop/payments.py", "shop/orders.py", "shop/refunds.py"] },
  { author: "Arjun Rao", files_covered: 2, commits: 9, files: ["shop/orders.py", "shop/api.py"] }];
const series = (v: number[]): Day[] => v.map((count, i) => ({ date: new Date(Date.UTC(2026, 10, 12 + i)).toISOString().slice(0, 10), count }));
demoDashboard.timeline = series([3, 5, 2, 8, 6, 0, 1, 9, 12, 7, 10, 6, 11, 14]);
export const demoAdmin: AdminOverview = { users: 37, organizations: 29, repositories: 54, analyses_total: 612,
  plans: { free: 21, pro: 5, team: 2, enterprise: 1 }, paying_teams: 7, comped_teams: 1, list_price_mrr_inr: 5 * 799 + 2 * 4999 + 4999, mrr_inr: 5 * 799 + 2 * 4999, mrr_note: "Billed MRR counts teams with an active paid subscription, at list price. Comped/pilot plans set by hand are excluded.",
  milestones: [1, 5, 20, 50, 100].map((t) => ({ target: t, reached: 7 >= t })), signups: series([1, 0, 2, 3, 1, 0, 4, 2, 3, 1, 5, 2, 3, 4]),
  analyses_daily: series([12, 18, 9, 30, 22, 4, 6, 33, 41, 28, 35, 24, 38, 47]), feedback: { confirmed: 118, false_positive: 19 }, measured_precision: 118 / 137,
  leads: { identified: 12, contacted: 8, interviewed: 5, pilot: 3, paying: 2, lost: 4 } };
export const demoOrgs: OrgRow[] = [
  { id: "o1", name: "Acme Payments", plan: "team", members: 12, repositories: 9, analyses_this_month: 214 },
  { id: "o2", name: "Nimbus Labs", plan: "pro", members: 4, repositories: 3, analyses_this_month: 88 },
  { id: "o3", name: "Kiran & Co", plan: "free", members: 1, repositories: 1, analyses_this_month: 14 }];
export const demoLeads: LeadRow[] = [
  { id: "l1", name: "Asha Verma", company: "Finlytics", contact: "asha@finlytics.example", stage: "interviewed", note: "Merges 40 PRs/week; wants Java support" },
  { id: "l2", name: "Rohit Shah", company: "CartNest", contact: "", stage: "contacted", note: "Intro call booked Friday" },
  { id: "l3", name: "Neha Iyer", company: "Pocketly", contact: "", stage: "pilot", note: "Running GitHub Action on 2 repos" },
  { id: "l4", name: "Dev Patel", company: "StackForge", contact: "", stage: "identified", note: "" }];
export const demoAudit: AuditRow[] = [
  { id: 4, organization_id: "o2", action: "analysis.completed", detail: "a91f…", created_at: "2026-11-25T09:14:00Z" },
  { id: 3, organization_id: "o1", action: "admin.plan_changed", detail: "pro -> team", created_at: "2026-11-24T17:02:00Z" },
  { id: 2, organization_id: "o3", action: "user.registered", detail: "", created_at: "2026-11-24T11:40:00Z" }];
