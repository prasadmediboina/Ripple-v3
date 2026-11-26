import Link from "next/link";
export const metadata = { title: "Terms of Service | Ripple" };
export default function Terms() {
  return (
    <main className="mx-auto max-w-3xl space-y-4 px-6 py-12 leading-7">
      <Link href="/" className="text-sm text-mute hover:text-fog">← Ripple</Link>
      <h1 className="text-3xl font-bold">Terms of Service</h1>
      <p className="rounded-md border border-amber/40 bg-amber/10 p-3 text-sm text-amber">Starter template, not legal advice. Have a lawyer review and complete it before accepting customers. Replace every [BRACKET].</p>
      <p>These terms govern your use of Ripple, provided by [COMPANY LEGAL NAME], [ADDRESS] (&ldquo;we&rdquo;).</p>
      <h2 className="pt-2 text-xl font-semibold">1. The service</h2><p>Ripple analyzes source code you connect and reports potential impacts of code changes. Findings are informational: they are potential impacts, not confirmed defects, and you remain responsible for your own testing and release decisions.</p>
      <h2 className="pt-2 text-xl font-semibold">2. Your code</h2><p>You keep all rights to your code. We read repository contents only to provide analysis, never execute it on our servers, and do not use it to train models. See the Privacy Policy.</p>
      <h2 className="pt-2 text-xl font-semibold">3. Accounts and acceptable use</h2><p>Keep your credentials secure. Do not misuse the service, attempt to access other customers&apos; data, or connect repositories you are not authorized to analyze.</p>
      <h2 className="pt-2 text-xl font-semibold">4. Plans, billing and cancellation</h2><p>Paid plans are billed monthly in INR through Razorpay. You can cancel at any time; access continues until the end of the paid period. [REFUND POLICY].</p>
      <h2 className="pt-2 text-xl font-semibold">5. Disclaimer and liability</h2><p>The service is provided &ldquo;as is&rdquo;. To the extent permitted by law, our liability is limited to the fees you paid in the previous [3/12] months. [GOVERNING LAW AND JURISDICTION].</p>
      <h2 className="pt-2 text-xl font-semibold">6. Contact</h2><p>[SUPPORT EMAIL]</p>
    </main>
  );
}
