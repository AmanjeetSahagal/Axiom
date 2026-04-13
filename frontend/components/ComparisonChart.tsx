"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Comparison } from "@/lib/types";

export function ComparisonChart({ comparison }: { comparison: Comparison }) {
  const data = Object.entries(comparison.category_breakdown).map(([category, values]) => ({
    category,
    ...values,
  }));

  return (
    <div className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
      <h3 className="font-display text-2xl">Category Breakdown</h3>
      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="baseline" fill="#D4A72C" radius={[6, 6, 0, 0]} />
            <Bar dataKey="candidate" fill="#0F4C3A" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

