"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";

import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import { Dataset, OptimizerCandidate, OptimizerJob, PromptTemplate, ProviderKeyStatus } from "@/lib/types";

const modelOptions = [
  { value: "gpt-4.1", label: "GPT-4.1", provider: "openai" },
  { value: "gpt-4.1-mini", label: "GPT-4.1 Mini", provider: "openai" },
  { value: "gpt-4o", label: "GPT-4o", provider: "openai" },
  { value: "claude-3.5-sonnet", label: "Claude 3.5 Sonnet", provider: "anthropic" },
  { value: "claude-3.7-sonnet", label: "Claude 3.7 Sonnet", provider: "anthropic" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash", provider: "gemini" },
  { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro", provider: "gemini" },
] as const;

const evaluatorOptions = [
  { value: "exact", label: "Exact" },
  { value: "semantic", label: "Semantic" },
  { value: "judge", label: "Judge" },
];

function formatCost(value: number) {
  return `$${value.toFixed(4)}`;
}

function candidateLabel(candidate?: OptimizerCandidate | null) {
  if (!candidate) return "None";
  return `${candidate.model} · ${candidate.score.toFixed(2)} · ${formatCost(candidate.cost)}`;
}

function getRecommendedCandidate(job: OptimizerJob | null) {
  if (!job) return null;
  return (
    job.candidates.find((candidate) => candidate.id === job.cheapest_passing_candidate_id) ??
    job.candidates.find((candidate) => candidate.id === job.best_candidate_id) ??
    null
  );
}

function jobIsActive(job?: OptimizerJob | null) {
  return job?.status === "pending" || job?.status === "running";
}

export function OptimizerClient() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [providerStatuses, setProviderStatuses] = useState<ProviderKeyStatus[]>([]);
  const [jobs, setJobs] = useState<OptimizerJob[]>([]);
  const [activeJobId, setActiveJobId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [promptId, setPromptId] = useState("");
  const [candidateModels, setCandidateModels] = useState<string[]>(["gemini-2.5-flash"]);
  const [evaluators, setEvaluators] = useState<string[]>(["exact", "semantic", "judge"]);
  const [targetScore, setTargetScore] = useState(0.85);
  const [maxBudget, setMaxBudget] = useState(1);
  const [maxCandidates, setMaxCandidates] = useState(12);
  const [maxIterations, setMaxIterations] = useState(3);
  const [includeAdversarial, setIncludeAdversarial] = useState(true);
  const [status, setStatus] = useState("Loading optimizer...");

  const activeJob = jobs.find((job) => job.id === activeJobId) ?? jobs[0] ?? null;
  const recommendedCandidate = getRecommendedCandidate(activeJob);
  const bestCandidate = activeJob?.candidates.find((candidate) => candidate.id === activeJob.best_candidate_id) ?? null;
  const cheapestPassingCandidate = activeJob?.candidates.find((candidate) => candidate.id === activeJob.cheapest_passing_candidate_id) ?? null;
  const activeJobIsRunning = jobIsActive(activeJob);
  const processedCandidateCount = activeJob?.candidates.length ?? 0;

  const chartData = useMemo(
    () =>
      (activeJob?.candidates ?? [])
        .filter((candidate) => !candidate.error_message)
        .map((candidate) => ({
          id: candidate.id.slice(0, 8),
          model: candidate.model,
          cost: candidate.cost,
          score: candidate.score,
          latency: candidate.latency_ms,
          pareto: candidate.pareto_optimal,
          target: candidate.passes_target,
        })),
    [activeJob],
  );

  async function load(options?: { silent?: boolean }) {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      const [datasetData, promptData, providerData, jobData] = await Promise.all([
        api.datasets(token),
        api.prompts(token),
        api.providerKeys(token),
        api.optimizerJobs(token),
      ]);
      setDatasets(datasetData);
      setPrompts(promptData);
      setProviderStatuses(providerData);
      setJobs(jobData);
      setDatasetId((current) => current || datasetData[0]?.id || "");
      setPromptId((current) => current || promptData[0]?.id || "");
      setActiveJobId((current) => current || jobData[0]?.id || "");
      if (!options?.silent) {
        setStatus(jobData.length ? "" : "No optimization jobs yet.");
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load optimizer");
    }
  }

  useEffect(() => {
    void load();
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void load({ silent: true });
      }
    }, 4000);
    return () => window.clearInterval(interval);
  }, []);

  async function startJob(event: FormEvent) {
    event.preventDefault();
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    if (!datasetId || !promptId) {
      setStatus("Choose a dataset and seed prompt.");
      return;
    }
    if (!candidateModels.length) {
      setStatus("Choose at least one model.");
      return;
    }
    if (!evaluators.length) {
      setStatus("Choose at least one evaluator.");
      return;
    }
    try {
      setStatus("Starting optimizer job...");
      const job = await api.createOptimizerJob(token, {
        dataset_id: datasetId,
        seed_prompt_template_id: promptId,
        candidate_models: candidateModels,
        evaluators,
        target_score: targetScore,
        max_budget: maxBudget,
        max_candidates: maxCandidates,
        max_iterations: maxIterations,
        include_adversarial: includeAdversarial,
      });
      setActiveJobId(job.id);
      setStatus("Optimizer job queued.");
      await load({ silent: true });
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to start optimizer");
    }
  }

  async function promoteCandidate(candidateId?: string | null) {
    if (!activeJob) return;
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      setStatus("Promoting prompt...");
      const prompt = await api.promoteOptimizerCandidate(token, activeJob.id, candidateId);
      setStatus(`Promoted ${prompt.name} v${prompt.version}.`);
      await load({ silent: true });
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to promote prompt");
    }
  }

  async function cancelActiveJob() {
    if (!activeJob) return;
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    if (!window.confirm(`Abort optimizer job ${activeJob.id.slice(0, 8)}? Completed candidates and runs will remain available.`)) {
      return;
    }
    try {
      setStatus("Requesting optimizer abort...");
      const updated = await api.cancelOptimizerJob(token, activeJob.id);
      setJobs((current) => current.map((job) => (job.id === updated.id ? updated : job)));
      setStatus("Optimizer abort requested.");
      await load({ silent: true });
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to abort optimizer job");
    }
  }

  function toggleModel(model: string, checked: boolean) {
    setCandidateModels((current) => (checked ? Array.from(new Set([...current, model])) : current.filter((item) => item !== model)));
  }

  function toggleEvaluator(evaluator: string, checked: boolean) {
    setEvaluators((current) => (checked ? Array.from(new Set([...current, evaluator])) : current.filter((item) => item !== evaluator)));
  }

  return (
    <div className="space-y-6">
      <form onSubmit={startJob} className="grid gap-4 rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Optimizer</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Find the cheapest passing prompt.</h2>
          </div>
          <button className="btn-primary inline-flex items-center gap-2 text-sm" type="submit" disabled={status === "Starting optimizer job..."}>
            {status === "Starting optimizer job..." ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : null}
            {status === "Starting optimizer job..." ? "Starting..." : "Start Search"}
          </button>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <select className="rounded-2xl border border-slate-200 px-4 py-3" value={datasetId} onChange={(event) => setDatasetId(event.target.value)}>
            <option value="">Select dataset</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name}
              </option>
            ))}
          </select>
          <select className="rounded-2xl border border-slate-200 px-4 py-3" value={promptId} onChange={(event) => setPromptId(event.target.value)}>
            <option value="">Select seed prompt</option>
            {prompts.map((prompt) => (
              <option key={prompt.id} value={prompt.id}>
                {prompt.name} v{prompt.version}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-4 lg:grid-cols-[1.5fr,1fr]">
          <div className="rounded-2xl border border-slate-200 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Models</p>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {modelOptions.map((option) => {
                const provider = providerStatuses.find((statusItem) => statusItem.provider === option.provider);
                const disabled = provider ? !provider.configured : false;
                return (
                  <label key={option.value} className={`rounded-2xl border p-3 text-sm ${candidateModels.includes(option.value) ? "border-ember bg-[#fff8f4]" : "border-slate-200 bg-white"} ${disabled ? "opacity-60" : ""}`}>
                    <div className="flex items-start gap-3">
                      <input
                        className="mt-1"
                        type="checkbox"
                        disabled={disabled}
                        checked={candidateModels.includes(option.value)}
                        onChange={(event) => toggleModel(option.value, event.target.checked)}
                      />
                      <div>
                        <p className="font-medium text-slate-900">{option.label}</p>
                        <p className="font-mono text-xs text-slate-500">{disabled ? `${option.provider} key missing` : option.value}</p>
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Evaluators</p>
            <div className="mt-3 grid gap-2">
              {evaluatorOptions.map((option) => (
                <label key={option.value} className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm">
                  <input type="checkbox" checked={evaluators.includes(option.value)} onChange={(event) => toggleEvaluator(option.value, event.target.checked)} />
                  {option.label}
                </label>
              ))}
            </div>
            <label className="mt-3 flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
              <input type="checkbox" checked={includeAdversarial} onChange={(event) => setIncludeAdversarial(event.target.checked)} />
              Generate adversarial rows
            </label>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <label className="grid gap-2 text-sm text-slate-600">
            Target score
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="number" min="0" max="1" step="0.01" value={targetScore} onChange={(event) => setTargetScore(Number(event.target.value))} />
          </label>
          <label className="grid gap-2 text-sm text-slate-600">
            Max spend
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="number" min="0.01" step="0.01" value={maxBudget} onChange={(event) => setMaxBudget(Number(event.target.value))} />
          </label>
          <label className="grid gap-2 text-sm text-slate-600">
            Max candidates
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="number" min="1" max="50" value={maxCandidates} onChange={(event) => setMaxCandidates(Number(event.target.value))} />
          </label>
          <label className="grid gap-2 text-sm text-slate-600">
            Max iterations
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="number" min="1" max="10" value={maxIterations} onChange={(event) => setMaxIterations(Number(event.target.value))} />
          </label>
        </div>
        {status ? <p className="text-sm text-slate-500">{status}</p> : null}
      </form>

      {jobs.length ? (
        <section className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-display text-2xl text-ink">Optimization Jobs</h3>
            <div className="flex flex-wrap items-center gap-2">
              <select className="rounded-2xl border border-slate-200 px-4 py-3 text-sm" value={activeJob?.id ?? ""} onChange={(event) => setActiveJobId(event.target.value)}>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.id.slice(0, 8)} · {job.status} · {job.candidates.length} candidates
                  </option>
                ))}
              </select>
              {activeJobIsRunning ? (
                <button className="btn-danger text-sm" type="button" onClick={() => void cancelActiveJob()}>
                  Abort Job
                </button>
              ) : null}
            </div>
          </div>
          {activeJob ? (
            <>
              {activeJobIsRunning ? (
                <div className="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-ember/20 bg-[#fff8f4] px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-ember/25 border-t-ember" />
                    <div>
                      <p className="text-sm font-medium text-ink">
                        {activeJob.status === "pending" ? "Optimizer queued" : "Optimizer is evaluating candidates"}
                      </p>
                      <p className="text-xs text-slate-600">
                        {processedCandidateCount}/{activeJob.max_candidates} candidates recorded · polling every 4 seconds
                      </p>
                    </div>
                  </div>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-ember shadow-sm">
                    {Math.round(activeJob.progress * 100)}%
                  </span>
                </div>
              ) : null}
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-ember transition-all" style={{ width: `${Math.round(activeJob.progress * 100)}%` }} />
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-4">
                <MetricCard label="Status" value={activeJob.status} hint={`${Math.round(activeJob.progress * 100)}% complete`} />
                <MetricCard label="Spend" value={formatCost(activeJob.total_spend)} hint={`Budget ${formatCost(activeJob.max_budget)}`} />
                <MetricCard label="Candidates" value={`${processedCandidateCount}/${activeJob.max_candidates}`} hint={`${activeJob.candidate_models.length} model${activeJob.candidate_models.length === 1 ? "" : "s"} in search`} />
                <MetricCard label="Cheapest Passing" value={candidateLabel(cheapestPassingCandidate)} hint={`Target ${activeJob.target_score.toFixed(2)}`} />
              </div>
              {bestCandidate ? (
                <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  Current best: <span className="font-medium text-ink">{candidateLabel(bestCandidate)}</span>
                </div>
              ) : null}
            </>
          ) : null}
        </section>
      ) : null}

      {activeJob ? (
        <section className="grid gap-4 xl:grid-cols-[1.2fr,0.8fr]">
          <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Cost Frontier</p>
                <h3 className="mt-2 font-display text-2xl text-ink">Score vs cost by candidate.</h3>
              </div>
              <button className="btn-secondary text-sm" type="button" onClick={() => void promoteCandidate(recommendedCandidate?.id)}>
                Promote Recommendation
              </button>
            </div>
            <div className="mt-5 h-80">
              {chartData.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 12, right: 18, bottom: 20, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="cost" name="Cost" tickFormatter={(value) => `$${Number(value).toFixed(3)}`} />
                    <YAxis dataKey="score" name="Score" domain={[0, 1]} />
                    <ZAxis dataKey="latency" range={[80, 220]} />
                    <Tooltip formatter={(value, name) => (name === "Cost" ? formatCost(Number(value)) : Number(value).toFixed(3))} cursor={{ strokeDasharray: "3 3" }} />
                    <Scatter name="Candidates" data={chartData.filter((item) => !item.pareto)} fill="#7A8798" />
                    <Scatter name="Pareto" data={chartData.filter((item) => item.pareto)} fill="#C7512D" />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-center">
                  {activeJobIsRunning ? <span className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-ember/25 border-t-ember" /> : null}
                  <p className="font-medium text-slate-800">
                    {activeJobIsRunning ? "Waiting for first candidate result" : "No candidate results yet"}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">The frontier chart will populate as evaluations complete.</p>
                </div>
              )}
            </div>
          </div>
          <div className="rounded-[28px] border border-black/5 bg-[#fff8f4] p-5 shadow-panel">
            <p className="text-xs uppercase tracking-[0.2em] text-ember/80">Recommendation</p>
            <h3 className="mt-2 font-display text-2xl text-ink">{candidateLabel(recommendedCandidate)}</h3>
            {recommendedCandidate ? (
              <>
                <p className="mt-3 text-sm text-slate-600">
                  {recommendedCandidate.passes_target ? "This is the cheapest candidate that meets the target." : "No candidate has met the target yet, so this is the current best result."}
                </p>
                <div className="mt-4 rounded-2xl border border-ember/10 bg-white/80 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Prompt Preview</p>
                  <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap font-mono text-xs text-slate-700">{recommendedCandidate.system_prompt}</pre>
                </div>
              </>
            ) : (
              <div className="mt-4 rounded-2xl border border-ember/10 bg-white/80 p-4">
                {activeJobIsRunning ? (
                  <div className="flex items-center gap-3">
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-ember/25 border-t-ember" />
                    <p className="text-sm text-slate-600">Evaluating prompt variants. Recommendation will appear after scoring starts.</p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-600">Candidates will appear after the worker starts processing.</p>
                )}
              </div>
            )}
          </div>
        </section>
      ) : null}

      {activeJob ? (
        <section className="overflow-hidden rounded-[28px] border border-black/5 bg-white/80 shadow-panel">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-ink text-white">
              <tr>
                <th className="px-4 py-3">Candidate</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Cost</th>
                <th className="px-4 py-3">Latency</th>
                <th className="px-4 py-3">Flags</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {activeJob.candidates.length ? activeJob.candidates.map((candidate) => (
                <tr key={candidate.id} className="border-t border-slate-100 align-top">
                  <td className="px-4 py-3 font-mono text-xs">{candidate.id.slice(0, 8)}</td>
                  <td className="px-4 py-3">{candidate.model}</td>
                  <td className="px-4 py-3">{candidate.score.toFixed(2)}</td>
                  <td className="px-4 py-3">{formatCost(candidate.cost)}</td>
                  <td className="px-4 py-3">{candidate.latency_ms.toFixed(0)} ms</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {candidate.passes_target ? <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-800">target</span> : null}
                      {candidate.pareto_optimal ? <span className="rounded-full bg-orange-100 px-2 py-1 text-xs text-orange-800">pareto</span> : null}
                      {candidate.error_message ? <span className="rounded-full bg-red-100 px-2 py-1 text-xs text-red-800">error</span> : null}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      {candidate.eval_run_id ? (
                        <Link className="btn-secondary text-xs" href={`/runs/${candidate.eval_run_id}`}>
                          Run
                        </Link>
                      ) : null}
                      <button className="btn-secondary text-xs" type="button" onClick={() => void promoteCandidate(candidate.id)}>
                        Promote
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr className="border-t border-slate-100">
                  <td className="px-4 py-8 text-center text-slate-500" colSpan={7}>
                    <div className="flex flex-col items-center justify-center gap-3">
                      {activeJobIsRunning ? <span className="h-7 w-7 animate-spin rounded-full border-2 border-ember/25 border-t-ember" /> : null}
                      <span>{activeJobIsRunning ? "Candidate evaluations are starting..." : "No candidates were created for this job."}</span>
                      {activeJobIsRunning ? (
                        <div className="grid w-full max-w-2xl gap-2">
                          {[0, 1, 2].map((item) => (
                            <div key={item} className="h-10 animate-pulse rounded-2xl bg-slate-100" />
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  );
}
