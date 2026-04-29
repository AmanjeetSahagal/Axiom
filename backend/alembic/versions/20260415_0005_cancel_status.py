"""add cancel statuses

Revision ID: 20260415_0005
Revises: 20260415_0004
Create Date: 2026-04-29 18:20:00.000000
"""

from alembic import op


revision = "20260415_0005"
down_revision = "20260415_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE runstatus ADD VALUE IF NOT EXISTS 'canceled'")
    op.execute("ALTER TYPE optimizationjobstatus ADD VALUE IF NOT EXISTS 'canceled'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    pass
