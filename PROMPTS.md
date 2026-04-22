# PROMPTS

This file documents representative AI prompts that materially shaped the architecture, product direction, and implementation of Axiom. The prompts below are intentionally curated: they are longer-form, technically specific, and focused on consequential engineering decisions rather than minor UI iteration.

## 1. Cloudflare Copilot Architecture

```text
Fastest path:

keep the existing frontend and product concept
move one core AI flow onto Cloudflare Workers
use Workers AI or an external LLM behind a Worker
add a chat-style interface for “evaluate my prompt/model output”
use Durable Objects or D1/KV for session memory/state
frame the app as an AI evaluation copilot

Implement the shortest credible path that preserves the existing product while making the Cloudflare AI components real and user-facing.
```

Impact:
- introduced the Cloudflare Worker runtime under `cloudflare/copilot/`
- added Durable Object-backed session memory
- created the `/copilot` chat flow in the frontend
- established the assignment-aligned AI app surface

## 2. Imported Run Evaluation Mode

```text
The platform should not only evaluate generated Gemini outputs. It should also support imported model outputs from arbitrary providers.

Extend the dataset/import format to allow `model_output`.
Add an `imported run` mode in addition to `generated run`.
Skip generation entirely for imported runs.
Reuse the exact, semantic, and judge evaluators for imported outputs.
Surface run mode clearly in the UI so users can tell whether a run is provider-executed or imported.

Implement this end to end across backend schemas, persistence, worker behavior, and frontend flow.
```

Impact:
- added `generated` and `imported` run modes
- allowed datasets to carry `model_output`
- made Axiom provider-agnostic for evaluation, not just Gemini generation

## 3. Multi-Provider Model Strategy

```text
The UI should expose major well-known model families, not only Gemini.

Add a real model catalog in the run launcher with explicit provider grouping for OpenAI, Anthropic, Google, Meta/OSS, and Mistral.
Where generated execution is not yet supported, label those models honestly as import-only rather than pretending they run.
Where generated execution is supported, make the support level explicit.

Do not make the UI misleading. The user should understand the difference between:
- models available for generated runs
- models available only for imported evaluation
- providers that require configured credentials
```

Impact:
- expanded the run launcher beyond Gemini-only options
- clarified generated vs imported support
- set up the later provider-key flow

## 4. Provider Keys And Generated Multi-Provider Runs

```text
Support generated runs for multiple providers and make user-scoped credentials part of the product.

Add secure provider key storage for providers such as Gemini, OpenAI, and Anthropic.
Create a settings surface where users can save and remove provider keys.
Route generated model execution by model family so `gpt-*` uses OpenAI, `claude-*` uses Anthropic, and `gemini-*` uses Gemini.
Keep external provider support explicit in the run launcher rather than hidden in backend logic.

Implement the full path, including backend models, storage, API routes, frontend settings UI, and run-launch validation.
```

Impact:
- added provider key storage and settings UI
- enabled generated multi-provider execution paths
- strengthened the product narrative beyond a single-provider evaluator

## 5. Dashboard Usability And Decision Quality

```text
The dashboard should optimize for decision-making, not just aggregate display.

Averages across all models are only weakly useful in a multi-model evaluation product. Refactor the dashboard so the active slice is always obvious, and make the top metrics about the current view rather than only a blended global average.
Add clearer drilldowns by model, provider, run type, and category.
Make it obvious what scope the user is looking at, what metrics belong to that scope, and how that scope compares to the wider baseline.

Prioritize interpretability over decorative charts.
```

Impact:
- reworked the dashboard around `Current View` vs baseline
- improved drilldowns and scope clarity
- reduced misleading all-model aggregation as the primary story

## 6. Server-Side Scaling For Results And Datasets

```text
The current frontend paginates run results client-side, which will not scale. Move pagination and filtering to the backend.

Add real server-side pagination, search, category filtering, and result filtering for run results.
Add dataset row pagination on the backend as well.
Wire the frontend result inspector and dataset browser to those paginated APIs instead of loading everything into memory.
Preserve the richer row context in the UI while changing the transport shape.

Implement this in a way that supports large datasets and large evaluation runs without changing the product model.
```

Impact:
- added server-side pagination for run results and dataset rows
- moved large-result browsing off the client
- made the product more defensible for non-demo scale

## 7. Reviewer-Mode Submission Flow

```text
Optimize the project for evaluator experience during local review.

The assignment demo path should not require Firebase login before the first meaningful interaction.
Make Copilot the primary reviewer entry point.
Add a demo-mode flag that makes the Copilot route publicly accessible for local review while preserving the richer authenticated app flow outside that mode.
Tighten the README so a reviewer can get to a working AI interaction in as few commands as possible.

Prefer reducing setup friction over preserving every production-style gate in the demo path.
```

Impact:
- introduced demo mode for local review
- made `/copilot` the shortest meaningful demo path
- improved the reviewer setup story in the README

## 8. Copilot Prompt Behavior

```text
The Copilot should not answer every question with the same rigid template.

Patch the system prompt so it remains evaluation-focused and product-oriented, but stop forcing the same repeated structure on every response.
Use plain prose by default.
Only use bullets or sections when they actually improve clarity.
Vary the response shape depending on whether the user is asking for a verdict, a comparison, a failure analysis, test suggestions, or implementation advice.

Keep the outputs specific and practical rather than generic.
```

Impact:
- removed the repetitive 3-part response bias
- made Copilot answers feel more natural and task-sensitive

## Notes

- These prompts are representative, not exhaustive.
- Minor styling changes, bug-fix nudges, and terse one-line prompts are intentionally omitted.
- The included prompts were chosen because they influenced architecture, product positioning, evaluator behavior, deployability, or reviewer experience in a significant way.
