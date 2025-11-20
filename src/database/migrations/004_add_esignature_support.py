"""Add e-signature support."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """Add e-signature tables."""

    # Create signature_type enum
    signature_type_enum = sa.Enum('drawn', 'typed', name='signature_type_enum')
    signature_type_enum.create(op.get_bind(), checkfirst=True)

    # Create signatures table
    op.create_table(
        'signatures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('signer_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),  # Null for external signers
        sa.Column('signer_email', sa.String(255), nullable=False),
        sa.Column('signer_name', sa.String(255), nullable=False),
        sa.Column('signature_data', sa.Text, nullable=False),  # Base64 encoded image or SVG
        sa.Column('signature_type', signature_type_enum, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text, nullable=False),
        sa.Column('signed_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('certificate_hash', sa.String(64), nullable=False),  # SHA-256 of document at signing time
        sa.Column('position_data', sa.JSON, nullable=True),  # Where to place signature on document
        sa.Column('is_valid', sa.Boolean, server_default='true', nullable=False),
    )

    # Create signing_sessions table for external signers
    op.create_table(
        'signing_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(500), unique=True, nullable=False),  # JWT token
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('completed', sa.Boolean, server_default='false', nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('access_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('last_accessed_at', sa.DateTime, nullable=True),
        sa.Column('verification_code', sa.String(6), nullable=True),
        sa.Column('verification_attempts', sa.Integer, server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Create signature_audit_log table
    op.create_table(
        'signature_audit_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('signature_id', sa.String(36), sa.ForeignKey('signatures.id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('signing_sessions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),  # 'session_created', 'link_accessed', 'code_sent', 'signed', etc.
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Add signature-related columns to documents table
    op.add_column('documents', sa.Column('signature_status', sa.String(50), server_default='not_required', nullable=False))
    op.add_column('documents', sa.Column('signatures_required', sa.Integer, server_default='0', nullable=False))
    op.add_column('documents', sa.Column('signatures_completed', sa.Integer, server_default='0', nullable=False))
    op.add_column('documents', sa.Column('fully_signed_at', sa.DateTime, nullable=True))

    # Create indexes
    op.create_index('idx_signatures_document_id', 'signatures', ['document_id'])
    op.create_index('idx_signatures_signer_id', 'signatures', ['signer_id'])
    op.create_index('idx_signatures_signer_email', 'signatures', ['signer_email'])
    op.create_index('idx_signing_sessions_document_id', 'signing_sessions', ['document_id'])
    op.create_index('idx_signing_sessions_token', 'signing_sessions', ['token'])
    op.create_index('idx_signing_sessions_expires_at', 'signing_sessions', ['expires_at'])
    op.create_index('idx_signature_audit_log_signature_id', 'signature_audit_log', ['signature_id'])
    op.create_index('idx_signature_audit_log_session_id', 'signature_audit_log', ['session_id'])


def downgrade():
    """Remove e-signature support."""

    # Drop indexes
    op.drop_index('idx_signature_audit_log_session_id', 'signature_audit_log')
    op.drop_index('idx_signature_audit_log_signature_id', 'signature_audit_log')
    op.drop_index('idx_signing_sessions_expires_at', 'signing_sessions')
    op.drop_index('idx_signing_sessions_token', 'signing_sessions')
    op.drop_index('idx_signing_sessions_document_id', 'signing_sessions')
    op.drop_index('idx_signatures_signer_email', 'signatures')
    op.drop_index('idx_signatures_signer_id', 'signatures')
    op.drop_index('idx_signatures_document_id', 'signatures')

    # Remove columns from documents table
    op.drop_column('documents', 'fully_signed_at')
    op.drop_column('documents', 'signatures_completed')
    op.drop_column('documents', 'signatures_required')
    op.drop_column('documents', 'signature_status')

    # Drop tables
    op.drop_table('signature_audit_log')
    op.drop_table('signing_sessions')
    op.drop_table('signatures')

    # Drop enum
    signature_type_enum = sa.Enum(name='signature_type_enum')
    signature_type_enum.drop(op.get_bind(), checkfirst=True)