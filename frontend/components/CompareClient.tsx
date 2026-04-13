"use client";

import { useEffect, useState } from "react";

import { ComparisonChart } from "@/components/ComparisonChart";
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import { Comparison, Run } from "@/lib/types";

export function CompareClient() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [baselineRunId, setBaselineRunId] = useState("");
  const [candidateRunId, setCandidateRunId] = useState("");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [status, setStatus] = useState("Loading runs...");

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
        setBaselineRunId(data[0]?.id || "");
        setCandidateRunId(data[1]?.id || data[0]?.id || "");
        setStatus(data.length >= 2 ? "Choose two runs to compare." : "Create at least two runs to compare.");
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Failed to load runs");
      }
    }

    void load();
  }, []);

  async function onCompare() {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      setStatus("Comparing runs...");
      const data = await api.compare(token, baselineRunId, candidateRunId);
      setComparison(data);
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to compare runs");
    }
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel md:grid-cols-[1fr,1fr,auto]">
        <select className="rounded-2xl border border-slate-200 px-4 py-3" value={baselineRunId} onChange={(e) => setBaselineRunId(e.target.value)}>
          <option value="">Select baseline run</option>
          {runs.map((run) => <option key={run.id} value={run.id}>{run.id.slice(0, 8)} · {run.model}</option>)}
        </select>
        <select className="rounded-2xl border border-slate-200 px-4 py-3" value={candidateRunId} onChange={(e) => setCandidateRunId(e.target.value)}>
          <option value="">Select candidate run</option>
          {runs.map((run) => <option key={run.id} value={run.id}>{run.id.slice(0, 8)} · {run.model}</option>)}
        </select>
        <button className="rounded-full bg-ink px-5 py-3 text-white" type="button" onClick={onCompare}>Compare</button>
        <p className="md:col-span-3 text-sm text-slate-500">{status}</p>
      </section>
      {comparison ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard label="Score Delta" value={comparison.score_delta.toFixed(2)} />
            <MetricCard label="Latency Delta" value={`${comparison.latency_delta.toFixed(0)} ms`} />
            <MetricCard label="Cost Delta" value={`$${comparison.cost_delta.toFixed(4)}`} />
          </div>
          <ComparisonChart comparison={comparison} />
        </>
      ) : null}
    </div>
  );
}

