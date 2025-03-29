"""update schema 20250324

Revision ID: 8cda8491a5a0
Revises: 
Create Date: 2025-03-24 22:50:10.690652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8cda8491a5a0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admins',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('mscb', sa.String(length=255), nullable=True),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('fullname', sa.String(length=255), nullable=True),
    sa.Column('is_email_verified', sa.Boolean(), nullable=False),
    sa.Column('verification_code', sa.String(length=6), nullable=True),
    sa.Column('verification_code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('password_reset_code', sa.String(length=6), nullable=True),
    sa.Column('password_reset_code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('professors',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('mscb', sa.String(length=10), nullable=True),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('fullname', sa.String(length=255), nullable=True),
    sa.Column('is_email_verified', sa.Boolean(), nullable=False),
    sa.Column('verification_code', sa.String(length=6), nullable=True),
    sa.Column('verification_code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('password_reset_code', sa.String(length=6), nullable=True),
    sa.Column('password_reset_code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('student',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('mssv', sa.String(length=10), nullable=True),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('fullname', sa.String(length=255), nullable=True),
    sa.Column('is_email_verified', sa.Boolean(), nullable=False),
    sa.Column('verification_code', sa.String(length=6), nullable=True),
    sa.Column('verification_code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('password_reset_code', sa.String(length=6), nullable=True),
    sa.Column('password_reset_code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('user_logins',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('user_role', sa.Enum('student', 'professor', 'admin', name='userrole'), nullable=False),
    sa.Column('login_timestamp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('activities',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('type', sa.Enum('view_course', 'resume_activity', 'complete_lesson', 'complete_assignment', 'enroll_course', 'badge_earned', 'add_feedback', name='activitytype'), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('courses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('professor_id', sa.UUID(), nullable=False),
    sa.Column('learning_outcomes', postgresql.ARRAY(sa.Text()), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('new', 'in_progress', 'completed', name='statustype'), nullable=False),
    sa.Column('image_url', sa.String(), nullable=True),
    sa.Column('nCredit', sa.Integer(), nullable=True),
    sa.Column('nSemester', sa.Integer(), nullable=True),
    sa.Column('class_name', sa.String(), nullable=True),
    sa.Column('courseID', sa.String(), nullable=True),
    sa.Column('createdByAdminID', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['professor_id'], ['professors.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exercises',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('topic', sa.String(), nullable=True),
    sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('max_score', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('original', 'recommended', 'quiz', 'code', name='exercisetype'), nullable=False),
    sa.Column('time_open', sa.DateTime(), nullable=True),
    sa.Column('time_close', sa.DateTime(), nullable=True),
    sa.Column('time_limit', sa.Integer(), nullable=True),
    sa.Column('attempts_allowed', sa.Integer(), nullable=True),
    sa.Column('grading_method', sa.Enum('highest', 'average', 'latest', 'first', name='gradingmethodtype'), nullable=False),
    sa.Column('shuffle_questions', sa.Boolean(), nullable=True),
    sa.Column('shuffle_answers', sa.Boolean(), nullable=True),
    sa.Column('review_after_completion', sa.Boolean(), nullable=True),
    sa.Column('show_correct_answers', sa.Boolean(), nullable=True),
    sa.Column('penalty_per_attempt', sa.Float(), nullable=True),
    sa.Column('pass_mark', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feedback',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('category', sa.Enum('user_interface', 'performance', 'feature_request', 'bug_report', 'other', name='feedbackcategory'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('rate', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=True),
    sa.Column('professor_id', sa.UUID(), nullable=True),
    sa.Column('feedback_type', sa.Enum('system', 'course', name='feedbacktype'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'in_progress', 'resolved', name='feedbackstatustype'), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['professor_id'], ['professors.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('learning_paths',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('objective', sa.String(), nullable=True),
    sa.Column('progress', sa.Float(), nullable=False),
    sa.Column('version', sa.Integer(), sa.Identity(always=False), nullable=False),
    sa.Column('llm_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lessons',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('learning_outcomes', postgresql.ARRAY(sa.String()), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_courses',
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.Column('last_accessed', sa.DateTime(), nullable=True),
    sa.Column('completed_lessons', sa.Integer(), nullable=True),
    sa.Column('time_spent', sa.Interval(), nullable=True),
    sa.Column('assignments_done', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('student_id', 'course_id')
    )
    op.create_table('documents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('lesson_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('document_url', sa.Text(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('progress_upload', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recommend_lessons',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('learning_path_id', sa.UUID(), nullable=False),
    sa.Column('lesson_id', sa.UUID(), nullable=True),
    sa.Column('progress', sa.Integer(), nullable=False),
    sa.Column('recommended_content', sa.Text(), nullable=True),
    sa.Column('explain', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('new', 'in_progress', 'completed', name='statustype'), nullable=False),
    sa.Column('bookmark', sa.Boolean(), nullable=False),
    sa.Column('start_date', sa.Text(), nullable=True),
    sa.Column('end_date', sa.Text(), nullable=True),
    sa.Column('duration_notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_exercises',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('exercise_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('new', 'in_progress', 'completed', name='statustype'), nullable=False),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('time_spent', sa.Integer(), nullable=True),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.Column('answer', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_exercises_exercise_id'), 'student_exercises', ['exercise_id'], unique=False)
    op.create_index(op.f('ix_student_exercises_student_id'), 'student_exercises', ['student_id'], unique=False)
    op.create_table('extracted_texts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('document_id', sa.UUID(), nullable=False),
    sa.Column('extracted_content', sa.Text(), nullable=True),
    sa.Column('processing_status', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('modules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('recommend_lesson_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('objectives', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('last_accessed', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recommend_lesson_id'], ['recommend_lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recommendDocuments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('module_id', sa.UUID(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recommend_quizzes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('module_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('new', 'in_progress', 'completed', name='statustype'), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('max_score', sa.Float(), nullable=False),
    sa.Column('time_limit', sa.Integer(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recommend_quiz_questions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('quiz_id', sa.UUID(), nullable=False),
    sa.Column('question_text', sa.String(), nullable=False),
    sa.Column('question_type', sa.String(), nullable=False),
    sa.Column('options', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('correct_answer', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('difficulty', sa.Enum('easy', 'medium', 'hard', name='difficultylevel'), nullable=False),
    sa.Column('explanation', sa.String(), nullable=True),
    sa.Column('points', sa.Float(), nullable=True),
    sa.Column('user_choice', postgresql.ARRAY(sa.String()), nullable=True),
    sa.ForeignKeyConstraint(['quiz_id'], ['recommend_quizzes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recommend_quiz_questions')
    op.drop_table('recommend_quizzes')
    op.drop_table('recommendDocuments')
    op.drop_table('modules')
    op.drop_table('extracted_texts')
    op.drop_index(op.f('ix_student_exercises_student_id'), table_name='student_exercises')
    op.drop_index(op.f('ix_student_exercises_exercise_id'), table_name='student_exercises')
    op.drop_table('student_exercises')
    op.drop_table('recommend_lessons')
    op.drop_table('documents')
    op.drop_table('student_courses')
    op.drop_table('lessons')
    op.drop_table('learning_paths')
    op.drop_table('feedback')
    op.drop_table('exercises')
    op.drop_table('courses')
    op.drop_table('activities')
    op.drop_table('user_logins')
    op.drop_table('student')
    op.drop_table('professors')
    op.drop_table('admins')
    # ### end Alembic commands ###
