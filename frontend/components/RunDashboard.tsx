"use client";

import { Bar, BarChart, CartesianGrid, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Run } from "@/lib/types";
import { MetricCard } from "@/components/MetricCard";

export function RunDashboard({ runs }: { runs: Run[] }) {
  const avgScore = runs.length ? runs.reduce((sum, run) => sum + run.avg_score, 0) / runs.length : 0;
  const totalCost = runs.reduce((sum, run) => sum + run.total_cost, 0);
  const avgLatency = runs.length
    ? runs.reduce((sum, run) => sum + (run.processed_rows ? 1200 : 0), 0) / runs.length
    : 0;
  const passBreakdown = [
    { name: "Completed", value: runs.filter((run) => run.status === "completed").length },
    { name: "In Flight", value: runs.filter((run) => run.status !== "completed").length },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Average Score" value={avgScore.toFixed(2)} hint="Normalized across runs" />
        <MetricCard label="Run Pass Rate" value={`${Math.round((passBreakdown[0].value / Math.max(runs.length, 1)) * 100)}%`} />
        <MetricCard label="Average Latency" value={`${avgLatency.toFixed(0)} ms`} />
        <MetricCard label="Total Cost" value={`$${totalCost.toFixed(4)}`} />
      </div>
      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Score Distribution</h3>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={runs}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="id" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="avg_score" fill="#C7512D" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <h3 className="font-display text-2xl">Pass / Fail</h3>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={passBreakdown} dataKey="value" nameKey="name" outerRadius={100} fill="#0F4C3A" />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

