import { RunResult } from "@/lib/types";

export function ResultInspector({ results }: { results: RunResult[] }) {
  return (
    <div className="space-y-4">
      {results.map((result) => (
        <article key={result.id} className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
            <span>Latency: {result.latency_ms} ms</span>
            <span>Tokens: {result.tokens}</span>
            {result.error_message ? <span className="rounded-full bg-red-50 px-3 py-1 text-red-700">Row failed</span> : null}
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <h4 className="font-semibold text-ink">Rendered Prompt</h4>
              <pre className="mt-2 whitespace-pre-wrap rounded-2xl bg-slate-50 p-4 text-sm">{result.rendered_prompt}</pre>
            </div>
            <div>
              <h4 className="font-semibold text-ink">{result.error_message ? "Error" : "Model Output"}</h4>
              <pre className="mt-2 whitespace-pre-wrap rounded-2xl bg-slate-50 p-4 text-sm">{result.error_message || result.output}</pre>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {result.scores.map((score) => (
              <div key={score.type} className="rounded-2xl border border-slate-100 bg-white p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{score.type}</p>
                <p className="mt-2 font-display text-3xl">{score.score.toFixed(2)}</p>
                <p className="mt-2 text-sm text-slate-600 break-words">{JSON.stringify(score.metadata)}</p>
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
