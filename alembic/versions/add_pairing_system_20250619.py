"""add pairing system

Revision ID: add_pairing_system_20250619
Revises: add_user_roles_20250609
Create Date: 2025-06-19 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_pairing_system_20250619'
down_revision: Union[str, None] = 'add_user_roles_20250609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 創建配對請求表
    op.create_table('pairing_requests',
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['requester_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('request_id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_pairing_requests_token'), 'pairing_requests', ['token'], unique=False)

    # 創建治療師客戶關係表
    op.create_table('therapist_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paired_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['therapist_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('therapist_id', 'client_id', name='unique_therapist_client')
    )


def downgrade() -> None:
    # 刪除治療師客戶關係表
    op.drop_table('therapist_clients')
    
    # 刪除配對請求表
    op.drop_index(op.f('ix_pairing_requests_token'), table_name='pairing_requests')
    op.drop_table('pairing_requests')