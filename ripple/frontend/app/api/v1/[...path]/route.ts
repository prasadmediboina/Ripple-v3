// Same-origin proxy to the FastAPI backend, read at RUNTIME (BACKEND_URL), so no CORS and no rebuild to change it.
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
const SKIP = new Set(["host", "connection", "content-length", "transfer-encoding", "content-encoding", "keep-alive"]);

function backend() {
  const b = process.env.BACKEND_URL ?? "http://localhost:8000";
  return (b.startsWith("http") ? b : `http://${b}`).replace(/\/$/, "");
}

async function handler(req: NextRequest, { params }: { params: { path: string[] } }) {
  const target = `${backend()}/api/v1/${params.path.join("/")}${req.nextUrl.search}`;
  const headers = new Headers();
  req.headers.forEach((v, k) => { if (!SKIP.has(k)) headers.set(k, v); });
  headers.set("accept-encoding", "identity");
  try {
    const res = await fetch(target, { method: req.method, headers, redirect: "manual", cache: "no-store",
      body: ["GET", "HEAD"].includes(req.method) ? undefined : await req.arrayBuffer() });
    const out = new Headers();
    res.headers.forEach((v, k) => { if (!SKIP.has(k)) out.set(k, v); });
    return new NextResponse([204, 304].includes(res.status) ? null : res.body, { status: res.status, headers: out });
  } catch {
    return NextResponse.json({ detail: "The Ripple backend is unreachable. Check that it is running." }, { status: 502 });
  }
}
export { handler as GET, handler as POST, handler as PATCH, handler as PUT, handler as DELETE };
