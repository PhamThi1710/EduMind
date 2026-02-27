from sqlalchemy import and_, extract
from machine.models import *
from core.response import Ok
from machine.controllers import *
from machine.schemas.requests.feedback import *
from machine.schemas.responses.feedback import *
from typing import List, Union
from fastapi import APIRouter, Depends, Query
from machine.providers import InternalProvider
from core.utils.get_current_user import get_current_user
from machine.schemas.responses.courses import *
from core.exceptions import *
from datetime import datetime, timezone, timedelta, date
from core.repository.enum import FeedbackStatusType
from pydantic import BaseModel

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/")
async def create_feedback(
    request: Union[CreateFeedbackRequest],
    current_user: Users = Depends(get_current_user),
    feedback_controller: FeedbackController = Depends(InternalProvider().get_feedback_controller),
):
    feedback_attributes = {
        "feedback_type": FeedbackType.course.value if request.type == FeedbackType.course else FeedbackType.system.value,
        "title": request.title,
        "category": request.category,
        "description": request.description,
        "rate": request.rate,
        "status": "pending",
        "user_id": str(current_user.id),
        "course_id": request.courseId if request.courseId else None,
    }

    try:
        feedback = await feedback_controller.feedback_repository.create(
            attributes=feedback_attributes,
            commit=True
        )
    except Exception as e:
        raise BadRequestException(message=f"Failed to create feedback: {str(e)}")

    feedback_response = CreateFeedbackResponse(
        id=str(feedback.id),
        type=feedback.feedback_type,
        title=feedback.title,
        category=feedback.category,
        description=feedback.description,
        rate=feedback.rate,
        status=feedback.status,
        created_at=str(feedback.created_at),
        resolved_at=str(feedback.resolved_at) if feedback.resolved_at else "",
    )

    return Ok(data=feedback_response, message="Feedback created successfully.")


