"""add optimizer jobs

Revision ID: 20260415_0004
Revises: 20260415_0003
Create Date: 2026-04-29 00:00:00.000000
"""

from alembic import op


revision = "20260415_0004"
down_revision = "20260415_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'optimizationjobstatus') THEN
                CREATE TYPE optimizationjobstatus AS ENUM ('pending', 'running', 'completed', 'failed');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS optimization_jobs (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES datasets (id) ON DELETE CASCADE,
            seed_prompt_template_id UUID NOT NULL REFERENCES prompt_templates (id),
            candidate_models JSON NOT NULL DEFAULT '[]'::json,
            selected_evaluators JSON NOT NULL DEFAULT '["exact","semantic","judge"]'::json,
            target_score DOUBLE PRECISION NOT NULL DEFAULT 0.85,
            max_budget DOUBLE PRECISION NOT NULL DEFAULT 1.0,
            max_candidates INTEGER NOT NULL DEFAULT 12,
            max_iterations INTEGER NOT NULL DEFAULT 3,
            include_adversarial BOOLEAN NOT NULL DEFAULT TRUE,
            status optimizationjobstatus NOT NULL DEFAULT 'pending',
            progress DOUBLE PRECISION NOT NULL DEFAULT 0,
            total_spend DOUBLE PRECISION NOT NULL DEFAULT 0,
            best_candidate_id UUID,
            cheapest_passing_candidate_id UUID,
            failure_metadata JSON NOT NULL DEFAULT '{}'::json,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS optimization_candidates (
            id UUID PRIMARY KEY,
            job_id UUID NOT NULL REFERENCES optimization_jobs (id) ON DELETE CASCADE,
            prompt_template_id UUID NOT NULL REFERENCES prompt_templates (id),
            eval_run_id UUID REFERENCES eval_runs (id) ON DELETE SET NULL,
            model VARCHAR(120) NOT NULL,
            system_prompt TEXT NOT NULL,
            user_template TEXT NOT NULL,
            iteration INTEGER NOT NULL DEFAULT 1,
            score DOUBLE PRECISION NOT NULL DEFAULT 0,
            cost DOUBLE PRECISION NOT NULL DEFAULT 0,
            latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0,
            passes_target BOOLEAN NOT NULL DEFAULT FALSE,
            pareto_optimal BOOLEAN NOT NULL DEFAULT FALSE,
            pruned BOOLEAN NOT NULL DEFAULT FALSE,
            error_message TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        ALTER TABLE optimization_jobs
        ADD CONSTRAINT fk_optimization_jobs_best_candidate
        FOREIGN KEY (best_candidate_id) REFERENCES optimization_candidates (id)
        """
    )
    op.execute(
        """
        ALTER TABLE optimization_jobs
        ADD CONSTRAINT fk_optimization_jobs_cheapest_passing_candidate
        FOREIGN KEY (cheapest_passing_candidate_id) REFERENCES optimization_candidates (id)
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_optimization_jobs_dataset_id ON optimization_jobs (dataset_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_optimization_jobs_seed_prompt_template_id ON optimization_jobs (seed_prompt_template_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_optimization_candidates_job_id ON optimization_candidates (job_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_optimization_candidates_prompt_template_id ON optimization_candidates (prompt_template_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_optimization_candidates_eval_run_id ON optimization_candidates (eval_run_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_optimization_candidates_eval_run_id")
    op.execute("DROP INDEX IF EXISTS ix_optimization_candidates_prompt_template_id")
    op.execute("DROP INDEX IF EXISTS ix_optimization_candidates_job_id")
    op.execute("DROP INDEX IF EXISTS ix_optimization_jobs_seed_prompt_template_id")
    op.execute("DROP INDEX IF EXISTS ix_optimization_jobs_dataset_id")
    op.execute("ALTER TABLE optimization_jobs DROP CONSTRAINT IF EXISTS fk_optimization_jobs_cheapest_passing_candidate")
    op.execute("ALTER TABLE optimization_jobs DROP CONSTRAINT IF EXISTS fk_optimization_jobs_best_candidate")
    op.execute("DROP TABLE IF EXISTS optimization_candidates")
    op.execute("DROP TABLE IF EXISTS optimization_jobs")
    op.execute("DROP TYPE IF EXISTS optimizationjobstatus")
