"use client";

import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";

export function AuthGuard({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = window.localStorage.getItem("axiom-token");
    setAuthenticated(Boolean(token));
    setReady(true);
  }, []);

  if (!ready) {
    return <div className="rounded-[28px] border border-black/5 bg-white/80 p-8 shadow-panel">Loading...</div>;
  }

  if (!authenticated) {
    return (
      <div className="rounded-[28px] border border-dashed border-slate-300 bg-white/80 p-8 shadow-panel">
        <p className="text-lg text-slate-700">You need to authenticate before using the product flows.</p>
        <Link href="/login" className="mt-4 inline-block rounded-full bg-ink px-5 py-3 text-white">
          Go to Login
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}

