"""add gemini 3 flash pricing

Revision ID: 7c9d2a81f4b6
Revises: 2f8a1d9c7b44
Create Date: 2026-06-10 00:00:00.000000
"""

from alembic import op


revision = "7c9d2a81f4b6"
down_revision = "2f8a1d9c7b44"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO model_pricing (model_key, display_name, input_price_per_1m, output_price_per_1m, active)
        VALUES ('gemini-3-flash-preview', 'Gemini 3.0 Flash', 0.500000, 3.000000, 1)
        ON DUPLICATE KEY UPDATE
            display_name = VALUES(display_name),
            input_price_per_1m = VALUES(input_price_per_1m),
            output_price_per_1m = VALUES(output_price_per_1m),
            active = VALUES(active)
        """
    )


def downgrade():
    op.execute("DELETE FROM model_pricing WHERE model_key = 'gemini-3-flash-preview'")
