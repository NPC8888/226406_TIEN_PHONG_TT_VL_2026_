"""use longtext for generated post content

Revision ID: 8a2d1c4e9f30
Revises: 4f6b9c2d1a77
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "8a2d1c4e9f30"
down_revision = "4f6b9c2d1a77"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "posts",
        "content",
        existing_type=sa.Text(),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "post_history",
        "content",
        existing_type=sa.Text(),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "post_history",
        "content",
        existing_type=mysql.LONGTEXT(),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "posts",
        "content",
        existing_type=mysql.LONGTEXT(),
        type_=sa.Text(),
        existing_nullable=True,
    )
