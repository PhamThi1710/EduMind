from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from core.exceptions import NotFoundException, BadRequestException
from core.response import Ok
from core.utils.get_current_user import get_current_user
from machine.controllers import ActivitiesController, CoursesController, LessonsController, StudentCoursesController, ExercisesController
from machine.models import Activities, Courses, Exercises, Lessons, StudentCourses, Users
from machine.providers import InternalProvider
from machine.schemas.requests import *
from machine.schemas.responses.dashboard import *

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/student-recent-course", response_model=Ok[WelcomeMessageResponse])
async def get_recent_course(
    current_user: Users = Depends(get_current_user),
    studentcourses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
):
    """Get the most recently accessed course by the current user."""
    recent_course = await studentcourses_controller.student_courses_repository.first(
        where_=[StudentCourses.user_id == current_user.id],
        order_={"desc": [{"field": "last_accessed", "model_class": StudentCourses}]},
        relations=[StudentCourses.course],
    )

    if not recent_course:
        return Ok(data=None, message="No recent course found.")

    last_accessed = recent_course.last_accessed
    if last_accessed is None:
        last_accessed = datetime.now()
    elif isinstance(last_accessed, str):
        try:
            last_accessed = datetime.fromisoformat(last_accessed)
        except ValueError:
            last_accessed = datetime.now()

    data = WelcomeMessageResponse(
        course=recent_course.course.name,
        course_id=recent_course.course.id,
        last_accessed=last_accessed.isoformat()
    )
    return Ok(data=data, message="Successfully fetched the recent course.")


@router.get("/student-activities", response_model=Ok[List[GetRecentActivitiesResponse]])
async def get_activities(
    current_user: Users = Depends(get_current_user),
    activities_controller: ActivitiesController = Depends(InternalProvider().get_activities_controller),
):
    recent_activities = await activities_controller.activities_repository.get_many(
        where_=[Activities.user_id == current_user.id],
        order_={"desc": [{"field": "timestamp", "model_class": Activities}]},
    )

    activities_data = [
        GetRecentActivitiesResponse(
            activity_id=activity.id,
            activity_description=activity.description,
            activity_type=str(activity.type),
            activity_date=activity.timestamp,
        )
        for activity in recent_activities
    ]
    return Ok(data=activities_data, message="Successfully fetched the recent activities.")


@router.post("/student-activities", response_model=Ok[bool])
async def add_activity(
    request: AddActivityRequest,
    current_user: Users = Depends(get_current_user),
    activities_controller: ActivitiesController = Depends(InternalProvider().get_activities_controller),
):
    try:
        if not request.type or not request.description:
            raise BadRequestException(message="Activity type and description are required.")

        activity = await activities_controller.activities_repository.create(
            attributes={
                "user_id": current_user.id,
                "type": request.type,
                "description": request.description,
                "timestamp": datetime.now(),
            },
            commit=True,
        )

        if not activity:
            raise NotFoundException(message="Failed to add activity.")

        return Ok(data=True, message="Successfully added the activity.")
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {e.errors()}")


@router.get("/professors", response_model=Ok[GetDashboardProfessorResponse])
async def get_professor_dashboard(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    lessons_controller: LessonsController = Depends(InternalProvider().get_lessons_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
):
    n_courses = await courses_controller.courses_repository.count(where_=[Courses.owner_id == current_user.id])
    courses = await courses_controller.courses_repository.get_many(where_=[Courses.owner_id == current_user.id])

    n_lessons = 0
    n_students_set = set()
    n_exercises = 0
    for course in courses:
        lessons_count = await lessons_controller.lessons_repository.count(where_=[Lessons.course_id == course.id])
        n_lessons += lessons_count

        student_courses = await student_courses_controller.student_courses_repository.get_many(
            where_=[StudentCourses.course_id == course.id]
        )
        user_ids = [sc.user_id for sc in student_courses]
        n_students_set.update(user_ids)

        exercises_count = await exercises_controller.exercises_repository.count(where_=[Exercises.course_id == course.id])
        n_exercises += exercises_count

    current_time = datetime.utcnow()
    upcoming_exercises_list = []
    for course in courses:
        upcoming_exercises = await exercises_controller.exercises_repository.get_many(
            where_=[
                Exercises.course_id == course.id,
                Exercises.time_close > current_time
            ],
        )
        upcoming_exercises_list.extend(upcoming_exercises)

    upcoming_exercises_list = sorted(upcoming_exercises_list, key=lambda ex: ex.time_close)[:4]
    upcoming_events = [
        Events(
            exercise_id=exercise.id,
            exercise_name=exercise.name,
            exercise_time_open=exercise.time_open.strftime("%H:%M %d/%m/%Y"),
            exercise_time_close=exercise.time_close.strftime("%H:%M %d/%m/%Y"),
            exercise_type=exercise.type,
            course_name=course.name,
            course_id=course.id,
            course_courseID=course.courseID,
            course_nSemester=course.nSemester
        )
        for exercise in upcoming_exercises_list
    ]

    response = GetDashboardProfessorResponse(
        professor_id=current_user.id,
        professor_name=current_user.full_name or current_user.email,
        nCourses=n_courses,
        nLessons=n_lessons,
        nStudents=len(n_students_set),
        nExercises=n_exercises,
        upcoming_events=upcoming_events
    )
    return Ok(data=response, message="Successfully fetched professor dashboard.")
