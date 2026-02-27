"""remove_ncredit_nsemester_classname_courseid_from_courses

Revision ID: 8cc0acfcc412
Revises: fe7578f5f70d
Create Date: 2026-02-27 02:48:41.376857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8cc0acfcc412"
down_revision: Union[str, None] = "fe7578f5f70d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("courses", "nCredit")
    op.drop_column("courses", "nSemester")
    op.drop_column("courses", "class_name")
    op.drop_column("courses", "courseID")


def downgrade() -> None:
    op.add_column("courses", sa.Column("courseID", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("courses", sa.Column("class_name", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("courses", sa.Column("nSemester", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column("courses", sa.Column("nCredit", sa.INTEGER(), autoincrement=False, nullable=True))
