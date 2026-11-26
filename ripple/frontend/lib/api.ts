const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error { constructor(public status: number, msg: string) { super(msg); } }

export async function api<T>(path: string, token: string | null, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, { ...init,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers } });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new ApiError(res.status, typeof detail === "string" ? detail : "Request failed");
  }
  return res.json();
}
