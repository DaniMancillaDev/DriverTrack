"""Add SchedulerLock

Revision ID: fb62c19fbfff
Revises: 1277c19faf5a
Create Date: 2026-04-11 09:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb62c19fbfff'
down_revision: Union[str, None] = '1277c19faf5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> void:
    op.create_table('scheduler_locks',
    sa.Column('task_name', sa.String(), nullable=False),
    sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('task_name')
    )
    op.create_index(op.f('ix_scheduler_locks_task_name'), 'scheduler_locks', ['task_name'], unique=False)


def downgrade() -> void:
    op.drop_index(op.f('ix_scheduler_locks_task_name'), table_name='scheduler_locks')
    op.drop_table('scheduler_locks')
