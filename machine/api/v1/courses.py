import math
import os
from datetime import date, datetime
from typing import List, Literal, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, Form
from sqlalchemy import and_, or_, func

from core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from core.response import Ok
from core.utils.file import upload_image
from core.utils.get_current_user import get_current_user
from machine.controllers import (
    CoursesController,
    DocumentsController,
    ExercisesController,
    ExtractedTextController,
    LearningPathsController,
    RecommendLessonsController,
)
from machine.models import (
    Courses,
    Documents,
    Exercises,
    LearningPaths,
    RecommendLessons,
    Users,
)
from machine.providers import InternalProvider
from machine.schemas.requests.courses import (
    CreateCourseRequest,
    UpdateCourseRequest,
    PutLearningOutcomesCoursesRequest,
    JoinCourseRequest,
)
from machine.schemas.responses.courses import (
    GetAdminCoursesPaginatedResponse,
    GetAdminCoursesResponse,
    GetCourseDetailResponse,
    GetCoursesPaginatedResponse,
    GetCoursesResponse,
    GetDocumentsResponse,
    PutLearningOutcomesCoursesResponse,
)
from machine.schemas.responses.progress_tracking import GetCoursesListResponse

router = APIRouter(prefix="/courses", tags=["courses"])


# ---------------------------------------------------------------------------
# GET /  – List courses for authenticated user (owned + member)
# ---------------------------------------------------------------------------
@router.get("/", response_model=Ok[GetCoursesPaginatedResponse])
async def get_courses(
    current_user: Users = Depends(get_current_user),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of items per page"),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    """Get all courses where the user is owner or member."""
    # Courses owned by user
    owned = await courses_controller.courses_repository.get_many(
        where_=[Courses.owner_id == current_user.id],
    )
    # Courses where user is a member
    member = await courses_controller.courses_repository.get_many(
        where_=[Courses.members.any(str(current_user.id))],
    )

    # Merge and deduplicate
    seen_ids = set()
    all_courses = []
    for c in owned + member:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            all_courses.append(c)

    total = len(all_courses)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_courses[start:end]

    content = [
        GetCoursesResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            start_date=str(c.start_date) if c.start_date else None,
            end_date=str(c.end_date) if c.end_date else None,
            image_url=c.image_url,

            learning_outcomes=c.learning_outcomes,
            status=c.status,
            is_owner=(c.owner_id == current_user.id),
            members_count=len(c.members) if c.members else 0,
        )
        for c in paginated
    ]

    return Ok(
        data=GetCoursesPaginatedResponse(
            content=content,
            currentPage=page,
            pageSize=page_size,
            totalRows=total,
            totalPages=total_pages,
        ),
        message="Successfully fetched courses.",
    )


# ---------------------------------------------------------------------------
# GET /count – Total count of owned courses
# ---------------------------------------------------------------------------
@router.get("/count", response_model=Ok[int])
async def count_courses(
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    count = await courses_controller.courses_repository.count(
        where_=[Courses.owner_id == current_user.id]
    )
    return Ok(data=count, message="Successfully fetched the count of courses.")


# ---------------------------------------------------------------------------
# GET /admin – List all courses (admin only)
# ---------------------------------------------------------------------------
@router.get("/admin", response_model=Ok[GetAdminCoursesPaginatedResponse])
async def get_all_courses_admin(
    current_user: Users = Depends(get_current_user),
    search_query: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(10),
    status: Optional[str] = Query(None),

    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="Only admins can access this endpoint.")

    filters = []
    if search_query:
        filters.append(Courses.name.ilike(f"%{search_query}%"))
    if status:
        filters.append(Courses.status == status)

    if start_date:
        filters.append(Courses.start_date >= start_date)
    if end_date:
        filters.append(Courses.end_date <= end_date)

    total = await courses_controller.courses_repository.count(where_=filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    courses = await courses_controller.courses_repository.get_many(
        where_=filters,
        order_={"desc": [{"field": "created_at", "model_class": Courses}]},
        limit=page_size,
        offset=(page - 1) * page_size,
        relations=[Courses.owner],
    )

    content = [
        GetAdminCoursesResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            start_date=str(c.start_date) if c.start_date else None,
            end_date=str(c.end_date) if c.end_date else None,
            status=c.status,

            owner_name=c.owner.full_name if c.owner else None,
            members_count=len(c.members) if c.members else 0,
        )
        for c in courses
    ]

    return Ok(
        data=GetAdminCoursesPaginatedResponse(
            content=content,
            currentPage=page,
            pageSize=page_size,
            totalRows=total,
            totalPages=total_pages,
        ),
        message="Successfully fetched all courses.",
    )


# ---------------------------------------------------------------------------
# POST / – Create a new course (any user)
# ---------------------------------------------------------------------------
@router.post("/", response_model=Ok[dict])
async def create_course(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    learning_outcomes: Optional[List[str]] = Form(None),
    start_date: Optional[date] = Form(None),
    end_date: Optional[date] = Form(None),

    files: List[UploadFile] = File(None),
    file_descriptions: List[str] = Form(None),
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    documents_controller: DocumentsController = Depends(InternalProvider().get_documents_controller),
    extracted_text_controller: ExtractedTextController = Depends(InternalProvider().get_extracted_text_controller),
):
    """Create a course. Optionally upload documents at creation time."""
    from utils.file_processor import process_document

    course = await courses_controller.courses_repository.create(
        attributes={
            "name": name,
            "description": description,
            "owner_id": current_user.id,
            "members": [],
            "learning_outcomes": learning_outcomes or [],
            "start_date": start_date,
            "end_date": end_date,

        },
        commit=True,
    )

    created_docs = []
    if files:
        for idx, file in enumerate(files):
            desc = file_descriptions[idx] if file_descriptions and idx < len(file_descriptions) else file.filename
            doc_url, _ = await upload_image(file, str(course.id))
            doc = await documents_controller.documents_repository.create(
                attributes={
                    "course_id": course.id,
                    "name": file.filename,
                    "type": file.content_type or "application/octet-stream",
                    "description": desc,
                    "document_url": doc_url,
                    "status": "processing",
                },
                commit=True,
            )
            created_docs.append({"id": str(doc.id), "name": doc.name})
            # Process document in background
            try:
                await process_document(doc, extracted_text_controller, documents_controller)
            except Exception:
                pass

    return Ok(
        data={
            "course_id": str(course.id),
            "name": course.name,
            "documents": created_docs,
        },
        message="Course created successfully.",
    )


# ---------------------------------------------------------------------------
# POST /join – Join a course
# ---------------------------------------------------------------------------
@router.post("/join", response_model=Ok[dict])
async def join_course(
    request: JoinCourseRequest,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    """Join another user's course. Adds current user to members list."""
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == request.course_id]
    )
    if not course:
        raise NotFoundException(message="Course not found.")

    if course.owner_id == current_user.id:
        raise BadRequestException(message="You are already the owner of this course.")

    current_members = list(course.members) if course.members else []
    if current_user.id in current_members:
        raise BadRequestException(message="You are already a member of this course.")

    current_members.append(current_user.id)
    await courses_controller.courses_repository.update(
        where_=[Courses.id == request.course_id],
        attributes={"members": current_members},
        commit=True,
    )
    return Ok(data={"course_id": str(course.id)}, message="Successfully joined the course.")


