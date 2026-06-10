"""add outline json to posts and post_history

Revision ID: 0c7b9f7c3d21
Revises: e55e8dc3cf79
Create Date: 2026-04-09 11:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0c7b9f7c3d21"
down_revision = "e55e8dc3cf79"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("posts", sa.Column("outline_json", sa.JSON(), nullable=True))
    op.add_column("post_history", sa.Column("outline_json", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("post_history", "outline_json")
    op.drop_column("posts", "outline_json")
