"""baseline schema

Revision ID: 20260415_0001
Revises:
Create Date: 2026-04-15 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260415_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'runstatus') THEN
                CREATE TYPE runstatus AS ENUM ('pending', 'running', 'completed', 'failed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scoretype') THEN
                CREATE TYPE scoretype AS ENUM ('exact', 'semantic', 'judge');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255),
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS datasets (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users (id),
            name VARCHAR(255) NOT NULL,
            schema JSON NOT NULL DEFAULT '{}'::json,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_datasets_user_id ON datasets (user_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users (id),
            name VARCHAR(255) NOT NULL,
            system_prompt TEXT NOT NULL,
            user_template TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_templates_user_id ON prompt_templates (user_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS dataset_rows (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES datasets (id),
            input JSON NOT NULL DEFAULT '{}'::json,
            expected_output TEXT,
            category VARCHAR(120)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_dataset_rows_dataset_id ON dataset_rows (dataset_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS eval_runs (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES datasets (id),
            prompt_template_id UUID NOT NULL REFERENCES prompt_templates (id),
            model VARCHAR(120) NOT NULL,
            selected_evaluators JSON NOT NULL DEFAULT '["exact","semantic","judge"]'::json,
            status runstatus NOT NULL DEFAULT 'pending',
            avg_score DOUBLE PRECISION NOT NULL DEFAULT 0,
            total_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
            processed_rows INTEGER NOT NULL DEFAULT 0,
            total_rows INTEGER NOT NULL DEFAULT 0,
            failed_rows INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_eval_runs_dataset_id ON eval_runs (dataset_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_eval_runs_prompt_template_id ON eval_runs (prompt_template_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS eval_results (
            id UUID PRIMARY KEY,
            run_id UUID NOT NULL REFERENCES eval_runs (id),
            dataset_row_id UUID NOT NULL REFERENCES dataset_rows (id),
            rendered_prompt TEXT NOT NULL,
            output TEXT NOT NULL,
            latency_ms INTEGER NOT NULL DEFAULT 0,
            tokens INTEGER NOT NULL DEFAULT 0,
            error_message TEXT
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_eval_results_run_id ON eval_results (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_eval_results_dataset_row_id ON eval_results (dataset_row_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluator_scores (
            id UUID PRIMARY KEY,
            eval_result_id UUID NOT NULL REFERENCES eval_results (id),
            type scoretype NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            passed BOOLEAN NOT NULL DEFAULT FALSE,
            metadata JSON NOT NULL DEFAULT '{}'::json
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_evaluator_scores_eval_result_id ON evaluator_scores (eval_result_id)")
    op.execute(
        """
        ALTER TABLE eval_runs
        ADD COLUMN IF NOT EXISTS selected_evaluators JSON NOT NULL DEFAULT '["exact","semantic","judge"]'::json
        """
    )
    op.execute("ALTER TABLE eval_runs ADD COLUMN IF NOT EXISTS failed_rows INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE eval_runs ADD COLUMN IF NOT EXISTS last_error TEXT")
    op.execute("ALTER TABLE eval_results ADD COLUMN IF NOT EXISTS error_message TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE eval_results DROP COLUMN IF EXISTS error_message")
    op.execute("ALTER TABLE eval_runs DROP COLUMN IF EXISTS last_error")
    op.execute("ALTER TABLE eval_runs DROP COLUMN IF EXISTS failed_rows")
    op.execute("ALTER TABLE eval_runs DROP COLUMN IF EXISTS selected_evaluators")
    op.execute("DROP INDEX IF EXISTS ix_evaluator_scores_eval_result_id")
    op.execute("DROP TABLE IF EXISTS evaluator_scores")
    op.execute("DROP INDEX IF EXISTS ix_eval_results_dataset_row_id")
    op.execute("DROP INDEX IF EXISTS ix_eval_results_run_id")
    op.execute("DROP TABLE IF EXISTS eval_results")
    op.execute("DROP INDEX IF EXISTS ix_eval_runs_prompt_template_id")
    op.execute("DROP INDEX IF EXISTS ix_eval_runs_dataset_id")
    op.execute("DROP TABLE IF EXISTS eval_runs")
    op.execute("DROP INDEX IF EXISTS ix_dataset_rows_dataset_id")
    op.execute("DROP TABLE IF EXISTS dataset_rows")
    op.execute("DROP INDEX IF EXISTS ix_prompt_templates_user_id")
    op.execute("DROP TABLE IF EXISTS prompt_templates")
    op.execute("DROP INDEX IF EXISTS ix_datasets_user_id")
    op.execute("DROP TABLE IF EXISTS datasets")
    op.execute("DROP INDEX IF EXISTS ix_users_email")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TYPE IF EXISTS scoretype")
    op.execute("DROP TYPE IF EXISTS runstatus")
