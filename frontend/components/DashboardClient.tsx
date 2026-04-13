"use client";

import { useEffect, useState } from "react";

import { RunDashboard } from "@/components/RunDashboard";
import { api } from "@/lib/api";
import { Run } from "@/lib/types";

export function DashboardClient() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [status, setStatus] = useState("Loading dashboard...");

  useEffect(() => {
    async function load() {
      const token = window.localStorage.getItem("axiom-token");
      if (!token) {
        setStatus("Login required.");
        return;
      }
      try {
        const data = await api.runs(token);
        setRuns(data);
        setStatus(data.length ? "" : "No runs yet. Seed demo data or launch one.");
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Failed to load dashboard");
      }
    }

    void load();
  }, []);

  return runs.length ? <RunDashboard runs={runs} /> : <div className="rounded-[28px] border border-black/5 bg-white/80 p-8 shadow-panel">{status}</div>;
}

