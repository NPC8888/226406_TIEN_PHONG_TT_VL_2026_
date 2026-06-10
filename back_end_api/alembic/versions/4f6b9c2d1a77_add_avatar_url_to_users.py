"""add avatar_url to users

Revision ID: 4f6b9c2d1a77
Revises: 0c7b9f7c3d21
Create Date: 2026-05-08 15:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "4f6b9c2d1a77"
down_revision = "0c7b9f7c3d21"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("avatar_url", sa.String(length=1024), nullable=True))


def downgrade():
    op.drop_column("users", "avatar_url")
