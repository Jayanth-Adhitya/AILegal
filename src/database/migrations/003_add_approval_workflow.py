"""Add approval workflow support."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """Add approval workflow tables."""

    # Create approval_status enum
    approval_status_enum = sa.Enum(
        'pending', 'reviewing', 'approved', 'rejected',
        name='approval_status_enum'
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)

    # Create document_approvals table
    op.create_table(
        'document_approvals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('party_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('party_email', sa.String(255), nullable=False),
        sa.Column('party_name', sa.String(255), nullable=False),
        sa.Column('status', approval_status_enum, nullable=False, server_default='pending'),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create approval_history table for audit trail
    op.create_table(
        'approval_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('approval_id', sa.String(36), sa.ForeignKey('document_approvals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),  # 'created', 'reviewed', 'approved', 'rejected'
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('actor_email', sa.String(255), nullable=False),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Add approval-related columns to documents table
    op.add_column('documents', sa.Column('approval_status', sa.String(50), server_default='draft', nullable=False))
    op.add_column('documents', sa.Column('all_parties_approved', sa.Boolean, server_default='false', nullable=False))

    # Create indexes
    op.create_index('idx_document_approvals_document_id', 'document_approvals', ['document_id'])
    op.create_index('idx_document_approvals_party_id', 'document_approvals', ['party_id'])
    op.create_index('idx_document_approvals_status', 'document_approvals', ['status'])
    op.create_index('idx_approval_history_approval_id', 'approval_history', ['approval_id'])
    op.create_index('idx_approval_history_created_at', 'approval_history', ['created_at'])


def downgrade():
    """Remove approval workflow support."""

    # Drop indexes
    op.drop_index('idx_approval_history_created_at', 'approval_history')
    op.drop_index('idx_approval_history_approval_id', 'approval_history')
    op.drop_index('idx_document_approvals_status', 'document_approvals')
    op.drop_index('idx_document_approvals_party_id', 'document_approvals')
    op.drop_index('idx_document_approvals_document_id', 'document_approvals')

    # Remove columns from documents table
    op.drop_column('documents', 'all_parties_approved')
    op.drop_column('documents', 'approval_status')

    # Drop tables
    op.drop_table('approval_history')
    op.drop_table('document_approvals')

    # Drop enum
    approval_status_enum = sa.Enum(name='approval_status_enum')
    approval_status_enum.drop(op.get_bind(), checkfirst=True)