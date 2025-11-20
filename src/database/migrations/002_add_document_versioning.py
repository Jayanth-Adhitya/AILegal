"""Add document versioning support."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """Add document versioning tables and columns."""

    # Create document_versions table
    op.create_table(
        'document_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('content', sa.LargeBinary, nullable=False),  # Stores the DOCX blob
        sa.Column('content_hash', sa.String(64), nullable=False),  # SHA-256 hash
        sa.Column('edited_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('edit_summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),  # Store additional version metadata
    )

    # Add versioning columns to documents table
    op.add_column('documents', sa.Column('version_number', sa.Integer, server_default='1', nullable=False))
    op.add_column('documents', sa.Column('edited_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('documents', sa.Column('edited_at', sa.DateTime, nullable=True))
    op.add_column('documents', sa.Column('is_locked', sa.Boolean, server_default='false', nullable=False))
    op.add_column('documents', sa.Column('lock_reason', sa.String(50), nullable=True))  # e.g., 'signed', 'approved'

    # Create indexes for efficient querying
    op.create_index('idx_document_versions_document_id', 'document_versions', ['document_id'])
    op.create_index('idx_document_versions_version_number', 'document_versions', ['document_id', 'version_number'], unique=True)
    op.create_index('idx_document_versions_created_at', 'document_versions', ['created_at'])


def downgrade():
    """Remove document versioning support."""

    # Drop indexes
    op.drop_index('idx_document_versions_created_at', 'document_versions')
    op.drop_index('idx_document_versions_version_number', 'document_versions')
    op.drop_index('idx_document_versions_document_id', 'document_versions')

    # Drop document_versions table
    op.drop_table('document_versions')

    # Remove columns from documents table
    op.drop_column('documents', 'lock_reason')
    op.drop_column('documents', 'is_locked')
    op.drop_column('documents', 'edited_at')
    op.drop_column('documents', 'edited_by')
    op.drop_column('documents', 'version_number')