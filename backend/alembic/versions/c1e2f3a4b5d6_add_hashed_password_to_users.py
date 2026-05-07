"""add hashed_password to users

Revision ID: c1e2f3a4b5d6
Revises: 4b5bb6c546ab
Create Date: 2026-05-07 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'c1e2f3a4b5d6'
down_revision = '4b5bb6c546ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'hashed_password')
