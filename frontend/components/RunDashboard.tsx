"use client";

import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Run } from "@/lib/types";
import { MetricCard } from "@/components/MetricCard";

const palette = ["#C7512D", "#0F4C3A", "#D4A72C", "#7C4D2D", "#7A8798"];

function getProvider(model: string) {
  if (model.startsWith("gpt-")) return "OpenAI";
  if (model.startsWith("claude-")) return "Anthropic";
  if (model.startsWith("gemini-")) return "Google";
  if (model.startsWith("llama-")) return "Meta / OSS";
  if (model.startsWith("mistral") || model.startsWith("mixtral-")) return "Mistral";
  return "Other";
}

function getRunLatency(run: Run) {
  const rowCount = run.results?.length ?? 0;
  return rowCount
    ? run.results!.reduce((rowSum, result) => rowSum + result.latency_ms, 0) / rowCount
    : 0;
}

export function RunDashboard({ runs }: { runs: Run[] }) {
  const [windowDays, setWindowDays] = useState<"all" | "7" | "30">("all");

  const filteredRuns = useMemo(() => {
    if (windowDays === "all") {
      return runs;
    }
    const cutoff = Date.now() - Number(windowDays) * 24 * 60 * 60 * 1000;
    return runs.filter((run) => new Date(run.created_at).getTime() >= cutoff);
  }, [runs, windowDays]);

  const {
    avgScore,
    totalCost,
    avgLatency,
    failureRate,
    passBreakdown,
    modelBreakdown,
    providerBreakdown,
    runTypeBreakdown,
    categoryBreakdown,
    bestModel,
    topProvider,
  } = useMemo(() => {
    const avgScoreValue = filteredRuns.length ? filteredRuns.reduce((sum, run) => sum + run.avg_score, 0) / filteredRuns.length : 0;
    const totalCostValue = filteredRuns.reduce((sum, run) => sum + run.total_cost, 0);
    const avgLatencyValue = filteredRuns.length
      ? filteredRuns.reduce((sum, run) => sum + getRunLatency(run), 0) / filteredRuns.length
      : 0;
    const failureRateValue = filteredRuns.length
      ? filteredRuns.reduce((sum, run) => sum + (run.total_rows ? run.failed_rows / run.total_rows : 0), 0) / filteredRuns.length
      : 0;

    const passData = [
      { name: "Completed", value: filteredRuns.filter((run) => run.status === "completed").length },
      { name: "In Flight", value: filteredRuns.filter((run) => run.status === "pending" || run.status === "running").length },
      { name: "Failed", value: filteredRuns.filter((run) => run.status === "failed").length },
    ];

    const modelMap = new Map<string, { runs: number; scoreSum: number; failureSum: number; latencySum: number }>();
    const providerMap = new Map<string, { runs: number; scoreSum: number; costSum: number }>();
    const runTypeMap = new Map<string, number>();
    const categoryMap = new Map<string, { rows: number; scoreSum: number; failed: number }>();

    filteredRuns.forEach((run) => {
      const latency = getRunLatency(run);
      const provider = getProvider(run.model);
      const modelEntry = modelMap.get(run.model) ?? { runs: 0, scoreSum: 0, failureSum: 0, latencySum: 0 };
      modelEntry.runs += 1;
      modelEntry.scoreSum += run.avg_score;
      modelEntry.failureSum += run.total_rows ? run.failed_rows / run.total_rows : 0;
      modelEntry.latencySum += latency;
      modelMap.set(run.model, modelEntry);

      const providerEntry = providerMap.get(provider) ?? { runs: 0, scoreSum: 0, costSum: 0 };
      providerEntry.runs += 1;
      providerEntry.scoreSum += run.avg_score;
      providerEntry.costSum += run.total_cost;
      providerMap.set(provider, providerEntry);

      runTypeMap.set(run.run_type, (runTypeMap.get(run.run_type) ?? 0) + 1);

      run.results?.forEach((result) => {
        const category = (result as { category?: string | null }).category || "uncategorized";
        const judgeScore = result.scores.find((score) => score.type === "judge")?.score;
        const semanticScore = result.scores.find((score) => score.type === "semantic")?.score;
        const exactScore = result.scores.find((score) => score.type === "exact")?.score;
        const normalizedJudge = typeof judgeScore === "number" ? judgeScore / 5 : undefined;
        const scoreCandidates = [exactScore, semanticScore, normalizedJudge].filter((value): value is number => typeof value === "number");
        const avgRowScore = scoreCandidates.length
          ? scoreCandidates.reduce((sum, value) => sum + value, 0) / scoreCandidates.length
          : 0;
        const categoryEntry = categoryMap.get(category) ?? { rows: 0, scoreSum: 0, failed: 0 };
        categoryEntry.rows += 1;
        categoryEntry.scoreSum += avgRowScore;
        if (result.error_message) {
          categoryEntry.failed += 1;
        }
        categoryMap.set(category, categoryEntry);
      });
    });

    const modelData = Array.from(modelMap.entries())
      .map(([model, value]) => ({
        model,
        runs: value.runs,
        avgScore: value.scoreSum / value.runs,
        avgFailureRate: value.failureSum / value.runs,
        avgLatency: value.latencySum / value.runs,
      }))
      .sort((a, b) => b.avgScore - a.avgScore);

    const providerData = Array.from(providerMap.entries())
      .map(([provider, value]) => ({
        provider,
        runs: value.runs,
        avgScore: value.scoreSum / value.runs,
        totalCost: value.costSum,
      }))
      .sort((a, b) => b.runs - a.runs);

    const runTypeData = Array.from(runTypeMap.entries()).map(([name, value]) => ({ name, value }));

    const categoryData = Array.from(categoryMap.entries())
      .map(([category, value]) => ({
        category,
        rows: value.rows,
        avgScore: value.rows ? value.scoreSum / value.rows : 0,
        failed: value.failed,
      }))
      .sort((a, b) => b.rows - a.rows);

    return {
      avgScore: avgScoreValue,
      totalCost: totalCostValue,
      avgLatency: avgLatencyValue,
      failureRate: failureRateValue,
      passBreakdown: passData,
      modelBreakdown: modelData,
      providerBreakdown: providerData,
      runTypeBreakdown: runTypeData,
      categoryBreakdown: categoryData,
      bestModel: modelData[0],
      topProvider: providerData[0],
    };
  }, [filteredRuns]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Overview</p>
          <h2 className="mt-2 font-display text-4xl text-ink">Performance across models and run types.</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { value: "all", label: "All Time" },
            { value: "30", label: "30 Days" },
            { value: "7", label: "7 Days" },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setWindowDays(option.value as typeof windowDays)}
              className={windowDays === option.value ? "btn-chip-active text-sm" : "btn-chip text-sm"}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Average Score" value={avgScore.toFixed(2)} hint="Normalized across runs" />
        <MetricCard label="Run Pass Rate" value={`${Math.round((passBreakdown[0].value / Math.max(filteredRuns.length, 1)) * 100)}%`} hint={`${filteredRuns.length} runs in view`} />
        <MetricCard label="Average Latency" value={`${avgLatency.toFixed(0)} ms`} />
        <MetricCard label="Failure Rate" value={`${Math.round(failureRate * 100)}%`} hint={`Total cost $${totalCost.toFixed(4)}`} />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Top Model" value={bestModel?.model ?? "None"} hint={bestModel ? `Avg score ${bestModel.avgScore.toFixed(2)}` : "No runs yet"} />
        <MetricCard label="Top Provider" value={topProvider?.provider ?? "None"} hint={topProvider ? `${topProvider.runs} runs in view` : "No runs yet"} />
        <MetricCard label="Generated Runs" value={`${runTypeBreakdown.find((item) => item.name === "generated")?.value ?? 0}`} />
        <MetricCard label="Imported Runs" value={`${runTypeBreakdown.find((item) => item.name === "imported")?.value ?? 0}`} />
      </div>
      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Model Score Breakdown</h3>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelBreakdown.slice(0, 8)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="model" tick={{ fontSize: 12 }} interval={0} angle={-18} textAnchor="end" height={72} />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Bar dataKey="avgScore" fill="#C7512D" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Run Status Mix</h3>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={passBreakdown} dataKey="value" nameKey="name" outerRadius={100}>
                  {passBreakdown.map((entry, index) => (
                    <Cell key={entry.name} fill={palette[index % palette.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Provider Breakdown</h3>
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-100">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Provider</th>
                  <th className="px-4 py-3 font-medium">Runs</th>
                  <th className="px-4 py-3 font-medium">Avg Score</th>
                  <th className="px-4 py-3 font-medium">Total Cost</th>
                </tr>
              </thead>
              <tbody>
                {providerBreakdown.map((provider) => (
                  <tr key={provider.provider} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium text-slate-800">{provider.provider}</td>
                    <td className="px-4 py-3">{provider.runs}</td>
                    <td className="px-4 py-3">{provider.avgScore.toFixed(2)}</td>
                    <td className="px-4 py-3">${provider.totalCost.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Run Type Mix</h3>
          <div className="mt-6 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={runTypeBreakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {runTypeBreakdown.map((entry, index) => (
                    <Cell key={entry.name} fill={palette[index % palette.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Model Detail</h3>
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-100">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Model</th>
                  <th className="px-4 py-3 font-medium">Runs</th>
                  <th className="px-4 py-3 font-medium">Avg Score</th>
                  <th className="px-4 py-3 font-medium">Avg Latency</th>
                </tr>
              </thead>
              <tbody>
                {modelBreakdown.map((model) => (
                  <tr key={model.model} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium text-slate-800">{model.model}</td>
                    <td className="px-4 py-3">{model.runs}</td>
                    <td className="px-4 py-3">{model.avgScore.toFixed(2)}</td>
                    <td className="px-4 py-3">{model.avgLatency.toFixed(0)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Category Breakdown</h3>
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-100">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Rows</th>
                  <th className="px-4 py-3 font-medium">Avg Score</th>
                  <th className="px-4 py-3 font-medium">Failed</th>
                </tr>
              </thead>
              <tbody>
                {categoryBreakdown.slice(0, 8).map((category) => (
                  <tr key={category.category} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium text-slate-800">{category.category}</td>
                    <td className="px-4 py-3">{category.rows}</td>
                    <td className="px-4 py-3">{category.avgScore.toFixed(2)}</td>
                    <td className="px-4 py-3">{category.failed}</td>
                  </tr>
                ))}
                {!categoryBreakdown.length ? (
                  <tr>
                    <td className="px-4 py-4 text-slate-500" colSpan={4}>No row-level category data yet.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
