"use client";

import { useEffect, useState } from "react";

import { RunDashboard } from "@/components/RunDashboard";
import { api } from "@/lib/api";
import { Run } from "@/lib/types";

export function DashboardClient() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [status, setStatus] = useState("Loading dashboard...");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const token = window.localStorage.getItem("axiom-token");
      if (!token) {
        if (!cancelled) {
          setStatus("Login required.");
        }
        return;
      }
      try {
        const data = await api.runs(token);
        if (!cancelled) {
          setRuns(data);
          setStatus(data.length ? "" : "No runs yet. Seed demo data or launch one.");
        }
      } catch (error) {
        if (!cancelled) {
          setStatus(error instanceof Error ? error.message : "Failed to load dashboard");
        }
      }
    }

    void load();
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void load();
      }
    }, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return runs.length ? <RunDashboard runs={runs} /> : <div className="rounded-[28px] border border-black/5 bg-white/80 p-8 shadow-panel">{status}</div>;
}
