from collections import defaultdict
from statistics import mean
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Dataset, DatasetRow, EvalResult, EvalRun, EvaluatorScore, PromptTemplate, RunStatus, ScoreType
from app.services.cost import estimate_cost
from app.services.evaluators import exact_match, llm_judge, semantic_similarity
from app.services.llm import call_model
from app.services.prompt_renderer import render_template


def create_run(db: Session, dataset_id: UUID, prompt_template_id: UUID, model: str) -> EvalRun:
    dataset = db.get(Dataset, dataset_id)
    prompt = db.get(PromptTemplate, prompt_template_id)
    if not dataset or not prompt:
        raise ValueError("Dataset or prompt template not found")

    run = EvalRun(
        dataset_id=dataset.id,
        prompt_template_id=prompt.id,
        model=model,
        status=RunStatus.pending,
        total_rows=len(dataset.rows),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def process_run(db: Session, run_id: UUID) -> EvalRun:
    run = db.execute(
        select(EvalRun)
        .options(
            joinedload(EvalRun.dataset).joinedload(Dataset.rows),
            joinedload(EvalRun.prompt_template),
        )
        .where(EvalRun.id == run_id)
    ).unique().scalar_one()
    run.status = RunStatus.running
    db.commit()

    score_totals: list[float] = []
    total_cost = 0.0

    for row in run.dataset.rows:
        rendered_user = render_template(run.prompt_template.user_template, row.input)
        output, latency_ms, prompt_tokens, output_tokens = call_model(
            run.prompt_template.system_prompt,
            rendered_user,
            run.model,
        )
        total_tokens = prompt_tokens + output_tokens
        result = EvalResult(
            run_id=run.id,
            dataset_row_id=row.id,
            rendered_prompt=rendered_user,
            output=output,
            latency_ms=latency_ms,
            tokens=total_tokens,
        )
        db.add(result)
        db.flush()

        exact = exact_match(output, row.expected_output)
        semantic = semantic_similarity(output, row.expected_output)
        judge = llm_judge(rendered_user, output, row.expected_output, run.model)
        evaluations = {
            ScoreType.exact: exact,
            ScoreType.semantic: semantic,
            ScoreType.judge: judge,
        }
        for score_type, evaluation in evaluations.items():
            db.add(
                EvaluatorScore(
                    eval_result_id=result.id,
                    type=score_type,
                    score=evaluation.score,
                    passed=evaluation.passed,
                    score_metadata=evaluation.metadata,
                )
            )

        row_avg = mean([exact.score, semantic.score, judge.score / 5.0])
        score_totals.append(row_avg)
        total_cost += estimate_cost(run.model, prompt_tokens, output_tokens)
        run.processed_rows += 1
        db.commit()

    run.avg_score = round(mean(score_totals), 4) if score_totals else 0.0
    run.total_cost = round(total_cost, 6)
    run.status = RunStatus.completed
    db.commit()
    db.refresh(run)
    return run


def compare_runs(db: Session, baseline_run_id: UUID, candidate_run_id: UUID) -> dict:
    baseline = db.execute(
        select(EvalRun)
        .options(
            joinedload(EvalRun.results).joinedload(EvalResult.dataset_row),
            joinedload(EvalRun.results).joinedload(EvalResult.scores),
        )
        .where(EvalRun.id == baseline_run_id)
    ).unique().scalar_one()
    candidate = db.execute(
        select(EvalRun)
        .options(
            joinedload(EvalRun.results).joinedload(EvalResult.dataset_row),
            joinedload(EvalRun.results).joinedload(EvalResult.scores),
        )
        .where(EvalRun.id == candidate_run_id)
    ).unique().scalar_one()

    def avg_latency(run: EvalRun) -> float:
        return mean([result.latency_ms for result in run.results]) if run.results else 0.0

    def category_scores(run: EvalRun) -> dict[str, list[float]]:
        categories: dict[str, list[float]] = defaultdict(list)
        for result in run.results:
            judge_scores = [score.score / 5.0 for score in result.scores if score.type == ScoreType.judge]
            if judge_scores:
                categories[result.dataset_row.category or "uncategorized"].append(judge_scores[0])
        return categories

    baseline_categories = category_scores(baseline)
    candidate_categories = category_scores(candidate)
    category_breakdown = {}
    for category in sorted(set(baseline_categories) | set(candidate_categories)):
        baseline_avg = mean(baseline_categories.get(category, [0.0]))
        candidate_avg = mean(candidate_categories.get(category, [0.0]))
        category_breakdown[category] = {
            "baseline": round(baseline_avg, 4),
            "candidate": round(candidate_avg, 4),
            "delta": round(candidate_avg - baseline_avg, 4),
        }

    return {
        "baseline_run_id": baseline.id,
        "candidate_run_id": candidate.id,
        "score_delta": round(candidate.avg_score - baseline.avg_score, 4),
        "latency_delta": round(avg_latency(candidate) - avg_latency(baseline), 2),
        "cost_delta": round(candidate.total_cost - baseline.total_cost, 6),
        "category_breakdown": category_breakdown,
    }
