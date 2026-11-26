"use client";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { api } from "@/lib/api";
import { useWorkspace } from "@/lib/store";

function Form() {
  const router = useRouter();
  const { setToken } = useWorkspace();
  const [register, setRegister] = useState(useSearchParams().get("mode") === "register");
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [org, setOrg] = useState("");
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      const r = await api<{ access_token: string }>(register ? "/auth/register" : "/auth/login", null,
        { method: "POST", body: JSON.stringify(register ? { email, password, organization_name: org || undefined } : { email, password }) });
      setToken(r.access_token); router.push("/dashboard");
    } catch (x: any) { setErr(x.message === "Failed to fetch" ? "Can’t reach the Ripple API. Check that the backend is running." : x.message); }
    setBusy(false);
  }
  const field = "mt-1 w-full rounded-md border border-line bg-ink px-3 py-2 outline-none focus:border-ripple";
  return (
    <form onSubmit={submit} className="card w-full max-w-sm p-6">
      <h1 className="text-2xl font-bold">{register ? "Create your workspace" : "Sign in"}</h1>
      <label className="mt-5 block text-sm">Work email<input className={field} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      <label className="mt-4 block text-sm">Password<input className={field} type="password" required minLength={register ? 10 : 1} value={password} onChange={(e) => setPassword(e.target.value)} />
        {register && <span className="text-xs text-mute">At least 10 characters</span>}</label>
      {register && <label className="mt-4 block text-sm">Team name (optional)<input className={field} value={org} onChange={(e) => setOrg(e.target.value)} /></label>}
      {err && <p role="alert" className="mt-4 text-sm text-coral">{err}</p>}
      <button disabled={busy} className="btn btn-primary mt-6 w-full">{busy ? "Working…" : register ? "Create workspace" : "Sign in"}</button>
      <button type="button" onClick={() => setRegister(!register)} className="mt-4 w-full text-sm text-mute hover:text-fog">{register ? "I already have an account" : "Create an account"}</button>
    </form>
  );
}

export default function Login() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-6">
      <Link href="/"><Logo size={30} /></Link>
      <Suspense><Form /></Suspense>
    </main>
  );
}
