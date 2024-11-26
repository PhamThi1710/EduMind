"""add student_lessons and student-exercises tables

Revision ID: d65df0b4e017
Revises: 2838e7388a1f
Create Date: 2024-11-22 14:24:04.135629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd65df0b4e017'
down_revision: Union[str, None] = '2838e7388a1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('student_lessons',
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('lesson_id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.Column('bookmark', sa.Boolean(), nullable=False),
    sa.Column('status', postgresql.ENUM(name="statustype", create_type=False)),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('student_id', 'lesson_id', 'course_id')
    )
    op.create_table('student_exercises',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('exercise_id', sa.UUID(), nullable=False),
    sa.Column('status', postgresql.ENUM(name="statustype", create_type=False)),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('submission', sa.Text(), nullable=True),
    sa.Column('time_spent', sa.Integer(), nullable=True),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_exercises_exercise_id'), 'student_exercises', ['exercise_id'], unique=False)
    op.create_index(op.f('ix_student_exercises_student_id'), 'student_exercises', ['student_id'], unique=False)
    op.add_column('exercises', sa.Column('duration', sa.Integer(), nullable=True))
    op.drop_column('exercises', 'status')
    op.drop_column('lessons', 'bookmark')
    op.drop_column('lessons', 'status')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('status', postgresql.ENUM('new', 'in_progress', 'completed', name='statustype'), server_default=sa.text("'new'::statustype"), autoincrement=False, nullable=False))
    op.add_column('lessons', sa.Column('bookmark', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
    op.add_column('exercises', sa.Column('status', postgresql.ENUM('new', 'in_progress', 'completed', name='statustype'), server_default=sa.text("'new'::statustype"), autoincrement=False, nullable=False))
    op.drop_column('exercises', 'duration')
    op.drop_index(op.f('ix_student_exercises_student_id'), table_name='student_exercises')
    op.drop_index(op.f('ix_student_exercises_exercise_id'), table_name='student_exercises')
    op.drop_table('student_exercises')
    op.drop_table('student_lessons')
    # ### end Alembic commands ###