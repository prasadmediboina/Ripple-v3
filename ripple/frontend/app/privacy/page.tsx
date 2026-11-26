import Link from "next/link";
export const metadata = { title: "Privacy Policy | Ripple" };
export default function Privacy() {
  return (
    <main className="mx-auto max-w-3xl space-y-4 px-6 py-12 leading-7">
      <Link href="/" className="text-sm text-mute hover:text-fog">← Ripple</Link>
      <h1 className="text-3xl font-bold">Privacy Policy</h1>
      <p className="rounded-md border border-amber/40 bg-amber/10 p-3 text-sm text-amber">Starter template, not legal advice. Have a lawyer review it (including India&apos;s DPDP Act obligations) and replace every [BRACKET].</p>
      <h2 className="pt-2 text-xl font-semibold">What we collect</h2><p>Account data (email, hashed password), team and usage data, and, for connected repositories, source code that we read to produce analyses. Payment details are handled by Razorpay; we never see card numbers.</p>
      <h2 className="pt-2 text-xl font-semibold">How we use source code</h2><p>Only to analyze your pull requests. We access repositories with read-only GitHub App permissions, never execute your code, and do not send it to third-party AI providers unless your team explicitly opts in. We do not use your code to train models.</p>
      <h2 className="pt-2 text-xl font-semibold">Retention and deletion</h2><p>We store derived analysis results (names, paths, dependency evidence). You can request deletion of your account and data at [SUPPORT EMAIL]. [RETENTION PERIOD].</p>
      <h2 className="pt-2 text-xl font-semibold">Subprocessors</h2><p>[HOSTING PROVIDER, e.g. Render/AWS], Razorpay (payments), GitHub (repository access).</p>
      <h2 className="pt-2 text-xl font-semibold">Contact</h2><p>[COMPANY LEGAL NAME], [ADDRESS], [PRIVACY CONTACT EMAIL]</p>
    </main>
  );
}