# ---------------------------------------------------------------------------
# POST /leave – Leave a course
# ---------------------------------------------------------------------------
@router.post("/leave", response_model=Ok[dict])
async def leave_course(
    request: JoinCourseRequest,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    """Leave a course. Removes current user from members list."""
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == request.course_id]
    )
    if not course:
        raise NotFoundException(message="Course not found.")

    if course.owner_id == current_user.id:
        raise BadRequestException(message="Owner cannot leave their own course.")

    current_members = list(course.members) if course.members else []
    if current_user.id not in current_members:
        raise BadRequestException(message="You are not a member of this course.")

    current_members.remove(current_user.id)
    await courses_controller.courses_repository.update(
        where_=[Courses.id == request.course_id],
        attributes={"members": current_members},
        commit=True,
    )
    return Ok(data={"course_id": str(course.id)}, message="Successfully left the course.")


# ---------------------------------------------------------------------------
# PATCH /{course_id}/image – Update course image
# ---------------------------------------------------------------------------
@router.patch("/{course_id}/image", response_model=Ok[dict])
async def update_course_image(
    course_id: str,
    file: UploadFile = File(...),
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == course_id]
    )
    if not course:
        raise NotFoundException(message="Course not found.")
    if course.owner_id != current_user.id:
        raise ForbiddenException(message="Only the course owner can update the image.")

    image_url, _ = await upload_image(file, course_id)
    updated = await courses_controller.courses_repository.update(
        where_=[Courses.id == course_id],
        attributes={"image_url": image_url},
        commit=True,
    )
    return Ok(data={"image_url": updated.image_url}, message="Course image updated.")


