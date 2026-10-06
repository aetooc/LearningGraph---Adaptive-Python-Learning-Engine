"""Learners and per-concept progress."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("goal", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "learner_mastery",
        sa.Column("learner_id", sa.Integer(), sa.ForeignKey("learners.id"), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), primary_key=True),
        sa.Column("mastery_score", sa.Numeric(3, 2), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("mastery_score >= 0 AND mastery_score <= 1", name="mastery_range"),
        sa.CheckConstraint("attempts >= 0", name="nonnegative_attempts"),
    )


def downgrade() -> None:
    op.drop_table("learner_mastery")
    op.drop_table("learners")
