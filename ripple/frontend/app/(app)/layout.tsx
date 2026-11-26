"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Logo } from "@/components/Logo";
import { useWorkspace } from "@/lib/store";

const nav = [{ href: "/dashboard", label: "Overview" }, { href: "/dashboard#analyses", label: "Pull request analyses" },
  { href: "/dashboard#repositories", label: "Repositories" }, { href: "/billing", label: "Billing" }];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { token, demo, ready, logout } = useWorkspace();
  const router = useRouter(); const path = usePathname();
  const [admin, setAdmin] = useState(false);
  useEffect(() => { if (token) api<{ is_admin: boolean }>("/auth/me", token).then((m) => setAdmin(m.is_admin)).catch(() => {}); }, [token]);
  useEffect(() => { if (ready && !token && !demo) router.replace("/login"); }, [ready, token, demo, router]);
  if (!ready || (!token && !demo)) return <div className="p-10 text-mute">Loading workspace…</div>;
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[232px_1fr]">
      <aside className="border-b border-line bg-panel/60 p-4 lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
        <Link href="/" className="block px-2 py-2"><Logo /></Link>
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="Workspace">
          {[...nav, ...(admin || demo ? [{ href: "/command", label: "Command center" }] : [])].map((n) => <Link key={n.href} href={n.href} className={`whitespace-nowrap rounded-md px-3 py-2 text-sm hover:bg-raised ${path === n.href ? "bg-raised" : "text-mute"}`}>{n.label}</Link>)}
        </nav>
        <button onClick={() => { logout(); router.push("/"); }} className="mt-4 rounded-md px-3 py-2 text-left text-sm text-mute hover:bg-raised lg:absolute lg:bottom-4">{demo ? "Leave sample workspace" : "Sign out"}</button>
      </aside>
      <div>
        {demo && <div className="border-b border-amber/40 bg-amber/10 px-6 py-2 text-sm text-amber">Sample workspace: every number here is fictional demo data, not your repositories.</div>}
        <div className="mx-auto max-w-6xl px-6 py-8">{children}</div>
      </div>
    </div>
  );
}
