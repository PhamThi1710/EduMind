"""update schema

Revision ID: ce40bd7ecdb6
Revises: efe0f7a9370e
Create Date: 2025-04-11 09:02:35.303715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ce40bd7ecdb6'
down_revision: Union[str, None] = 'efe0f7a9370e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('activities', 'type',
               existing_type=postgresql.ENUM('view_course', 'resume_activity', 'complete_lesson', 'complete_assignment', 'enroll_course', 'badge_earned', 'add_feedback', name='activitytype'),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.drop_constraint('extracted_texts_document_id_fkey', 'extracted_texts', type_='foreignkey')
    op.create_foreign_key(None, 'extracted_texts', 'documents', ['document_id'], ['id'], ondelete='CASCADE')
    op.alter_column('feedback', 'feedback_type',
               existing_type=postgresql.ENUM('system', 'course', name='feedbacktype'),
               type_=sa.String(length=255),
               nullable=True)
    op.drop_column('lessons', 'order')

    # 2. Add the 'order' column again, this time correctly as an Identity column
    op.add_column('lessons', sa.Column('order', sa.Integer(), sa.Identity(start=1, increment=1, always=False), nullable=False))
    op.add_column('modules', sa.Column('progress', sa.Integer(), nullable=True))
    op.alter_column('programming_test_results', 'judge0_token',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=False)
    op.add_column('recommend_lessons', sa.Column('order', sa.Integer(), nullable=True))
    op.add_column('recommend_lessons', sa.Column('time_spent', sa.Interval(), nullable=True))
    op.add_column('student_courses', sa.Column('percentage_done', sa.Integer(), nullable=True))
    op.add_column('student_courses', sa.Column('issues_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.drop_column('student_courses', 'assignments_done')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('student_courses', sa.Column('assignments_done', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('student_courses', 'issues_summary')
    op.drop_column('student_courses', 'percentage_done')
    op.drop_column('recommend_lessons', 'time_spent')
    op.drop_column('recommend_lessons', 'order')
    op.alter_column('programming_test_results', 'judge0_token',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.drop_column('modules', 'progress')
    op.drop_column('lessons', 'order')
    op.add_column('lessons', sa.Column('order', sa.Integer(), nullable=False)) # Or its previous 
    op.alter_column('feedback', 'feedback_type',
               existing_type=sa.String(length=255),
               type_=postgresql.ENUM('system', 'course', name='feedbacktype'),
               nullable=False)
    op.drop_constraint(None, 'extracted_texts', type_='foreignkey')
    op.create_foreign_key('extracted_texts_document_id_fkey', 'extracted_texts', 'documents', ['document_id'], ['id'])
    op.alter_column('activities', 'type',
               existing_type=sa.String(length=255),
               type_=postgresql.ENUM('view_course', 'resume_activity', 'complete_lesson', 'complete_assignment', 'enroll_course', 'badge_earned', 'add_feedback', name='activitytype'),
               existing_nullable=False)
    # ### end Alembic commands ###
