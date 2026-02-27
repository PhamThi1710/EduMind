from typing import List
from core.response import Ok
from machine.models import *
from datetime import datetime
import datetime
from machine.controllers import *
from machine.schemas.requests import *
from machine.providers import InternalProvider
from machine.schemas.responses.dashboard import *
from fastapi import APIRouter, Depends, HTTPException
from core.exceptions import NotFoundException, BadRequestException
from core.utils.get_current_user import get_current_user

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.get("/events", response_model=Ok[List[Events]])
async def get_all_events(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
):
    # Determine if user is an owner (professor/admin) or a student by checking both
    owner_courses = await courses_controller.courses_repository.get_many(
        where_=[Courses.owner_id == current_user.id]
    )

    courses = []

    if owner_courses:
        courses = owner_courses
    else:
        # User is a student enrolled in courses
        student_courses = await student_courses_controller.student_courses_repository.get_many(
            where_=[StudentCourses.user_id == current_user.id]
        )
        for sc in student_courses:
            course = await courses_controller.courses_repository.first(
                where_=[Courses.id == sc.course_id]
            )
            if course:
                courses.append(course)

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
            course_courseID=item["course"].courseID,
            course_nSemester=item["course"].nSemester,
        )
        for item in upcoming_exercises_list
    ]

    return Ok(data=events, message="Successfully fetched all upcoming exercise events.")