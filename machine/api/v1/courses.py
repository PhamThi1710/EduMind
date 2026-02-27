import math
import os
from datetime import date, datetime
from typing import List, Literal, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import and_

from core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from core.response import Ok
from core.utils.file import generate_presigned_url, update_course_image_s3
from core.utils.get_current_user import get_current_user
from machine.controllers import (
    CoursesController,
    DocumentsController,
    ExercisesController,
    LearningPathsController,
    LessonsController,
    StudentCoursesController,
)
from machine.models import (
    Courses,
    Documents,
    Exercises,
    LearningPaths,
    Lessons,
    StudentCourses,
    Users,
)
from machine.models import *  # keep for schema/response model symbols
from machine.providers import InternalProvider
from machine.schemas.requests import *
from machine.schemas.responses.courses import *
from machine.schemas.responses.exercise import *
from machine.schemas.responses.learning_path import LearningPathDTO, RecommendedLessonDTO
from machine.schemas.responses.progress_tracking import GetCoursesListResponse
from utils.data import availableCourses

router = APIRouter(prefix="/courses", tags=["courses"])
# Fixed routes should come first


@router.get("/", response_model=Ok[List[GetCoursesListResponse]])
async def get_courses(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    """Get the list of courses for the authenticated user (owner for admin role)."""
    courses = await courses_controller.courses_repository.get_many(
        where_=[Courses.owner_id == current_user.id],
        order_={"desc": ["start_date"]},
    )

    if not courses:
        raise NotFoundException(message="No courses found.")

    course_list = [
        GetCoursesListResponse(
            course_id=course.id,
            course_name=course.name,
            course_courseID=course.courseID,
            course_nSemester=course.nSemester,
            course_class_name=course.class_name,
            course_start_date=course.start_date,
            course_end_date=course.end_date,
        )
        for course in courses
    ]
    return Ok(data=course_list, message="Successfully fetched the course list.")


@router.get("/student", response_model=Ok[GetCoursesPaginatedResponse])
async def get_student_courses(
    current_user: Users = Depends(get_current_user),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of items per page"),
    search_query: Optional[str] = Query(None, description="Search query to filter courses"),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    learning_paths_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    where_conditions = (
        [StudentCourses.user_id == current_user.id, Courses.name.ilike(f"%{search_query}%")]
        if search_query
        else [StudentCourses.user_id == current_user.id]
    )
    select_fields = [
        Courses.id.label("id"),
        Courses.name.label("name"),
        Courses.start_date.label("start_date"),
        Courses.end_date.label("end_date"),
        Courses.learning_outcomes.label("learning_outcomes"),
        Courses.status.label("status"),
        Courses.image_url.label("image_url"),
        Courses.nCredit.label("nCredit"),
        Courses.nSemester.label("nSemester"),
        Courses.courseID.label("courseID"),
        Courses.class_name.label("class_name"),
        StudentCourses.last_accessed.label("last_accessed"),
        StudentCourses.percentage_done.label("percentage_complete"),
    ]
    join_conditions = {"courses": {"type": "left", "alias": "courses_alias"}}

    courses = await student_courses_controller.student_courses_repository._get_many(
        where_=where_conditions,
        fields=select_fields,
        join_=join_conditions,
        order_={"asc": ["last_accessed"]},
        limit=page_size,
        skip=(page - 1) * page_size,
    )

    if not courses:
        return Ok(
            data={"content": [], "pageSize": page_size, "currentPage": page, "totalRows": 0, "totalPages": 0},
            message="No courses found.",
        )

    total_page = math.ceil(len(courses) / page_size)
    content = []
    for course in courses:
        learning_path = await learning_paths_controller.get_learning_path(
            user_id=current_user.id, course_id=course.id
        )
        course_response = GetCoursesResponse(
            id=course.id,
            name=course.name,
            start_date=str(course.start_date),
            end_date=str(course.end_date),
            learning_outcomes=course.learning_outcomes or [],
            status=course.status,
            image_url=generate_presigned_url(course.image_url, expiration=604800) if course.image_url else "",
            last_accessed=str(course.last_accessed),
            nCredit=course.nCredit,
            nSemester=course.nSemester,
            courseID=course.courseID,
            class_name=str(course.class_name),
            percentage_complete=str(learning_path.progress) if learning_path else "0",
        )
        content.append(course_response)

    return Ok(
        data={"content": content, "pageSize": page_size, "currentPage": page, "totalRows": len(courses), "totalPages": total_page},
        message="Successfully fetched the courses.",
    )


@router.get("/count/", response_model=Ok[int])
async def count_courses(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")
    count = await courses_controller.courses_repository.count(where_=None)
    return Ok(data=count, message="Successfully fetched the count of courses.")


@router.get("/available", description="Get all available courses of HCMUT")
async def get_available_courses(
    current_user: Users = Depends(get_current_user),
):
    return Ok(data=availableCourses, message="Successfully fetched the available courses.")


@router.post("/add-students", response_model=Ok[AddStudentsToCourseResponse])
async def add_students_to_course(
    request: AddStudentsToCourseRequest,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    if current_user.role not in ("admin",):
        raise ForbiddenException(message="You are not allowed to add students to courses.")

    if not request.course_id:
        raise BadRequestException(message="Course ID is required.")
    if not request.student_ids or len(request.student_ids) == 0:
        raise BadRequestException(message="At least one student ID is required.")

    course = await courses_controller.courses_repository.first(where_=[Courses.id == request.course_id])
    if not course:
        raise NotFoundException(message=f"Course with ID {request.course_id} not found.")

    # Look up users by student_id_number (replaces mssv)
    users = await user_controller.user_repository._get_many(
        where_=[Users.student_id_number.in_(request.student_ids)],
        fields=[Users.id, Users.student_id_number]
    )
    if not users:
        raise NotFoundException(message="No valid users found with the provided student IDs.")

    existing_enrollments = await student_courses_controller.student_courses_repository._get_many(
        where_=[
            StudentCourses.course_id == request.course_id,
            StudentCourses.user_id.in_([u["id"] for u in users])
        ],
        fields=[StudentCourses.user_id]
    )
    enrolled_user_ids = {e["user_id"] for e in existing_enrollments}
    users_to_enroll = [u for u in users if u["id"] not in enrolled_user_ids]

    if not users_to_enroll:
        return Ok(
            data={"course_id": course.id, "course_name": course.name, "added_students_count": 0,
                  "already_enrolled_count": len(request.student_ids), "student_courses_list": []},
            message="All provided students are already enrolled in this course.",
        )

    sc_attributes = [{"user_id": u["id"], "course_id": request.course_id} for u in users_to_enroll]
    try:
        create_student_courses = await student_courses_controller.student_courses_repository.create_many(
            attributes_list=sc_attributes, commit=True
        )
        if not create_student_courses:
            raise Exception("Failed to add students to the course - no records returned.")

        sc_response = []
        for sc in create_student_courses:
            mssv = None
            for u in users_to_enroll:
                if str(u["id"]) == str(sc.user_id):
                    mssv = u.get("student_id_number")
                    break
            sc_response.append(StudentCourseInfo(
                student_id=str(sc.user_id),
                student_mssv=mssv,
                course_id=str(sc.course_id),
                last_accessed=str(sc.last_accessed) if hasattr(sc, 'last_accessed') else None,
                completed_lessons=sc.completed_lessons if hasattr(sc, 'completed_lessons') else None,
                time_spent=str(sc.time_spent) if hasattr(sc, 'time_spent') else None,
                percentage_done=sc.percentage_done if hasattr(sc, 'percentage_done') else None,
            ))

        already_enrolled_count = len(request.student_ids) - len(users_to_enroll)
        response = AddStudentsToCourseResponse(
            course_id=str(course.id),
            course_name=course.name,
            added_students_count=len(create_student_courses),
            already_enrolled_count=already_enrolled_count,
            student_courses_list=sc_response,
        )
        return Ok(
            data=response,
            message=f"Successfully added {len(create_student_courses)} student(s) to the course. {already_enrolled_count} student(s) were already enrolled.",
        )
    except Exception as e:
        print(f"Error adding students to course: {str(e)}")
        raise Exception(f"Failed to add students to the course: {str(e)}")


@router.get("/admin", description="Get all courses for admin", response_model=Ok[GetAdminCoursesPaginatedResponse])
async def get_all_courses_admin(
    current_user: Users = Depends(get_current_user),
    search_query: Optional[str] = Query(None, description="Search query to filter courses by name or courseID"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of items per page"),
    nCredit: Optional[int] = Query(None),
    nSemester: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    where_conditions = []
    if search_query:
        where_conditions.append((Courses.name.ilike(f"%{search_query}%")) | (Courses.courseID.ilike(f"%{search_query}%")))
    if nCredit is not None:
        where_conditions.append(Courses.nCredit == nCredit)
    if nSemester is not None:
        where_conditions.append(Courses.nSemester == nSemester)
    if start_date:
        where_conditions.append(Courses.start_date >= start_date)
    if end_date:
        where_conditions.append(Courses.end_date <= end_date)

    select_fields = [
        Courses.id.label("id"),
        Courses.name.label("name"),
        Courses.start_date.label("start_date"),
        Courses.end_date.label("end_date"),
        Courses.learning_outcomes.label("learning_outcomes"),
        Courses.status.label("status"),
        Courses.image_url.label("image"),
        Courses.nCredit.label("nCredit"),
        Courses.nSemester.label("nSemester"),
        Courses.courseID.label("courseID"),
        Courses.class_name.label("class_name"),
        Courses.owner_id.label("owner_id"),
    ]

    courses = await courses_controller.courses_repository._get_many(
        where_=where_conditions,
        fields=select_fields,
        order_={"desc": ["start_date"]},
        limit=page_size,
        skip=(page - 1) * page_size,
    )

    if not courses:
        return Ok(
            data={"content": [], "pageSize": page_size, "currentPage": page, "totalRows": 0, "totalPages": 0},
            message="No courses found.",
        )

    total_rows = await courses_controller.courses_repository.count(where_=where_conditions)
    total_pages = math.ceil(total_rows / page_size)

    courses_response = {
        "content": [
            GetAdminCoursesResponse(
                id=course.id,
                name=course.name,
                start_date=str(course.start_date),
                end_date=str(course.end_date),
                status=course.status,
                nCredit=course.nCredit if course.nCredit else 0,
                nSemester=course.nSemester if course.nSemester else 0,
                courseID=course.courseID,
                class_name=course.class_name if course.class_name else "",
                professor_id=str(course.owner_id) if course.owner_id else "",
            )
            for course in courses
        ],
        "pageSize": page_size,
        "currentPage": page,
        "totalRows": total_rows,
        "totalPages": total_pages,
    }
    return Ok(data=courses_response, message="Successfully fetched the courses.")


@router.patch("/{course_id}/image", response_model=Ok)
async def update_course_image(
    course_id: str,
    file: UploadFile = File(...),
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    course = await courses_controller.courses_repository.first(where_=[Courses.id == course_id])
    if not course:
        raise NotFoundException(message=f"Course with ID {course_id} not found.")

    if course.owner_id != current_user.id:
        raise ForbiddenException(message="You don't have permission to update this course.")

    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise BadRequestException(message="Invalid file type. Only JPG, JPEG, PNG, and GIF files are allowed.")

    file_content = await file.read()
    existing_image_key = course.image_url
    s3_key, presigned_url = await update_course_image_s3(
        existing_image_key,
        file_content,
        f"course_{course_id}{file_extension}"
    )

    await courses_controller.courses_repository.update(
        where_=[Courses.id == course_id],
        attributes={"image_url": s3_key},
        commit=True,
    )
    return Ok(message="Course image updated successfully.", data={"image_url": presigned_url})


@router.get("/{courseId}", response_model=Ok[GetCourseDetailResponse])
async def get_course_for_student(
    courseId: str,
    current_user: Users = Depends(get_current_user),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    learning_paths_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    select_fields = [
        Courses.name.label("name"),
        Courses.id.label("id"),
        Courses.start_date.label("start_date"),
        Courses.end_date.label("end_date"),
        Courses.learning_outcomes.label("learning_outcomes"),
        Courses.status.label("status"),
        Courses.image_url.label("image_url"),
        Courses.nCredit.label("nCredit"),
        Courses.nSemester.label("nSemester"),
        Courses.courseID.label("courseID"),
        Courses.class_name.label("class_name"),
        StudentCourses.last_accessed.label("last_accessed"),
        StudentCourses.completed_lessons.label("completed_lessons"),
        StudentCourses.time_spent.label("time_spent"),
        StudentCourses.percentage_done.label("percentage_done"),
    ]
    join_conditions = {"courses": {"type": "left", "alias": "courses_alias"}}

    course = await student_courses_controller.student_courses_repository._get_many(
        where_=[and_(StudentCourses.course_id == courseId, StudentCourses.user_id == current_user.id)],
        fields=select_fields,
        join_=join_conditions,
    )
    get_course = course[0] if course else None
    try:
        learning_path = await learning_paths_controller.get_learning_path(
            user_id=current_user.id, course_id=courseId
        )
    except NotFoundException:
        learning_path = None

    if not course:
        return Ok(
            data=GetCourseDetailResponse(
                course_id=courseId, course_name="", course_start_date="", course_end_date="",
                course_learning_outcomes=[], course_status="", course_image="",
                course_nCredit=0, course_nSemester=0, course_courseID="", course_classname="",
                course_percentage_complete="", course_last_accessed="",
                completed_lessons=0, time_spent="", percentage_done=0,
            ),
            message="You are not enrolled in this course.",
        )

    image_url = generate_presigned_url(get_course.image_url, expiration=604800) if get_course.image_url else ""
    course_response = GetCourseDetailResponse(
        course_id=str(courseId),
        course_name=get_course.name,
        course_start_date=str(get_course.start_date) if get_course.start_date else "",
        course_end_date=str(get_course.end_date) if get_course.end_date else "",
        course_learning_outcomes=get_course.learning_outcomes or [],
        course_status=get_course.status,
        course_image=image_url,
        course_nCredit=get_course.nCredit,
        course_nSemester=get_course.nSemester,
        course_courseID=get_course.courseID,
        course_classname=get_course.class_name,
        course_percentage_complete=str(learning_path.progress) if learning_path else "0",
        course_last_accessed=str(get_course.last_accessed) if get_course.last_accessed else "",
        completed_lessons=get_course.completed_lessons or 0,
        time_spent=str(get_course.time_spent) if get_course.time_spent else "",
        percentage_done=str(learning_path.progress) if learning_path else "0",
    )
    return Ok(data=course_response, message="Successfully fetched the course.")


@router.get("/{courseId}/professor", response_model=Ok[ProfessorInformation])
async def get_professor_for_course(
    courseId: str,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    course = await courses_controller.courses_repository.first(where_=[Courses.id == courseId])
    if not course:
        raise NotFoundException(message="Course not found.")

    owner = await user_controller.user_repository.first(where_=[Users.id == course.owner_id])
    if not owner:
        raise NotFoundException(message="Course owner not found.")

    professor_response = ProfessorInformation(
        professor_id=owner.id,
        professor_name=owner.full_name or "",
        professor_email=owner.email,
        professor_avatar=str(owner.avatar_url) if owner.avatar_url else "",
    )
    return Ok(data=professor_response, message="Successfully fetched the professor.")


@router.get("/{courseId}/students", response_model=Ok[List[StudentList]])
async def get_students_for_course(
    courseId: str,
    current_user: Users = Depends(get_current_user),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    select_fields = [
        Users.id.label("id"),
        Users.full_name.label("name"),
        Users.email.label("email"),
        Users.avatar_url.label("avatar_url"),
        Users.student_id_number.label("ms"),
    ]
    join_conditions = {"user": {"type": "left", "table": Users}}

    students = await student_courses_controller.student_courses_repository._get_many(
        where_=[StudentCourses.course_id == courseId],
        fields=select_fields,
        join_=join_conditions,
    )

    if not students:
        return Ok(data=[], message="No students found.")

    students_response = [
        StudentList(
            student_id=student.id,
            student_name=student.name or "",
            student_email=student.email,
            student_avatar=str(student.avatar_url) if student.avatar_url else "",
            student_mssv=student.ms or "",
        )
        for student in students
    ]
    return Ok(data=students_response, message="Successfully fetched the students.")


@router.get("/{courseId}/lessons", response_model=Ok[List[GetLessonsResponse]])
async def get_lessons_for_course(
    courseId: str,
    current_user: Users = Depends(get_current_user),
    lessons_controller: LessonsController = Depends(InternalProvider().get_lessons_controller),
    documents_controller: DocumentsController = Depends(InternalProvider().get_documents_controller),
):
    select_fields = [
        Lessons.id.label("id"),
        Lessons.title.label("title"),
        Lessons.description.label("description"),
        Lessons.learning_outcomes.label("learning_outcomes"),
        Lessons.order.label("order"),
    ]

    lessons = await lessons_controller.lessons_repository._get_many(
        where_=[Lessons.course_id == courseId],
        fields=select_fields,
    )

    if not lessons:
        return Ok(data=[], message="No lessons found.")

    lessons_response = [
        GetLessonsResponse(
            id=lesson.id,
            title=lesson.title,
            description=lesson.description or "",
            learning_outcomes=lesson.learning_outcomes or [],
            order=lesson.order,
            nDocuments=await documents_controller.documents_repository.count(where_=[Documents.lesson_id == lesson.id]),
        )
        for lesson in lessons
    ]
    return Ok(data=lessons_response, message="Successfully fetched the lessons.")


@router.get(
    "/{courseId}/lessons_recommendation/",
    response_model=Ok[List[GetLessonsRecommendationResponse]],
)
async def get_lessons_recommendation(
    courseId: UUID,
    current_user: Users = Depends(get_current_user),
    learning_paths_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
    lessons_controller: LessonsController = Depends(InternalProvider().get_lessons_controller),
):
    where_learning_path_conditions = [
        LearningPaths.user_id == current_user.id,
        LearningPaths.course_id == courseId,
    ]
    learning_path = await learning_paths_controller.learning_paths_repository.first(
        where_=where_learning_path_conditions,
        relations=[LearningPaths.recommend_lessons, LearningPaths.course],
    )

    if not learning_path:
        raise NotFoundException(message="Learning path not found for the given user and course.")

    recommend_lessons = learning_path.recommend_lessons
    course_name = learning_path.course.name if learning_path.course else "Unknown Course"

    if not recommend_lessons:
        raise NotFoundException(message="No recommended lessons found for the given learning path.")

    recommended_lessons: List[GetLessonsRecommendationResponse] = []
    for recommend_lesson in recommend_lessons:
        lesson = await lessons_controller.lessons_repository.first(where_=[Lessons.id == recommend_lesson.id])
        if not lesson:
            continue
        recommended_lessons.append(
            GetLessonsRecommendationResponse(
                course_id=courseId,
                course_name=course_name,
                lesson_id=lesson.id,
                title=lesson.title,
                description=lesson.description or "",
                order=lesson.order,
                bookmark=lesson.bookmark if hasattr(lesson, "bookmark") else False,
                status=recommend_lesson.status,
            )
        )
    return Ok(data=recommended_lessons, message="Successfully fetched the recommended lessons.")


@router.post("/", response_model=Ok[Union[CreateCourseResponse, List[CreateCourseResponse]]])
async def create_course(
    request: List[CreateCourseRequest],
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="Your account is not allowed to create a course.")

    if not request or len(request) == 0:
        raise BadRequestException(message="At least one course is required.")

    async def resolve_owner(professor_id_number: str) -> UUID:
        owner = await user_controller.user_repository.first(
            where_=[Users.employee_id_number == professor_id_number]
        )
        if not owner:
            raise NotFoundException(message=f"User with employee ID {professor_id_number} not found.")
        return owner.id

    async def enroll_users(owner_user_ids, course_id):
        users = await user_controller.user_repository._get_many(
            where_=[Users.student_id_number.in_(owner_user_ids)],
            fields=[Users.id, Users.student_id_number]
        )
        sc_attrs = [{"user_id": u["id"], "course_id": course_id} for u in users]
        if sc_attrs:
            await student_courses_controller.student_courses_repository.create_many(
                attributes_list=sc_attrs, commit=True
            )
        return users

    if len(request) == 1:
        r = request[0]
        if not r.nSemester or not r.class_name:
            raise BadRequestException(message="Semester and class name are required.")
        existing = await courses_controller.courses_repository.first(
            where_=[Courses.courseID == r.courseID, Courses.nSemester == r.nSemester, Courses.class_name == r.class_name]
        )
        if existing:
            raise BadRequestException(message="Course already exists.")

        owner_id = await resolve_owner(r.professorID)
        course_attributes = {
            "name": r.name,
            "owner_id": owner_id,
            "nCredit": r.creditNumber,
            "nSemester": r.nSemester,
            "createdByAdminID": current_user.id,
            "courseID": r.courseID,
            "start_date": r.startDate,
            "end_date": r.endDate,
            "class_name": r.class_name,
        }
        created_course = await courses_controller.courses_repository.create(attributes=course_attributes, commit=True)
        if not created_course:
            raise Exception("Failed to create course")

        enrolled = await enroll_users(r.studentIDs, created_course.id)
        return Ok(
            data={
                "course_id": created_course.id,
                "courseID": created_course.courseID,
                "name": created_course.name,
                "owner_id": created_course.owner_id,
                "start_date": str(created_course.start_date),
                "end_date": str(created_course.end_date),
                "status": created_course.status,
                "nCredit": created_course.nCredit,
                "nSemester": created_course.nSemester,
                "learning_outcomes": created_course.learning_outcomes or "",
                "image_url": str(created_course.image_url) if created_course.image_url else "",
                "student_courses_count": len(enrolled),
                "class_name": created_course.class_name,
            },
            message="Successfully created the course.",
        )
    else:
        professor_ids = [c.professorID for c in request]
        professors = await user_controller.user_repository._get_many(
            where_=[Users.employee_id_number.in_(professor_ids)],
            fields=[Users.id, Users.employee_id_number]
        )
        prof_id_map = {p["employee_id_number"]: p["id"] for p in professors}

        courses_attributes = []
        for r in request:
            if not r.nSemester or not r.class_name:
                raise BadRequestException(message="Semester and class name are required.")
            existing = await courses_controller.courses_repository.first(
                where_=[Courses.courseID == r.courseID, Courses.nSemester == r.nSemester, Courses.class_name == r.class_name]
            )
            if existing:
                raise BadRequestException(message="Course already exists.")
            if not r.name:
                raise BadRequestException(message="Course name is required.")
            owner_id = prof_id_map.get(r.professorID)
            if not owner_id:
                raise NotFoundException(message=f"User with employee ID {r.professorID} not found.")
            courses_attributes.append({
                "name": r.name,
                "owner_id": owner_id,
                "nCredit": r.creditNumber,
                "nSemester": r.nSemester,
                "createdByAdminID": current_user.id,
                "status": "new",
                "courseID": r.courseID,
                "start_date": r.startDate,
                "end_date": r.endDate,
                "class_name": r.class_name,
            })

        create_courses = await courses_controller.courses_repository.create_many(
            attributes_list=courses_attributes, commit=True
        )
        if not create_courses:
            raise Exception("Failed to create courses")

        courses_response = []
        for created_course, req_course in zip(create_courses, request):
            await enroll_users(req_course.studentIDs, created_course.id)
            courses_response.append({
                "course_id": created_course.id,
                "courseID": created_course.courseID,
                "name": created_course.name,
                "owner_id": created_course.owner_id,
                "start_date": str(created_course.start_date) if created_course.start_date else "",
                "end_date": str(created_course.end_date) if created_course.end_date else "",
                "status": created_course.status,
                "nCredit": created_course.nCredit,
                "nSemester": created_course.nSemester,
                "learning_outcomes": created_course.learning_outcomes or "",
                "image_url": str(created_course.image_url) if created_course.image_url else "",
                "class_name": created_course.class_name,
            })
        return Ok(data=courses_response, message="Successfully created the courses.")


@router.get("/{course_id}/personalized-lp", response_model=Ok[LearningPathDTO])
async def get_personalized_lp(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    lp_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    lp = await lp_controller.get_learning_path(course_id=course_id, user_id=current_user.id)
    return Ok(data=LearningPathDTO.model_validate(lp))


@router.get("/{course_id}/learning-path/recommended-lessons")
async def get_recommended_lessons(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    expand: Optional[Literal["modules"]] = Query(None, description="Expand related data, e.g., 'modules'."),
    lp_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    recommended_lessons = await lp_controller.get_recommended_lessons(
        user_id=current_user.id, course_id=course_id, expand=expand
    )
    return Ok(data=recommended_lessons)


@router.get("/{course_id}/students/{student_id}/learning-path/recommended-lessons")
async def get_recommended_lessons_for_student(
    course_id: UUID,
    student_id: UUID,
    current_user: Users = Depends(get_current_user),
    expand: Optional[Literal["modules"]] = Query(None, description="Expand related data, e.g., 'modules'."),
    lp_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    recommended_lessons = await lp_controller.get_recommended_lessons(
        user_id=student_id, course_id=course_id, expand=expand
    )
    return Ok(data=recommended_lessons)


@router.delete("/{course_id}/learning-path")
async def delete_learning_path(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    lp_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    await lp_controller.delete_learning_path(user_id=current_user.id, course_id=course_id)
    return Ok(data=None, message="Successfully deleted the learning path.")


@router.get("/{course_id}/exercises", response_model=Ok[List[GetExercise]])
async def get_course_exercises(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    course = await courses_controller.courses_repository.first(where_=[Courses.id == course_id])
    if not course:
        raise NotFoundException(message="Course not found for the given ID.")

    is_owner = (course.owner_id == current_user.id)
    conditions = [Exercises.course_id == course_id]
    if not is_owner:
        conditions.append(Exercises.time_open <= datetime.now())

    exercises = await exercises_controller.exercises_repository.get_many(
        where_=conditions,
        order_={"desc": ["time_open"]},
    )
    return Ok[List[GetExercise]](data=[
        GetExercise(
            id=exercise.id,
            name=exercise.name,
            description=exercise.description,
            type=exercise.type,
            time_open=exercise.time_open.strftime("%H:%M %d/%m/%Y"),
            time_close=exercise.time_close.strftime("%H:%M %d/%m/%Y"),
            time_limit=exercise.time_limit,
            attempts_allowed=exercise.attempts_allowed,
            grading_method=exercise.grading_method,
        )
        for exercise in exercises
    ])


@router.patch("/admin/{course_id}")
async def update_course(
    course_id: UUID,
    request: UpdateCourseRequest,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    course_attributes = {}
    if request.name is not None:
        course_attributes["name"] = request.name
    if request.n_credit is not None:
        course_attributes["nCredit"] = request.n_credit
    if request.n_semester is not None:
        course_attributes["nSemester"] = request.n_semester
    if request.courseID is not None:
        course_attributes["courseID"] = request.courseID
    if request.start_date is not None:
        course_attributes["start_date"] = request.start_date
    if request.end_date is not None:
        course_attributes["end_date"] = request.end_date
    if request.class_name is not None:
        course_attributes["class_name"] = request.class_name
    if request.professor_id is not None:
        course_attributes["owner_id"] = request.professor_id
    if request.status is not None:
        course_attributes["status"] = request.status

    update_course_result = await courses_controller.courses_repository.update(
        where_=[Courses.id == course_id],
        attributes=course_attributes,
        commit=True,
    )

    if not update_course_result:
        raise BadRequestException(message="Failed to update course.")

    return Ok(data=None, message="Successfully updated the course.")


@router.delete("/admin/{course_id}")
async def delete_course(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    await courses_controller.courses_repository.delete(where_=[Courses.id == course_id])
    await student_courses_controller.student_courses_repository.delete(where_=[StudentCourses.course_id == course_id])
    await courses_controller.courses_repository.session.commit()
    await student_courses_controller.student_courses_repository.session.commit()

    return Ok(data=None, message="Successfully deleted the course.")


@router.get("/issues/{course_id}")
async def get_course_issues(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    student_courses_controller: StudentCoursesController = Depends(InternalProvider().get_studentcourses_controller),
):
    course = await student_courses_controller.student_courses_repository.first(
        where_=[StudentCourses.course_id == course_id]
    )
    if not course:
        raise NotFoundException(message="Student does not enroll in this course.")

    return Ok(data={"issues_summary": course.issues_summary}, message="Successfully fetched the course issues.")
