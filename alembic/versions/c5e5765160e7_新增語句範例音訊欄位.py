"""新增語句範例音訊欄位

Revision ID: c5e5765160e7
Revises: e9e9fafefbf9
Create Date: 2025-08-18 23:48:14.793634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e5765160e7'
down_revision: Union[str, None] = 'e9e9fafefbf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 新增語句範例音訊欄位
    op.add_column('sentences', sa.Column('example_audio_path', sa.String(), nullable=True))
    op.add_column('sentences', sa.Column('example_audio_duration', sa.Float(), nullable=True))
    op.add_column('sentences', sa.Column('example_file_size', sa.Integer(), nullable=True))
    op.add_column('sentences', sa.Column('example_content_type', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 移除語句範例音訊欄位
    op.drop_column('sentences', 'example_content_type')
    op.drop_column('sentences', 'example_file_size')
    op.drop_column('sentences', 'example_audio_duration')
    op.drop_column('sentences', 'example_audio_path')
