import Link from "next/link";

import { LogoMark } from "@/components/LogoMark";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-14 lg:px-10">
      <section className="grid gap-8 lg:grid-cols-[1.15fr,0.85fr] lg:items-stretch">
        <div className="flex flex-col justify-between rounded-[36px] border border-black/5 bg-white/80 p-8 shadow-panel backdrop-blur md:p-10">
          <div>
            <div className="flex items-center gap-4">
              <LogoMark size="lg" />
              <div>
                <p className="text-sm uppercase tracking-[0.32em] text-ember">Axiom</p>
                <p className="mt-2 font-display text-3xl text-ink">Evaluation OS</p>
              </div>
            </div>
            <h1 className="mt-10 max-w-4xl font-display text-5xl leading-[1.02] text-ink md:text-6xl">
              Turn prompt and model iteration into a measurable engineering loop.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Run datasets against model variants, score hallucinations and regressions, and compare quality, latency, and cost without falling back to spreadsheet guesswork.
            </p>
          </div>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/dashboard" className="btn-primary px-7">
              Open Dashboard
            </Link>
            <Link href="/login" className="btn-secondary px-7">
              Continue with Google
            </Link>
          </div>
        </div>

        <div className="grid gap-6">
          <div className="rounded-[36px] border border-ember/10 bg-[#17162a] p-8 text-white shadow-panel">
            <p className="text-sm uppercase tracking-[0.28em] text-white/60">Workflow</p>
            <div className="mt-8 grid gap-4">
              {[
                ["1", "Upload datasets", "Bring CSV or JSON evaluation sets with expected answers, categories, and imported outputs."],
                ["2", "Launch runs", "Test generated or imported runs across Gemini, GPT, Claude, and future providers."],
                ["3", "Inspect evidence", "Drill into row-level disagreements, judge reasoning, and category-level regressions."],
              ].map(([step, title, body]) => (
                <div key={step} className="grid grid-cols-[auto,1fr] gap-4 rounded-[24px] border border-white/10 bg-white/5 p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-ember font-semibold text-white">{step}</div>
                  <div>
                    <p className="font-semibold text-white">{title}</p>
                    <p className="mt-1 text-sm leading-6 text-white/70">{body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ["Quality", "Exact, semantic, and judge scoring in one run."],
              ["Speed", "Async workers keep the API responsive at scale."],
              ["Cost", "Track tradeoffs by model, provider, and run type."],
            ].map(([title, body]) => (
              <div key={title} className="rounded-[28px] border border-black/5 bg-white/75 p-5 shadow-panel">
                <p className="text-sm uppercase tracking-[0.22em] text-ember">{title}</p>
                <p className="mt-3 text-sm leading-6 text-slate-600">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[0.95fr,1.05fr]">
        <div className="rounded-[36px] border border-black/5 bg-white/80 p-8 shadow-panel">
          <p className="text-sm uppercase tracking-[0.28em] text-slate-500">What You Measure</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {[
              ["Average score", "See whether a prompt or model is actually better."],
              ["Hallucination rate", "Catch groundedness failures before they ship."],
              ["Latency", "Understand the speed cost of higher-quality models."],
              ["Run comparisons", "Baseline one run directly against another."],
            ].map(([title, body]) => (
              <div key={title} className="rounded-[24px] border border-slate-100 bg-slate-50 p-5">
                <p className="font-semibold text-ink">{title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[36px] border border-black/5 bg-white/80 p-8 shadow-panel">
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              ["500+", "Rows per run"],
              ["Generated", "and imported modes"],
              ["Multi-model", "dashboard breakdowns"],
            ].map(([value, label]) => (
              <div key={value} className="rounded-[24px] border border-ember/10 bg-[#fff8f4] p-5 text-center">
                <p className="font-display text-4xl text-ember">{value}</p>
                <p className="mt-3 text-sm uppercase tracking-[0.18em] text-slate-600">{label}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 rounded-[28px] border border-slate-100 bg-slate-50 p-6">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Built For Iteration</p>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
              Axiom gives you datasets, prompts, runs, comparisons, judge reasoning, provider-backed generation, and imported-output evaluation in the same workflow.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/runs" className="btn-primary">
                Launch a Run
              </Link>
              <Link href="/compare" className="btn-secondary">
                Compare Runs
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
