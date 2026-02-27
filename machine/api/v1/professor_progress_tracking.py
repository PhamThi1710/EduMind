from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from core.exceptions import BadRequestException, NotFoundException
from core.response import Ok
from core.utils.get_current_user import get_current_user
from machine.controllers import (
    CoursesController,
    ExercisesController,
    LearningPathsController,
    LessonsController,
    RecommendLessonsController,
    StudentCoursesController,
    StudentExercisesController,
)
from machine.models import Courses, Exercises, Lessons, RecommendLessons, StudentCourses, StudentExercises, Users
from machine.providers import InternalProvider
from machine.schemas.responses.progress_tracking import *

router = APIRouter(prefix="/professor_progress_tracking", tags=["professor_progress_tracking"])


@router.get("/courses/{course_id}/grades", response_model=Ok[GetCourseGradesResponse])
async def get_grades(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    student_exercises_controller: StudentExercisesController = Depends(InternalProvider().get_studentexercises_controller),
    recommend_lessons_controller: RecommendLessonsController = Depends(InternalProvider().get_recommendlessons_controller),
    lessons_controller: LessonsController = Depends(InternalProvider().get_lessons_controller),
    learning_paths_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    """Get the grades for a course (requires course ownership)."""
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == course_id],
        relations=[Courses.student_courses, Courses.exercises],
    )
    if not course:
        raise NotFoundException(message="No courses found.")
    if course.owner_id != current_user.id:
        raise BadRequestException(message="You are not authorized to access the grades for this course.")

    student_courses = await student_courses_controller.student_courses_repository.get_many(
        where_=[StudentCourses.course_id == course_id]
    )
    if not student_courses:
        raise NotFoundException(message="No students found in the course.")

    students_list = []
    for student_course in student_courses:
        user = await user_controller.user_repository.first(where_=[Users.id == student_course.user_id])
        if not user:
            continue
        student_id = user.id
        student_name = user.full_name or ""
        student_email = user.email
        student_mssv = user.student_id_number or ""

        learning_path_progress = await learning_paths_controller.get_learning_path(
            user_id=student_id, course_id=course_id
        )
        learning_path = None
        if learning_path_progress:
            recommend_lessons = await recommend_lessons_controller.recommend_lessons_repository.get_many(
                where_=[RecommendLessons.learning_path_id == learning_path_progress.id]
            )
            lessons = []
            if recommend_lessons:
                for rec_lesson in recommend_lessons:
                    lesson = await lessons_controller.lessons_repository.first(
                        where_=[Lessons.id == rec_lesson.lesson_id]
                    )
                    if lesson:
                        lessons.append(LessonInLearningPath(
                            lesson_id=rec_lesson.id,
                            lesson_name=lesson.title,
                            description=lesson.description,
                            progress=rec_lesson.progress,
                        ))
            learning_path = LearningPathProgressInCourse(
                learning_path_id=learning_path_progress.id,
                progress=learning_path_progress.progress,
                objective=learning_path_progress.objective,
                lessons=lessons,
            )

        exercises = await exercises_controller.exercises_repository.get_many(
            where_=[Exercises.course_id == course_id],
        )
        exercise_student = []
        for exercise in exercises:
            student_exercise = await student_exercises_controller.student_exercises_repository.first(
                where_=[StudentExercises.exercise_id == exercise.id, StudentExercises.user_id == student_id],
            )
            score = student_exercise.score if student_exercise else 0
            exercise_student.append(ExeriseStudentProgressInCourse(
                exercise_id=exercise.id,
                exercise_name=exercise.name,
                score=score,
            ))

        total_score = sum(e.score for e in exercise_student)
        average_score = total_score / len(exercise_student) if exercise_student else 0.0

        students_list.append(StudentProgressInCourse(
            student_id=student_id,
            student_name=student_name,
            student_email=student_email,
            student_mssv=student_mssv,
            exercises=exercise_student,
            learning_path=learning_path,
            average_score=average_score,
        ))

    return Ok(data=GetCourseGradesResponse(students_list=students_list), message="Successfully fetched the grades course.")


@router.get("/courses/{course_id}/exercises/{exercise_id}/grades", response_model=Ok[GetExerciseGradesResponse])
async def get_exercise_grades(
    course_id: UUID,
    exercise_id: UUID,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    student_exercises_controller: StudentExercisesController = Depends(InternalProvider().get_studentexercises_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    """Get per-student exercise grades for a course (requires course ownership)."""
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == course_id],
        relations=[Courses.student_courses, Courses.exercises],
    )
    if not course:
        raise NotFoundException(message="No courses found.")
    if course.owner_id != current_user.id:
        raise BadRequestException(message="You are not authorized to access the grades for this course.")

    student_courses = await student_courses_controller.student_courses_repository.get_many(
        where_=[StudentCourses.course_id == course_id]
    )
    if not student_courses:
        raise NotFoundException(message="No students found in the course.")

    exercise = await exercises_controller.exercises_repository.first(where_=[Exercises.id == exercise_id])
    students_list = []
    for student_course in student_courses:
        user = await user_controller.user_repository.first(where_=[Users.id == student_course.user_id])
        if not user:
            continue
        student_id = user.id
        student_exercise = await student_exercises_controller.student_exercises_repository.first(
            where_=[StudentExercises.exercise_id == exercise.id, StudentExercises.user_id == student_id],
        )
        if not student_exercise:
            score, completion_date, question_answers = 0, None, []
        else:
            score = student_exercise.score
            completion_date = student_exercise.completion_date
            question_answers = [
                AnswerQuizExercise(
                    question=answer.get('question', '') if isinstance(answer, dict) else '',
                    answers=answer.get('answers', []) if isinstance(answer, dict) else []
                )
                for answer in (student_exercise.answer or [])
            ]

        students_list.append(StudentProgressInExercise(
            student_id=student_id,
            student_name=user.full_name or "",
            student_email=user.email,
            student_mssv=user.student_id_number or "",
            score=score,
            date=completion_date,
            question_answers=question_answers,
        ))

    return Ok(data=GetExerciseGradesResponse(students_list=students_list, type='quiz'), message="Successfully fetched the grades exercise.")
