"""add user provider keys

Revision ID: 20260415_0003
Revises: 20260415_0002
Create Date: 2026-04-15 01:30:00.000000
"""

from alembic import op


revision = "20260415_0003"
down_revision = "20260415_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'providertype') THEN
                CREATE TYPE providertype AS ENUM ('openai', 'anthropic', 'gemini');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_provider_keys (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            provider providertype NOT NULL,
            encrypted_api_key TEXT NOT NULL,
            key_hint VARCHAR(12) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_provider_keys_user_id ON user_provider_keys (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_provider_keys_provider ON user_provider_keys (provider)")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_user_provider_keys_user_provider
        ON user_provider_keys (user_id, provider)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_user_provider_keys_user_provider")
    op.execute("DROP INDEX IF EXISTS ix_user_provider_keys_provider")
    op.execute("DROP INDEX IF EXISTS ix_user_provider_keys_user_id")
    op.execute("DROP TABLE IF EXISTS user_provider_keys")
    op.execute("DROP TYPE IF EXISTS providertype")
