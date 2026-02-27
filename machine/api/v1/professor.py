"""
Owner (formerly "professor") routes — now uses the unified Users model.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_

from core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from core.response import Ok
from core.utils.file import generate_presigned_url
from core.utils.get_current_user import get_current_user
from machine.controllers import CoursesController, LessonsController, ExercisesController, DocumentsController, StudentCoursesController
from machine.models import Courses, Lessons, Documents, Exercises, StudentCourses, Users
from machine.providers import InternalProvider
from machine.schemas.requests import *
from machine.schemas.responses.courses import *

router = APIRouter(prefix="/professors", tags=["professors"])


@router.get("/courses", response_model=Ok[GetProfessorCoursesPaginatedResponse])
async def get_professor_courses(
    current_user: Users = Depends(get_current_user),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of items per page"),
    search_query: Optional[str] = Query(None, description="Search query to filter courses"),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="Only admins/professors can access course management.")
    
    where_conditions = [Courses.owner_id == current_user.id]

    if search_query:
        where_conditions.append(
            or_(
                Courses.name.ilike(f"%{search_query}%"),
                Courses.class_name.ilike(f"%{search_query}%"),
                Courses.courseID.ilike(f"%{search_query}%"),
            )
        )

    courses = await courses_controller.courses_repository.get_many(
        where_=where_conditions,
        order_={"desc": ["start_date"]},
        limit=page_size,
        skip=(page - 1) * page_size,
    )

    if not courses:
        return Ok(
            data=GetProfessorCoursesPaginatedResponse(content=[], currentPage=page, pageSize=page_size, totalRows=0, totalPages=0),
            message="No courses found.",
        )

    courses_response = []
    for course in courses:
        student_courses = await student_courses_controller.student_courses_repository.get_many(
            where_=[StudentCourses.course_id == course.id]
        )

        course_data = GetProfessorCoursesResponse(
            id=course.id,
            name=course.name,
            start_date=course.start_date,
            end_date=course.end_date,
            student_list=[],   # Populated separately if needed
            learning_outcomes=course.learning_outcomes or [],
            professor=ProfessorInformation(
                professor_id=current_user.id,
                professor_name=current_user.full_name or "",
                professor_email=current_user.email,
                professor_avatar=current_user.avatar_url or "",
            ),
            status=course.status,
            image_url=generate_presigned_url(course.image_url, expiration=604800) if course.image_url else "",
            nSemester=course.nSemester,
            nCredit=course.nCredit,
            courseID=course.courseID,
            class_name=str(course.class_name),
        )

        courses_response.append(course_data)

    total_rows = len(courses_response)
    total_pages = (total_rows + page_size - 1) // page_size
    paginated_content = courses_response[(page - 1) * page_size: page * page_size]

    response = GetProfessorCoursesPaginatedResponse(
        content=paginated_content,
        currentPage=page,
        pageSize=page_size,
        totalRows=total_rows,
        totalPages=total_pages,
    )
    return Ok(data=response, message="Successfully fetched professor courses.")


@router.get("/courses/{course_id}", response_model=Ok[GetCourseDetailProfessorResponse])
async def get_course_detail_for_professor(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    lessons_controller: LessonsController = Depends(InternalProvider().get_lessons_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
    document_controller: DocumentsController = Depends(InternalProvider().get_documents_controller),
):
    course = await courses_controller.courses_repository.first(where_=[Courses.id == course_id])
    if not course:
        raise NotFoundException(message="Course not found.")

    if current_user.role != "admin" or course.owner_id != current_user.id:
        raise ForbiddenException(message="You are not authorized to access this course details.")

    student_courses = await student_courses_controller.student_courses_repository.get_many(
        where_=[StudentCourses.course_id == course.id]
    )
    exercises_count = await exercises_controller.exercises_repository.count(where_=[Exercises.course_id == course.id])
    lessons = await lessons_controller.lessons_repository.get_many(where_=[Lessons.course_id == course_id])

    documents_count = 0
    for lesson in lessons:
        doc_count = await document_controller.documents_repository.count(where_=[Documents.lesson_id == lesson.id])
        documents_count += doc_count

    image_url = generate_presigned_url(course.image_url, expiration=604800) if course.image_url else ""

    course_detail = GetCourseDetailProfessorResponse(
        course_id=course.id,
        course_name=course.name,
        course_start_date=course.start_date.isoformat(),
        course_end_date=course.end_date.isoformat(),
        course_learning_outcomes=course.learning_outcomes or [],
        course_status=course.status,
        course_image_url=image_url,
        course_nCredit=course.nCredit,
        course_nSemester=course.nSemester,
        course_courseID=course.courseID,
        course_class_name=course.class_name,
        nStudents=len(student_courses),
        nLessons=len(lessons),
        nExercises=exercises_count,
        nDocuments=documents_count,
    )

    return Ok[GetCourseDetailProfessorResponse](data=course_detail)


@router.put("/courses/{course_id}/learning_outcomes", response_model=Ok[PutLearningOutcomesCoursesResponse])
async def change_learning_outcomes(
    course_id: UUID,
    body: PutLearningOutcomesCoursesRequest,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    course = await courses_controller.courses_repository.first(where_=[Courses.id == course_id])
    if not course:
        raise BadRequestException(message="Course not found.")

    if current_user.role != "admin" or current_user.id != course.owner_id:
        raise BadRequestException(message="You are not allowed to update this course's learning outcomes.")

    updated_course = await courses_controller.courses_repository.update(
        where_=[Courses.id == course_id],
        attributes={"learning_outcomes": body.learning_outcomes},
        commit=True,
    )

    if not updated_course:
        raise Exception("Failed to update course learning outcomes")

    return Ok(
        data=PutLearningOutcomesCoursesResponse(
            course_id=updated_course.id,
            learning_outcomes=updated_course.learning_outcomes,
        ),
        message="Successfully updated the course learning outcomes.",
    )
