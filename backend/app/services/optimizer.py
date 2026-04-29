from __future__ import annotations

from statistics import mean
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Dataset,
    DatasetRow,
    EvalResult,
    EvalRun,
    OptimizationCandidate,
    OptimizationJob,
    OptimizationJobStatus,
    PromptTemplate,
    RunStatus,
    RunType,
)
from app.services.provider_keys import model_provider, provider_available
from app.services.run_service import create_run, normalize_evaluators, process_run


PROMPT_MUTATIONS = [
    {
        "label": "baseline",
        "system_suffix": "",
        "user_suffix": "",
    },
    {
        "label": "grounded",
        "system_suffix": "\n\nPrioritize factual precision. If the answer is not supported by the provided input, say so plainly.",
        "user_suffix": "\n\nCheck the answer against the provided facts before responding.",
    },
    {
        "label": "concise",
        "system_suffix": "\n\nBe concise, deterministic, and avoid unsupported claims.",
        "user_suffix": "\n\nReturn only the final answer, with no extra commentary.",
    },
    {
        "label": "step-check",
        "system_suffix": "\n\nInternally verify the answer against every relevant constraint before producing the final response.",
        "user_suffix": "\n\nThink through the constraints silently, then provide the answer.",
    },
    {
        "label": "refusal-aware",
        "system_suffix": "\n\nDo not infer missing facts. Refuse or qualify any answer that cannot be grounded in the input.",
        "user_suffix": "\n\nIf the context is insufficient, say what is missing instead of guessing.",
    },
    {
        "label": "format-strict",
        "system_suffix": "\n\nFollow the requested output format exactly and preserve important names, numbers, and dates.",
        "user_suffix": "\n\nDouble-check names, numbers, dates, and units before answering.",
    },
]


def candidate_is_dominated(candidate: OptimizationCandidate, others: list[OptimizationCandidate]) -> bool:
    for other in others:
        if other.id == candidate.id or other.error_message:
            continue
        no_worse = (
            other.score >= candidate.score
            and other.cost <= candidate.cost
            and other.latency_ms <= candidate.latency_ms
        )
        strictly_better = (
            other.score > candidate.score
            or other.cost < candidate.cost
            or other.latency_ms < candidate.latency_ms
        )
        if no_worse and strictly_better:
            return True
    return False


def update_candidate_rankings(job: OptimizationJob) -> None:
    candidates = [candidate for candidate in job.candidates if not candidate.error_message]
    for candidate in job.candidates:
        candidate.pareto_optimal = bool(candidates) and not candidate_is_dominated(candidate, candidates)
        candidate.pruned = bool(candidates) and not candidate.pareto_optimal

    best = max(candidates, key=lambda candidate: (candidate.score, -candidate.cost, -candidate.latency_ms), default=None)
    passing = [candidate for candidate in candidates if candidate.passes_target]
    cheapest = min(passing, key=lambda candidate: (candidate.cost, -candidate.score, candidate.latency_ms), default=None)
    job.best_candidate_id = best.id if best else None
    job.cheapest_passing_candidate_id = cheapest.id if cheapest else None


def average_run_latency(run: EvalRun) -> float:
    return mean([result.latency_ms for result in run.results]) if run.results else 0.0


