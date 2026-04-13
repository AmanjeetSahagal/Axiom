"use client";

import { FormEvent, useEffect, useState } from "react";

import { DatasetTable } from "@/components/DatasetTable";
import { api } from "@/lib/api";
import { Dataset } from "@/lib/types";

const starterRows = [
  {
    input: {
      question: "What is Axiom?",
      context: "Axiom is an LLM evaluation platform for prompt, model, and regression analysis.",
    },
    expected_output: "Axiom is an LLM evaluation platform for prompt, model, and regression analysis.",
    category: "intro",
  },
];

export function DatasetManager() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [name, setName] = useState("Starter Dataset");
  const [schema, setSchema] = useState('{"question":"string","context":"string"}');
  const [rows, setRows] = useState(JSON.stringify(starterRows, null, 2));
  const [status, setStatus] = useState("Loading datasets...");

  async function loadDatasets() {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      const data = await api.datasets(token);
      setDatasets(data);
      setStatus(data.length ? "" : "No datasets yet.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load datasets");
    }
  }

  useEffect(() => {
    void loadDatasets();
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      setStatus("Creating dataset...");
      await api.createDataset(token, {
        name,
        schema: JSON.parse(schema),
        rows: JSON.parse(rows),
      });
      setStatus("Dataset created.");
      await loadDatasets();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to create dataset");
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="grid gap-4 rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
        <h3 className="font-display text-3xl">Create Dataset</h3>
        <input className="rounded-2xl border border-slate-200 px-4 py-3" value={name} onChange={(e) => setName(e.target.value)} />
        <textarea className="min-h-24 rounded-2xl border border-slate-200 px-4 py-3 font-mono text-sm" value={schema} onChange={(e) => setSchema(e.target.value)} />
        <textarea className="min-h-64 rounded-2xl border border-slate-200 px-4 py-3 font-mono text-sm" value={rows} onChange={(e) => setRows(e.target.value)} />
        <button className="w-fit rounded-full bg-ink px-5 py-3 text-white" type="submit">Save Dataset</button>
        <p className="text-sm text-slate-500">{status}</p>
      </form>
      <DatasetTable datasets={datasets} />
    </div>
  );
}

