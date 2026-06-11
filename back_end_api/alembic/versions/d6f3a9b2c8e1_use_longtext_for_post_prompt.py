"""use longtext for post prompt metadata

Revision ID: d6f3a9b2c8e1
Revises: 7c9d2a81f4b6
Create Date: 2026-06-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "d6f3a9b2c8e1"
down_revision = "7c9d2a81f4b6"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "posts",
        "prompt",
        existing_type=sa.Text(),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "post_history",
        "prompt",
        existing_type=sa.Text(),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "post_history",
        "prompt",
        existing_type=mysql.LONGTEXT(),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "posts",
        "prompt",
        existing_type=mysql.LONGTEXT(),
        type_=sa.Text(),
        existing_nullable=True,
    )