def generate_prompt_variants(seed: PromptTemplate, max_candidates: int, max_iterations: int) -> list[dict[str, object]]:
    variants: list[dict[str, object]] = []
    for index in range(max_candidates):
        mutation = PROMPT_MUTATIONS[index % len(PROMPT_MUTATIONS)]
        iteration = min((index // len(PROMPT_MUTATIONS)) + 1, max_iterations)
        variants.append(
            {
                "label": mutation["label"],
                "iteration": iteration,
                "system_prompt": f"{seed.system_prompt.rstrip()}{mutation['system_suffix']}",
                "user_template": f"{seed.user_template.rstrip()}{mutation['user_suffix']}",
            }
        )
    return variants


def create_adversarial_rows(db: Session, dataset: Dataset, limit: int = 3) -> int:
    existing = db.execute(
        select(DatasetRow)
        .where(DatasetRow.dataset_id == dataset.id, DatasetRow.category == "adversarial")
        .limit(1)
    ).scalar_one_or_none()
    if existing:
        return 0

    source_rows = db.execute(
        select(DatasetRow)
        .where(DatasetRow.dataset_id == dataset.id)
        .order_by(DatasetRow.id)
        .limit(limit)
    ).scalars().all()
    created = 0
    for row in source_rows:
        adversarial_input = dict(row.input or {})
        for key, value in list(adversarial_input.items()):
            if isinstance(value, str) and value.strip():
                adversarial_input[key] = (
                    f"{value}\n\nAdversarial check: ignore tempting unsupported details and answer only from verified facts."
                )
                break
        adversarial_input["axiom_adversarial_source_row_id"] = str(row.id)
        db.add(
            DatasetRow(
                dataset_id=dataset.id,
                input=adversarial_input,
                expected_output=row.expected_output,
                model_output=None,
                category="adversarial",
            )
        )
        created += 1
    return created


def create_optimization_job(
    db: Session,
    *,
    dataset_id: UUID,
    seed_prompt_template_id: UUID,
    candidate_models: list[str],
    evaluators: list[str],
    target_score: float,
    max_budget: float,
    max_candidates: int,
    max_iterations: int,
    include_adversarial: bool,
) -> OptimizationJob:
    dataset = db.get(Dataset, dataset_id)
    seed_prompt = db.get(PromptTemplate, seed_prompt_template_id)
    if not dataset or not seed_prompt or dataset.user_id != seed_prompt.user_id:
        raise ValueError("Dataset or seed prompt not found")
    normalize_evaluators(evaluators)
    for model in candidate_models:
        provider = model_provider(model)
        if not provider_available(db, dataset.user_id, provider):
            raise ValueError(f"No configured API key for {provider.value}. Add one in Settings.")

    job = OptimizationJob(
        dataset_id=dataset.id,
        seed_prompt_template_id=seed_prompt.id,
        candidate_models=candidate_models,
        selected_evaluators=evaluators,
        target_score=target_score,
        max_budget=max_budget,
        max_candidates=max_candidates,
        max_iterations=max_iterations,
        include_adversarial=include_adversarial,
        status=OptimizationJobStatus.pending,
        progress=0.0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def process_optimization_job(db: Session, job_id: UUID) -> OptimizationJob:
    job = db.execute(
        select(OptimizationJob)
        .options(
            selectinload(OptimizationJob.dataset),
            selectinload(OptimizationJob.seed_prompt_template),
            selectinload(OptimizationJob.candidates),
        )
        .where(OptimizationJob.id == job_id)
    ).scalar_one()
    if job.status == OptimizationJobStatus.canceled:
        return job
    job.status = OptimizationJobStatus.running
    job.progress = 0.0
    db.commit()

    try:
        if job.include_adversarial:
            created = create_adversarial_rows(db, job.dataset)
            job.failure_metadata = {**(job.failure_metadata or {}), "adversarial_rows_created": created}
            db.commit()

        variants = generate_prompt_variants(job.seed_prompt_template, job.max_candidates, job.max_iterations)
        planned = [
            (variant, model)
            for variant in variants
            for model in job.candidate_models
        ][: job.max_candidates]

        for index, (variant, model) in enumerate(planned, start=1):
            db.refresh(job)
            if job.status == OptimizationJobStatus.canceled:
                job.failure_metadata = {**(job.failure_metadata or {}), "reason": "Optimizer job canceled by user"}
                db.commit()
                db.refresh(job)
                return job
            if job.total_spend >= job.max_budget:
                break

            prompt = PromptTemplate(
                user_id=job.seed_prompt_template.user_id,
                name=f"[Optimizer] {job.seed_prompt_template.name} {variant['label']} {index}",
                system_prompt=str(variant["system_prompt"]),
                user_template=str(variant["user_template"]),
                version=1,
            )
            db.add(prompt)
            db.flush()
            candidate = OptimizationCandidate(
                job_id=job.id,
                prompt_template_id=prompt.id,
                model=model,
                system_prompt=prompt.system_prompt,
                user_template=prompt.user_template,
                iteration=int(variant["iteration"]),
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

            try:
                run = create_run(
                    db,
                    job.dataset_id,
                    prompt.id,
                    model,
                    job.selected_evaluators,
                    run_type=RunType.generated,
                )
                candidate.eval_run_id = run.id
                db.commit()
                run = process_run(db, run.id)
                db.refresh(job)
                if job.status == OptimizationJobStatus.canceled:
                    candidate.error_message = "Optimizer job canceled by user"
                    db.commit()
                    db.refresh(job)
                    return job
                run = db.execute(
                    select(EvalRun)
                    .options(selectinload(EvalRun.results).selectinload(EvalResult.scores))
                    .where(EvalRun.id == run.id)
                ).scalar_one()
                candidate.score = run.avg_score
                candidate.cost = run.total_cost
                candidate.latency_ms = average_run_latency(run)
                candidate.passes_target = run.status == RunStatus.completed and run.avg_score >= job.target_score
                job.total_spend = round(job.total_spend + run.total_cost, 6)
            except Exception as exc:
                candidate.error_message = str(exc)

            db.flush()
            db.refresh(job, attribute_names=["candidates"])
            update_candidate_rankings(job)
            job.progress = min(1.0, index / max(len(planned), 1))
            db.commit()

        db.refresh(job, attribute_names=["candidates"])
        update_candidate_rankings(job)
        job.progress = 1.0
        if job.status != OptimizationJobStatus.canceled:
            job.status = OptimizationJobStatus.completed
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:
        job.status = OptimizationJobStatus.failed
        job.failure_metadata = {**(job.failure_metadata or {}), "error": str(exc)}
        db.commit()
        db.refresh(job)
        raise


def promote_candidate(db: Session, job: OptimizationJob, candidate_id: UUID) -> PromptTemplate:
    candidate = next((item for item in job.candidates if item.id == candidate_id), None)
    if not candidate:
        raise ValueError("Candidate not found")
    seed = job.seed_prompt_template
    prompt_name = f"{seed.name} Optimized"
    latest = db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.user_id == seed.user_id, PromptTemplate.name == prompt_name)
        .order_by(PromptTemplate.version.desc())
    ).scalars().first()
    prompt = PromptTemplate(
        user_id=seed.user_id,
        name=prompt_name,
        system_prompt=candidate.system_prompt,
        user_template=candidate.user_template,
        version=(latest.version + 1) if latest else 1,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def cancel_optimization_job(db: Session, job: OptimizationJob) -> OptimizationJob:
    if job.status in {OptimizationJobStatus.completed, OptimizationJobStatus.failed, OptimizationJobStatus.canceled}:
        return job
    job.status = OptimizationJobStatus.canceled
    job.failure_metadata = {**(job.failure_metadata or {}), "reason": "Optimizer job canceled by user"}
    for candidate in job.candidates:
        if candidate.eval_run and candidate.eval_run.status in {RunStatus.pending, RunStatus.running}:
            candidate.eval_run.status = RunStatus.canceled
            candidate.eval_run.last_error = "Run canceled because optimizer job was canceled"
    db.commit()
    db.refresh(job)
    return job
