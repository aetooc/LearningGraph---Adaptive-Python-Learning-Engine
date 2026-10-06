"""One graded attempt per learner and stored question."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("learner_id", sa.Integer(), sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("selected_option_index", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("misconception_tag", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("learner_id", "question_id", name="unique_learner_question_attempt"),
        sa.CheckConstraint("selected_option_index >= 0 AND selected_option_index <= 3", name="selected_index_range"),
    )


def downgrade() -> None:
    op.drop_table("attempts")