# ---------------------------------------------------------------------------
# GET /{courseId} – Get course details
# ---------------------------------------------------------------------------
@router.get("/{courseId}", response_model=Ok[GetCourseDetailResponse])
async def get_course_detail(
    courseId: str,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    documents_controller: DocumentsController = Depends(InternalProvider().get_documents_controller),
    exercises_controller: ExercisesController = Depends(InternalProvider().get_exercises_controller),
):
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == courseId],
    )
    if not course:
        raise NotFoundException(message="Course not found.")

    # Check access: owner, member, or admin
    is_owner = course.owner_id == current_user.id
    is_member = current_user.id in (course.members or [])
    if not is_owner and not is_member and current_user.role != "admin":
        raise ForbiddenException(message="You don't have access to this course.")

    n_docs = await documents_controller.documents_repository.count(
        where_=[Documents.course_id == course.id]
    )
    n_exercises = await exercises_controller.exercises_repository.count(
        where_=[Exercises.course_id == course.id]
    )

    return Ok(
        data=GetCourseDetailResponse(
            course_id=course.id,
            course_name=course.name,
            course_description=course.description,
            course_start_date=str(course.start_date) if course.start_date else None,
            course_end_date=str(course.end_date) if course.end_date else None,
            course_learning_outcomes=course.learning_outcomes or [],
            course_status=str(course.status),
            course_image=course.image_url,

            is_owner=is_owner,
            members_count=len(course.members) if course.members else 0,
            nDocuments=n_docs,
            nExercises=n_exercises,
        ),
        message="Successfully fetched course details.",
    )


# ---------------------------------------------------------------------------
# GET /{courseId}/documents – List documents for a course
# ---------------------------------------------------------------------------
@router.get("/{courseId}/documents", response_model=Ok[List[GetDocumentsResponse]])
async def get_documents_for_course(
    courseId: str,
    current_user: Users = Depends(get_current_user),
    documents_controller: DocumentsController = Depends(InternalProvider().get_documents_controller),
):
    docs = await documents_controller.documents_repository.get_many(
        where_=[Documents.course_id == courseId],
    )
    from core.utils.file import generate_presigned_url

    result = []
    for d in docs:
        url = generate_presigned_url(d.document_url) if d.document_url else ""
        result.append(
            GetDocumentsResponse(id=d.id, name=d.name, type=d.type, url=url)
        )
    return Ok(data=result, message="Successfully fetched documents.")


# ---------------------------------------------------------------------------
# PUT /{courseId}/learning-outcomes – Update learning outcomes
# ---------------------------------------------------------------------------
@router.put("/{courseId}/learning-outcomes", response_model=Ok[PutLearningOutcomesCoursesResponse])
async def update_learning_outcomes(
    courseId: str,
    request: PutLearningOutcomesCoursesRequest,
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == courseId]
    )
    if not course:
        raise NotFoundException(message="Course not found.")
    if course.owner_id != current_user.id:
        raise ForbiddenException(message="Only the course owner can update learning outcomes.")

    updated = await courses_controller.courses_repository.update(
        where_=[Courses.id == courseId],
        attributes={"learning_outcomes": request.learning_outcomes},
        commit=True,
    )
    return Ok(
        data=PutLearningOutcomesCoursesResponse(
            course_id=updated.id,
            learning_outcomes=updated.learning_outcomes,
        ),
        message="Learning outcomes updated.",
    )


