"""Controlled concepts and prerequisite edges."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_table(
        "prerequisites",
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), primary_key=True),
        sa.Column("prerequisite_id", sa.Integer(), sa.ForeignKey("concepts.id"), primary_key=True),
        sa.CheckConstraint("concept_id != prerequisite_id", name="no_self_edge"),
    )


def downgrade() -> None:
    op.drop_table("prerequisites")
    op.drop_table("concepts")
