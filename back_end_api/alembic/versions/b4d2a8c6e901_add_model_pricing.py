"""add model pricing

Revision ID: b4d2a8c6e901
Revises: 91c0f42a7b18
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b4d2a8c6e901"
down_revision = "91c0f42a7b18"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_pricing",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("input_price_per_1m", sa.Numeric(12, 6), nullable=False),
        sa.Column("output_price_per_1m", sa.Numeric(12, 6), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_key"),
    )
    op.execute(
        """
        INSERT INTO model_pricing (model_key, display_name, input_price_per_1m, output_price_per_1m, active)
        VALUES ('gemini-2.5-flash-lite', 'Gemini 2.5 Flash-Lite', 0.100000, 0.400000, 1)
        """
    )


def downgrade():
    op.drop_table("model_pricing")
