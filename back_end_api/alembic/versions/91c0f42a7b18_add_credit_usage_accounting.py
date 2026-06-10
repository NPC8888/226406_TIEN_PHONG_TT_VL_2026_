"""add credit and token usage accounting

Revision ID: 91c0f42a7b18
Revises: 8a2d1c4e9f30
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "91c0f42a7b18"
down_revision = "8a2d1c4e9f30"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("credit_balance", sa.Numeric(12, 6), nullable=False, server_default="1.000000"))
    op.add_column("users", sa.Column("total_input_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("total_output_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("total_credit_spent", sa.Numeric(12, 6), nullable=False, server_default="0.000000"))
    op.add_column("posts", sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("credit_cost", sa.Numeric(12, 6), nullable=False, server_default="0.000000"))
    op.add_column("post_history", sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("post_history", sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("post_history", sa.Column("credit_cost", sa.Numeric(12, 6), nullable=False, server_default="0.000000"))


def downgrade():
    op.drop_column("post_history", "credit_cost")
    op.drop_column("post_history", "output_tokens")
    op.drop_column("post_history", "input_tokens")
    op.drop_column("posts", "credit_cost")
    op.drop_column("posts", "output_tokens")
    op.drop_column("posts", "input_tokens")
    op.drop_column("users", "total_credit_spent")
    op.drop_column("users", "total_output_tokens")
    op.drop_column("users", "total_input_tokens")
    op.drop_column("users", "credit_balance")
