"""drop_createdByAdminID_from_courses

Revision ID: 09e8c95966e5
Revises: 8cc0acfcc412
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "09e8c95966e5"
down_revision: Union[str, None] = "8cc0acfcc412"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("courses", "createdByAdminID")


def downgrade() -> None:
    op.add_column("courses", sa.Column("createdByAdminID", sa.VARCHAR(), nullable=True))
