"""Add password reset token support."""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add password_reset_tokens table."""

    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('used_at', sa.DateTime, nullable=True),
        sa.Column('request_count', sa.Integer, server_default='1', nullable=False),
        sa.Column('window_start', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for efficient lookups
    op.create_index('idx_password_reset_tokens_hash', 'password_reset_tokens', ['token_hash'])
    op.create_index('idx_password_reset_tokens_user_expires', 'password_reset_tokens', ['user_id', 'expires_at'])
    op.create_index('idx_password_reset_tokens_expires', 'password_reset_tokens', ['expires_at'])


def downgrade():
    """Remove password_reset_tokens table."""

    # Drop indexes
    op.drop_index('idx_password_reset_tokens_expires', 'password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_user_expires', 'password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_hash', 'password_reset_tokens')

    # Drop table
    op.drop_table('password_reset_tokens')