@router.get("/courses/{course_id}", response_model=Ok[List[GetFeedbackProfessorResponse]])
async def get_feedback_professor(
    course_id: str,
    current_user: Users = Depends(get_current_user),
    feedback_controller: FeedbackController = Depends(InternalProvider().get_feedback_controller),
    user_controller=Depends(InternalProvider().get_user_controller),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    if current_user.role not in ["admin", "professor"]:
        raise ForbiddenException(message="Only admins/professors can access course feedback.")
    
    # Must be course owner if professor
    if current_user.role == "professor":
        course = await courses_controller.courses_repository.first(
            where_=[Courses.id == course_id, Courses.owner_id == current_user.id]
        )
    else:
        course = await courses_controller.courses_repository.first(where_=[Courses.id == course_id])

    if not course:
        raise BadRequestException(message="Course not found or access denied.")

    feedbacks = await feedback_controller.feedback_repository.get_many(
        where_=[Feedback.course_id == course_id]
    )

    feedback_response = []
    for feedback in feedbacks:
        user = await user_controller.user_repository.first(where_=[Users.id == feedback.user_id])
        if not user:
            continue
        feedback_response.append(
            GetFeedbackProfessorResponse(
                id=feedback.id,
                type=feedback.feedback_type,
                title=feedback.title,
                category=feedback.category,
                description=feedback.description,
                rate=feedback.rate,
                status=feedback.status,
                created_at=str(feedback.created_at),
                resolved_at=str(feedback.resolved_at) if feedback.resolved_at else "",
                student_id=feedback.user_id,
                student_name=user.full_name,
                student_email=user.email,
                student_mssv=user.student_id_number or user.employee_id_number or "",
            )
        )

    return Ok(data=feedback_response)


@router.get("/", description="Get all feedbacks")
async def get_feedback_list(
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None),
    feedback_type: str = Query(None, title="Feedback Type", description="Type of feedback", example="system"),
    status: str = Query(None, title="Feedback Status", description="Status of feedback", example="pending"),
    category: str = Query(None, title="Feedback Category", description="Category of feedback", example="user_interface"),
    start_date: date = Query(None, description="Start date for feedback creation (format: YYYY-MM-DD)"),
    end_date: date = Query(None, description="End date for feedback creation (format: YYYY-MM-DD)"),
    current_user: Users = Depends(get_current_user),
    feedback_controller: FeedbackController = Depends(InternalProvider().get_feedback_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to get feedbacks.")

    filters = []

    if category:
        if category not in ["user_interface", "feature_request", "bug_report", "performance", "others"]:
            raise BadRequestException(message="Invalid feedback category.")
        filters.append(Feedback.category == category)

    if feedback_type:
        if feedback_type not in ["system", "course"]:
            raise BadRequestException(message="Invalid feedback type.")
        filters.append(Feedback.feedback_type == feedback_type)

    if status:
        if status not in ["pending", "in_progress", "resolved"]:
            raise BadRequestException(message="Invalid feedback status.")
        filters.append(Feedback.status == status)

    if month:
        filters.append(extract('month', Feedback.created_at) == month)
    if year:
        filters.append(extract('year', Feedback.created_at) == year)
    if start_date:
        filters.append(Feedback.created_at >= start_date)
    if end_date:
        filters.append(Feedback.created_at <= end_date)

    join_conditions = {
        "user": {"type": "left", "alias": "user_alias"},
    }

    select_fields = [
        Feedback.id,
        Feedback.feedback_type,
        Feedback.title,
        Feedback.category,
        Feedback.description,
        Feedback.rate,
        Feedback.status,
        Feedback.created_at,
        Feedback.resolved_at,
        Feedback.user_id,
        Users.full_name.label("name"),
        Users.email.label("email"),
    ]

    feedbacks = await feedback_controller.feedback_repository._get_many(
        where_=filters, join_=join_conditions, fields=select_fields
    )
    feedback_response = [
        {
            "id": feedback.id,
            "type": "course" if feedback.feedback_type == "course" else "system",
            "title": feedback.title,
            "category": feedback.category,
            "description": feedback.description,
            "rate": feedback.rate,
            "status": feedback.status,
            "created_at": feedback.created_at,
            "resolved_at": feedback.resolved_at if feedback.resolved_at else "",
            "student_id": feedback.user_id,
            "student_name": feedback.name if feedback.name else "",
            "student_email": feedback.email if feedback.email else "",
        }
        for feedback in feedbacks
    ]
    return Ok(data=feedback_response, message="Feedbacks retrieved successfully.")


@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    request: UpdateFeedbackRequest,
    current_user: Users = Depends(get_current_user),
    feedback_controller: FeedbackController = Depends(InternalProvider().get_feedback_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to update feedbacks.")

    feedback = await feedback_controller.feedback_repository.first(where_=[Feedback.id == feedback_id])
    if not feedback:
        raise BadRequestException(message="Feedback not found.")

    try:
        resolved_at = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None) if request.status == FeedbackStatusType.resolved else None

        updated_feedback = await feedback_controller.feedback_repository.update(
            where_=[Feedback.id == feedback_id],
            attributes={"status": request.status, "resolved_at": resolved_at},
            commit=True,
        )

        if not updated_feedback:
            raise BadRequestException(message="Failed to update feedback.")

        return Ok(data=bool(True), message="Feedback updated successfully.")

    except Exception as e:
        raise BadRequestException(message=f"Failed to update feedback: {str(e)}")


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    current_user: Users = Depends(get_current_user),
    feedback_controller: FeedbackController = Depends(InternalProvider().get_feedback_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to delete feedbacks.")

    feedback = await feedback_controller.feedback_repository.first(where_=[Feedback.id == feedback_id])
    if not feedback:
        raise BadRequestException(message="Feedback not found.")

    try:
        await feedback_controller.feedback_repository.delete(where_=[Feedback.id == feedback_id])
        await feedback_controller.feedback_repository.session.commit()
    except Exception as e:
        raise BadRequestException(message=f"Failed to delete feedback: {str(e)}")

    return Ok(data=bool(True), message="Feedback deleted successfully.")


@router.post("/professors", response_model=Ok[List[FeedbackSummaryResponse]])
async def get_recent_professor_feedback(
    request: FeedbackDashboardRequest,
    current_user: Users = Depends(get_current_user),
    feedback_controller: FeedbackController = Depends(InternalProvider().get_feedback_controller),
    courses_controller: CoursesController = Depends(InternalProvider().get_courses_controller),
):
    # Course owner access check
    filters = [Feedback.feedback_type == "course"]

    if request.course_id:
        course = await courses_controller.courses_repository.first(
            where_=[Courses.id == request.course_id, Courses.owner_id == current_user.id]
        )
        if not course:
            raise BadRequestException(message="Course not found or access denied.")
        filters.append(Feedback.course_id == request.course_id)
    else:
        courses = await courses_controller.courses_repository.get_many(
            where_=[Courses.owner_id == current_user.id]
        )
        course_ids = [c.id for c in courses]
        if course_ids:
            filters.append(Feedback.course_id.in_(course_ids))
        else:
            return Ok(data=[], message="No courses found for this user.")

    join_conditions = {
        "user": {"type": "left", "alias": "user_alias"},
        "course": {"type": "left", "alias": "course_alias"},
    }

    select_fields = [
        Feedback.id,
        Feedback.title,
        Feedback.category,
        Feedback.description,
        Feedback.rate,
        Feedback.created_at,
        Feedback.user_id,
        Feedback.course_id,
        Users.full_name.label("student_name"),
        Courses.name.label("course_name"),
    ]

    limit = request.limit if hasattr(request, "limit") and request.limit else 5

    feedbacks = await feedback_controller.feedback_repository._get_many(
        where_=filters,
        join_=join_conditions,
        fields=select_fields,
        order_={"desc": ["created_at"]},
        limit=limit,
    )

    feedback_responses = [
        {
            "id": str(feedback.id),
            "student_id": str(feedback.user_id),
            "student_name": feedback.student_name if feedback.student_name else "",
            "title": feedback.title,
            "description": feedback.description,
            "category": feedback.category,
            "rate": feedback.rate,
            "created_at": str(feedback.created_at),
            "course_id": str(feedback.course_id) if feedback.course_id else None,
            "course_name": feedback.course_name if feedback.course_name else None,
        }
        for feedback in feedbacks
    ]

    return Ok(data=feedback_responses, message="Recent feedback retrieved successfully.")