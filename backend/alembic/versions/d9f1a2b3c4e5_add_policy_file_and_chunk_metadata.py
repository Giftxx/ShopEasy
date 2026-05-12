"""add policy file tracking and chunk metadata

Revision ID: d9f1a2b3c4e5
Revises: c1e2f3a4b5d6
Create Date: 2026-05-08 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'd9f1a2b3c4e5'
down_revision = 'c1e2f3a4b5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # policies: track original uploaded file
    op.add_column('policies', sa.Column('source_file_path', sa.String(500), nullable=True))
    op.add_column('policies', sa.Column('source_filename', sa.String(255), nullable=True))
    op.add_column('policies', sa.Column('file_size_bytes', sa.Integer(), nullable=True))

    # policy_chunks: structured metadata from intelligent extraction
    op.add_column('policy_chunks', sa.Column('heading', sa.String(255), nullable=True))
    op.add_column('policy_chunks', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('policy_chunks', sa.Column('page_number', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('policy_chunks', 'page_number')
    op.drop_column('policy_chunks', 'tags')
    op.drop_column('policy_chunks', 'heading')
    op.drop_column('policies', 'file_size_bytes')
    op.drop_column('policies', 'source_filename')
    op.drop_column('policies', 'source_file_path')
