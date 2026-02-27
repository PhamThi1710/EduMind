from typing import List
from core.response import Ok
from machine.models import Courses, Exercises, Users
import datetime
from machine.controllers import CoursesController, ExercisesController
from machine.providers import InternalProvider
from machine.schemas.responses.dashboard import *
from fastapi import APIRouter, Depends
from core.utils.get_current_user import get_current_user

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.get("/events", response_model=Ok[List[Events]])
async def get_all_events(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
):
    # Get courses where user is owner
    owner_courses = await courses_controller.courses_repository.get_many(
        where_=[Courses.owner_id == current_user.id]
    )

    # Get courses where user is a member
    member_courses = await courses_controller.courses_repository.get_many(
        where_=[Courses.members.any(str(current_user.id))]
    )

    # Combine both, avoiding duplicates
    course_ids = set()
    courses = []
    for c in (owner_courses or []) + (member_courses or []):
        if c.id not in course_ids:
            course_ids.add(c.id)
            courses.append(c)

    upcoming_exercises_list = []
    current_time = datetime.datetime.utcnow()

    for course in courses:
        upcoming_exercises = await exercises_controller.exercises_repository.get_many(
            where_=[Exercises.course_id == course.id]
        )
        for exercise in upcoming_exercises:
            upcoming_exercises_list.append({"exercise": exercise, "course": course})

    upcoming_exercises_list = sorted(upcoming_exercises_list, key=lambda item: item["exercise"].time_close)

    events = [
        Events(
            exercise_id=item["exercise"].id,
            exercise_name=item["exercise"].name,
            exercise_time_open=item["exercise"].time_open,
            exercise_time_close=item["exercise"].time_close,
            exercise_type=item["exercise"].type,
            course_name=item["course"].name,
            course_id=item["course"].id,

        )
        for item in upcoming_exercises_list
    ]

    return Ok(data=events, message="Successfully fetched all upcoming exercise events.")