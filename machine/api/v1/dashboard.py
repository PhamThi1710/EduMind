from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends
from core.response import Ok
from core.utils.get_current_user import get_current_user
from machine.controllers import CoursesController, ExercisesController
from machine.models import Courses, Exercises, Users
from machine.providers import InternalProvider
from machine.schemas.responses.dashboard import *

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/recent-course", response_model=Ok[WelcomeMessageResponse])
async def get_recent_course(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    """Get the most recently updated course where the user is owner or member."""
    # Try owned courses first
    recent = await courses_controller.courses_repository.first(
        where_=[Courses.owner_id == current_user.id],
        order_={"desc": [{"field": "updated_at", "model_class": Courses}]},
    )
    if not recent:
        # Try member courses
        courses = await courses_controller.courses_repository.get_many(
            where_=[Courses.members.any(str(current_user.id))],
            order_={"desc": [{"field": "updated_at", "model_class": Courses}]},
            limit=1,
        )
        recent = courses[0] if courses else None

    if not recent:
        return Ok(data=None, message="No recent course found.")

    return Ok(
        data=WelcomeMessageResponse(course=recent.name, course_id=recent.id),
        message="Successfully fetched the recent course.",
    )


@router.get("/overview", response_model=Ok[GetDashboardResponse])
async def get_dashboard_overview(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
):
    """Dashboard overview for the current user."""
    owned = await courses_controller.courses_repository.get_many(
        where_=[Courses.owner_id == current_user.id]
    )
    member = await courses_controller.courses_repository.get_many(
        where_=[Courses.members.any(str(current_user.id))]
    )
    seen_ids = set()
    all_courses = []
    for c in owned + member:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            all_courses.append(c)

    n_courses = len(all_courses)
    n_exercises = 0
    upcoming_exercises_list = []
    current_time = datetime.utcnow()

    for course in all_courses:
        ex_count = await exercises_controller.exercises_repository.count(
            where_=[Exercises.course_id == course.id]
        )
        n_exercises += ex_count

        upcoming = await exercises_controller.exercises_repository.get_many(
            where_=[Exercises.course_id == course.id, Exercises.time_close > current_time],
        )
        for ex in upcoming:
            upcoming_exercises_list.append((ex, course))

    upcoming_exercises_list.sort(key=lambda x: x[0].time_close)
    upcoming_exercises_list = upcoming_exercises_list[:4]

    upcoming_events = [
        Events(
            exercise_id=ex.id,
            exercise_name=ex.name,
            exercise_time_open=ex.time_open.strftime("%H:%M %d/%m/%Y") if ex.time_open else "",
            exercise_time_close=ex.time_close.strftime("%H:%M %d/%m/%Y") if ex.time_close else "",
            exercise_type=ex.type,
            course_name=course.name,
            course_id=course.id,

        )
        for ex, course in upcoming_exercises_list
    ]

    return Ok(
        data=GetDashboardResponse(
            user_id=current_user.id,
            user_name=current_user.full_name or current_user.email,
            nCourses=n_courses,
            nExercises=n_exercises,
            upcoming_events=upcoming_events,
        ),
        message="Successfully fetched dashboard.",
    )
