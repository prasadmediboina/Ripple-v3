"use client";
import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";

type Ws = { token: string | null; demo: boolean; ready: boolean; setToken: (t: string) => void; enterDemo: () => void; logout: () => void };
const Ctx = createContext<Ws>(null as unknown as Ws);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [token, setTok] = useState<string | null>(null);
  const [demo, setDemo] = useState(false);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    try { setTok(localStorage.getItem("ripple_token")); setDemo(localStorage.getItem("ripple_demo") === "1"); } catch {}
    setReady(true);
  }, []);
  const setToken = useCallback((t: string) => { localStorage.setItem("ripple_token", t); localStorage.removeItem("ripple_demo"); setTok(t); setDemo(false); }, []);
  const enterDemo = useCallback(() => { localStorage.setItem("ripple_demo", "1"); setDemo(true); }, []);
  const logout = useCallback(() => { localStorage.removeItem("ripple_token"); localStorage.removeItem("ripple_demo"); setTok(null); setDemo(false); }, []);
  return <Ctx.Provider value={{ token, demo, ready, setToken, enterDemo, logout }}>{children}</Ctx.Provider>;
}
export const useWorkspace = () => useContext(Ctx);
