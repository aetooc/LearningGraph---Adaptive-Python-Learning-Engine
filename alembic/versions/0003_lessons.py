"""Validated lessons and internal answer keys."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("learner_id", sa.Integer(), sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("examples", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lessons_learner_id", "lessons", ["learner_id"])
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("code_snippet", sa.Text(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_option_index", sa.Integer(), nullable=False),
        sa.Column("misconceptions", sa.JSON(), nullable=False),
        sa.UniqueConstraint("lesson_id", "position", name="unique_lesson_question_position"),
        sa.CheckConstraint("correct_option_index >= 0 AND correct_option_index <= 3", name="answer_index_range"),
        sa.CheckConstraint("position >= 0 AND position <= 2", name="question_position_range"),
    )


def downgrade() -> None:
    op.drop_table("questions")
    op.drop_index("ix_lessons_learner_id", table_name="lessons")
    op.drop_table("lessons")
