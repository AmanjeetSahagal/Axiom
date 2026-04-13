"use client";

import { useEffect, useState } from "react";

import { ResultInspector } from "@/components/ResultInspector";
import { api } from "@/lib/api";
import { Run } from "@/lib/types";

export function RunDetailClient({ id }: { id: string }) {
  const [run, setRun] = useState<Run | null>(null);
  const [status, setStatus] = useState("Loading run...");

  useEffect(() => {
    async function load() {
      const token = window.localStorage.getItem("axiom-token");
      if (!token) {
        setStatus("Login required.");
        return;
      }
      try {
        const data = await api.run(token, id);
        setRun(data);
        setStatus("");
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Failed to load run");
      }
    }

    void load();
  }, [id]);

  if (!run) {
    return <div className="rounded-[28px] border border-black/5 bg-white/80 p-8 shadow-panel">{status}</div>;
  }

  return (
    <section className="space-y-6">
      <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
        <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Run Detail</p>
        <h2 className="mt-2 font-display text-4xl text-ink">{run.model}</h2>
        <p className="mt-3 text-slate-600">
          Status: {run.status} | Rows: {run.processed_rows}/{run.total_rows} | Average score: {run.avg_score.toFixed(2)}
        </p>
      </div>
      <ResultInspector results={run.results || []} />
    </section>
  );
}

