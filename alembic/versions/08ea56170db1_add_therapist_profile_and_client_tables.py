"""add_therapist_profile_and_client_tables

Revision ID: 08ea56170db1
Revises: add_user_roles_20250609
Create Date: 2025-06-11 20:10:00.140904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '08ea56170db1'
down_revision: Union[str, None] = 'add_user_roles_20250609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # 建立 therapist_profiles 表
    op.create_table('therapist_profiles',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_number', sa.String(length=50), nullable=False),
        sa.Column('specialization', sa.String(length=200), nullable=True),
        sa.Column('bio', sa.String(length=1000), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('education', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('profile_id'),
        sa.UniqueConstraint('license_number'),
        sa.UniqueConstraint('user_id')
    )
    
    # 建立 therapist_clients 表
    op.create_table('therapist_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['therapist_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 建立索引以提升查詢效能
    op.create_index('ix_therapist_profiles_user_id', 'therapist_profiles', ['user_id'], unique=False)
    op.create_index('ix_therapist_clients_therapist_id', 'therapist_clients', ['therapist_id'], unique=False)
    op.create_index('ix_therapist_clients_client_id', 'therapist_clients', ['client_id'], unique=False)
    op.create_index('ix_therapist_clients_is_active', 'therapist_clients', ['is_active'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    # 刪除索引
    op.drop_index('ix_therapist_clients_is_active', table_name='therapist_clients')
    op.drop_index('ix_therapist_clients_client_id', table_name='therapist_clients')
    op.drop_index('ix_therapist_clients_therapist_id', table_name='therapist_clients')
    op.drop_index('ix_therapist_profiles_user_id', table_name='therapist_profiles')
    
    # 刪除表
    op.drop_table('therapist_clients')
    op.drop_table('therapist_profiles')