# ---------------------------------------------------------------------------
# GET /{course_id}/learning-path – Get personalised learning path
# ---------------------------------------------------------------------------
@router.get("/{course_id}/learning-path", response_model=Ok[dict])
async def get_personalized_lp(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    lp_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    lp = await lp_controller.learning_paths_repository.first(
        where_=[
            LearningPaths.user_id == current_user.id,
            LearningPaths.course_id == course_id,
        ],
    )
    if not lp:
        return Ok(data=None, message="No learning path found.")
    return Ok(data={"id": str(lp.id), "progress": lp.progress, "objective": lp.objective}, message="OK")


# ---------------------------------------------------------------------------
# GET /{course_id}/recommended-lessons – Get recommended lessons for a learning path
# ---------------------------------------------------------------------------
@router.get("/{course_id}/recommended-lessons")
async def get_recommended_lessons(
    course_id: UUID,
    current_user: Users = Depends(get_current_user),
    expand: Optional[Literal["modules"]] = Query(None),
    lp_controller: LearningPathsController = Depends(InternalProvider().get_learningpaths_controller),
):
    lp = await lp_controller.learning_paths_repository.first(
        where_=[
            LearningPaths.user_id == current_user.id,
            LearningPaths.course_id == course_id,
        ],
        relations=[LearningPaths.recommend_lessons],
    )
    if not lp:
        return Ok(data=[], message="No learning path found.")

    lessons_data = []
    for rl in lp.recommend_lessons:
        item = {
            "id": str(rl.id),
            "title": rl.title,
            "description": rl.description,
            "progress": rl.progress,
            "status": str(rl.status),
            "bookmark": rl.bookmark,
            "order": rl.order,
            "start_date": rl.start_date,
            "end_date": rl.end_date,
        }
        if expand == "modules":
            from machine.models import Modules
            modules = rl.modules or []
            item["modules"] = [
                {"id": str(m.id), "title": m.title, "progress": m.progress, "objectives": m.objectives}
                for m in modules
            ]
        lessons_data.append(item)

    return Ok(data=lessons_data, message="Successfully fetched recommended lessons.")


# ---------------------------------------------------------------------------
# POST /{courseId}/documents – Upload documents to a course
# ---------------------------------------------------------------------------
@router.post("/{courseId}/documents", response_model=Ok[List[dict]])
async def add_documents_to_course(
    courseId: UUID,
    files: List[UploadFile] = File(...),
    descriptions: List[str] = Form(...),
    current_user: Users = Depends(get_current_user),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
    documents_controller: DocumentsController = Depends(InternalProvider().get_documents_controller),
    extracted_text_controller: ExtractedTextController = Depends(InternalProvider().get_extracted_text_controller),
):
    """Upload documents to an existing course."""
    from utils.file_processor import process_document

    course = await courses_controller.courses_repository.first(
        where_=[Courses.id == courseId]
    )
    if not course:
        raise NotFoundException(message="Course not found.")
    if course.owner_id != current_user.id:
        raise ForbiddenException(message="Only the course owner can add documents.")

    created_docs = []
    for idx, file in enumerate(files):
        desc = descriptions[idx] if idx < len(descriptions) else file.filename
        doc_url, _ = await upload_image(file, str(courseId))
        doc = await documents_controller.documents_repository.create(
            attributes={
                "course_id": str(courseId),
                "name": file.filename,
                "type": file.content_type or "application/octet-stream",
                "description": desc,
                "document_url": doc_url,
                "status": "processing",
            },
            commit=True,
        )
        created_docs.append({"id": str(doc.id), "name": doc.name, "status": doc.status})
        try:
            await process_document(doc, extracted_text_controller, documents_controller)
        except Exception:
            pass

    return Ok(data=created_docs, message="Documents uploaded successfully.")
