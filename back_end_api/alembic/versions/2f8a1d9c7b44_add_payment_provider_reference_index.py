"""add payment provider reference index

Revision ID: 2f8a1d9c7b44
Revises: b4d2a8c6e901
Create Date: 2026-06-10 00:00:00.000000
"""

from alembic import op


revision = "2f8a1d9c7b44"
down_revision = "b4d2a8c6e901"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_payments_provider_payment_id",
        "payments",
        ["provider", "provider_payment_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_payments_provider_payment_id", table_name="payments")
