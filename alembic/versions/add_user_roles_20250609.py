"""add user roles

Revision ID: add_user_roles_20250609
Revises: fca1308887e6
Create Date: 2025-06-09 17:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_user_roles_20250609'
down_revision: Union[str, None] = 'fca1308887e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 如果角色欄位不存在，則新增它
    try:
        op.add_column('users', sa.Column('role', sa.String(), nullable=True))
        op.execute("UPDATE users SET role = 'client' WHERE role IS NULL")
        op.alter_column('users', 'role', nullable=False)

    except Exception:
        # 如果欄位已存在，則跳過
        pass


def downgrade() -> None:
    # 移除角色欄位
    try:
        op.drop_column('users', 'role')
    except Exception:
        # 如果欄位不存在，則跳過
        pass
