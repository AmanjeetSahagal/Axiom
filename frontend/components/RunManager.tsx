"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { Dataset, PromptTemplate, Run } from "@/lib/types";

export function RunManager() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [promptId, setPromptId] = useState("");
  const [model, setModel] = useState("gemini-2.5-flash");
  const [status, setStatus] = useState("Loading runs...");

  async function load() {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      const [datasetData, promptData, runData] = await Promise.all([
        api.datasets(token),
        api.prompts(token),
        api.runs(token),
      ]);
      setDatasets(datasetData);
      setPrompts(promptData);
      setRuns(runData);
      setDatasetId((current) => current || datasetData[0]?.id || "");
      setPromptId((current) => current || promptData[0]?.id || "");
      setStatus(runData.length ? "" : "No runs yet.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load runs");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      setStatus("Launching run...");
      await api.createRun(token, {
        dataset_id: datasetId,
        prompt_template_id: promptId,
        model,
        evaluators: ["exact", "semantic", "judge"],
      });
      setStatus("Run queued.");
      await load();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to create run");
    }
  }

  async function seedDemo() {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      setStatus("Seeding demo data...");
      await api.seedDemo(token);
      setStatus("Demo dataset, prompt, and run created.");
      await load();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to seed demo");
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="grid gap-4 rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel md:grid-cols-2">
        <div className="md:col-span-2 flex items-center justify-between gap-4">
          <h3 className="font-display text-3xl">Launch Evaluation Run</h3>
          <button className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm" onClick={seedDemo} type="button">
            Seed Demo Data
          </button>
        </div>
        <select className="rounded-2xl border border-slate-200 px-4 py-3" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
          <option value="">Select dataset</option>
          {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
        </select>
        <select className="rounded-2xl border border-slate-200 px-4 py-3" value={promptId} onChange={(e) => setPromptId(e.target.value)}>
          <option value="">Select prompt</option>
          {prompts.map((prompt) => <option key={prompt.id} value={prompt.id}>{prompt.name} v{prompt.version}</option>)}
        </select>
        <input className="rounded-2xl border border-slate-200 px-4 py-3 md:col-span-2" value={model} onChange={(e) => setModel(e.target.value)} />
        <button className="w-fit rounded-full bg-ink px-5 py-3 text-white" type="submit">Launch Run</button>
        <p className="md:col-span-2 text-sm text-slate-500">{status}</p>
      </form>
      <section className="rounded-[28px] border border-black/5 bg-white/80 shadow-panel">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-ink text-white">
            <tr>
              <th className="px-4 py-3">Run</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Rows</th>
              <th className="px-4 py-3">Score</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="border-t border-slate-100">
                <td className="px-4 py-3"><Link href={`/runs/${run.id}`} className="text-ember">{run.id.slice(0, 8)}</Link></td>
                <td className="px-4 py-3">{run.model}</td>
                <td className="px-4 py-3 capitalize">{run.status}</td>
                <td className="px-4 py-3">{run.processed_rows}/{run.total_rows}</td>
                <td className="px-4 py-3">{run.avg_score.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
