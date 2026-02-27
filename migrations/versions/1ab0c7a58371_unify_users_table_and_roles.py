"""unify_users_table_and_roles

Revision ID: 1ab0c7a58371
Revises: 01fe6da4040c
Create Date: 2026-02-25 15:02:06.782657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ab0c7a58371'
down_revision: Union[str, None] = '01fe6da4040c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop Judge0 & Coding Assistant Related Tables (from deleted models)
    op.drop_table('programming_test_results')
    op.drop_table('programming_testcases')
    op.drop_table('programming_submissions')
    op.drop_table('programming_language_configs')
    op.drop_table('coding_conversations')

    # 2. Create the unified 'users' table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='user', nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('student_id_number', sa.String(length=20), nullable=True),
        sa.Column('employee_id_number', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 3. Update 'courses' (professor_id -> owner_id)
    op.drop_constraint('courses_professor_id_fkey', 'courses', type_='foreignkey')
    op.alter_column('courses', 'professor_id', new_column_name='owner_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('courses_owner_id_fkey', 'courses', 'users', ['owner_id'], ['id'], ondelete='CASCADE')

    # 4. Update 'student_courses' (student_id -> user_id)
    op.drop_constraint('student_courses_student_id_fkey', 'student_courses', type_='foreignkey')
    op.alter_column('student_courses', 'student_id', new_column_name='user_id', existing_type=sa.UUID(), nullable=False)
    # Re-create PK for student_courses
    op.drop_constraint('student_courses_pkey', 'student_courses', type_='primary')
    op.create_primary_key('student_courses_pkey', 'student_courses', ['user_id', 'course_id'])
    op.create_foreign_key('student_courses_user_id_fkey', 'student_courses', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 5. Update 'activities' (student_id -> user_id)
    op.drop_constraint('activities_student_id_fkey', 'activities', type_='foreignkey')
    op.alter_column('activities', 'student_id', new_column_name='user_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('activities_user_id_fkey', 'activities', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 6. Update 'learning_paths' (student_id -> user_id)
    op.drop_constraint('learning_paths_student_id_fkey', 'learning_paths', type_='foreignkey')
    op.alter_column('learning_paths', 'student_id', new_column_name='user_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('learning_paths_user_id_fkey', 'learning_paths', 'users', ['user_id'], ['id'])

    # 7. Update 'student_exercises' (student_id -> user_id)
    op.drop_constraint('student_exercises_student_id_fkey', 'student_exercises', type_='foreignkey')
    op.alter_column('student_exercises', 'student_id', new_column_name='user_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('student_exercises_user_id_fkey', 'student_exercises', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 8. Update 'feedback' (collapse student_id + professor_id -> user_id)
    op.drop_constraint('feedback_student_id_fkey', 'feedback', type_='foreignkey')
    op.drop_constraint('feedback_professor_id_fkey', 'feedback', type_='foreignkey')
    op.drop_column('feedback', 'professor_id')
    op.alter_column('feedback', 'student_id', new_column_name='user_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key('feedback_user_id_fkey', 'feedback', 'users', ['user_id'], ['id'])

    # 9. Update 'user_logins'
    op.alter_column('user_logins', 'user_role', type_=sa.String(length=20), existing_type=sa.Enum('student', 'professor', 'admin', name='userrole'), postgresql_using='user_role::text')
    op.create_foreign_key('user_logins_user_id_fkey', 'user_logins', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 10. Drop old tables
    op.drop_table('student')
    op.drop_table('professors')
    op.drop_table('admins')


def downgrade() -> None:
    # Downgrade is not practical for this destructive migration
    pass
