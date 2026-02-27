"""remove_lessons_studentcourses_activities_studentexercises

Revision ID: fe7578f5f70d
Revises: 1ab0c7a58371
Create Date: 2026-02-27 02:31:46.185596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fe7578f5f70d"
down_revision: Union[str, None] = "1ab0c7a58371"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop FK constraints that reference lessons table FIRST
    op.drop_constraint("documents_lesson_id_fkey", "documents", type_="foreignkey")
    op.drop_constraint("recommend_lessons_lesson_id_fkey", "recommend_lessons", type_="foreignkey")

    # 2. Now safe to drop the tables
    op.drop_table("lessons")
    op.drop_table("activities")
    op.drop_index("ix_student_exercises_exercise_id", table_name="student_exercises")
    op.drop_index("ix_student_exercises_student_id", table_name="student_exercises")
    op.drop_table("student_exercises")
    op.drop_table("student_courses")

    # 3. Update documents: replace lesson_id with course_id
    op.add_column("documents", sa.Column("course_id", sa.UUID(), nullable=True))
    op.execute("UPDATE documents SET course_id = course_id WHERE course_id IS NOT NULL")
    op.drop_column("documents", "lesson_id")
    op.create_foreign_key("documents_course_id_fkey", "documents", "courses", ["course_id"], ["id"], ondelete="CASCADE")

    # 4. Update courses: add members array and description
    op.add_column("courses", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("members", postgresql.ARRAY(sa.UUID()), server_default="{}", nullable=False))

    # 5. Update recommend_lessons: add title/description, drop lesson_id
    op.add_column("recommend_lessons", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("recommend_lessons", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("recommend_lessons", sa.Column("learning_outcomes", postgresql.ARRAY(sa.String()), nullable=True))
    op.drop_column("recommend_lessons", "lesson_id")


def downgrade() -> None:
    op.add_column("recommend_lessons", sa.Column("lesson_id", sa.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key("recommend_lessons_lesson_id_fkey", "recommend_lessons", "lessons", ["lesson_id"], ["id"], ondelete="CASCADE")
    op.drop_column("recommend_lessons", "learning_outcomes")
    op.drop_column("recommend_lessons", "description")
    op.drop_column("recommend_lessons", "title")
    op.add_column("documents", sa.Column("lesson_id", sa.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint("documents_course_id_fkey", "documents", type_="foreignkey")
    op.create_foreign_key("documents_lesson_id_fkey", "documents", "lessons", ["lesson_id"], ["id"], ondelete="CASCADE")
    op.drop_column("documents", "course_id")
    op.drop_column("courses", "members")
    op.drop_column("courses", "description")
    op.create_table("student_courses",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "course_id", name="student_courses_pkey")
    )
    op.create_table("student_exercises",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("exercise_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="student_exercises_pkey")
    )
    op.create_table("activities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", sa.VARCHAR(length=255), nullable=False),
        sa.Column("description", sa.VARCHAR(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name="activities_pkey")
    )
    op.create_table("lessons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.VARCHAR(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="lessons_pkey")
    )
