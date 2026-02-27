from typing import List
from core.response import Ok
from machine.models import *
from fastapi import APIRouter, Depends
from machine.schemas.requests import *
from machine.schemas.responses.recommend import *
from machine.controllers import *
from machine.providers import InternalProvider
from core.utils.get_current_user import get_current_user
from core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/recommend_lessons", tags=["recommendation"])


@router.get("/{recommendLessonId}", response_model=Ok[RecommendLessonResponse])
async def recommend_lesson(
    recommendLessonId: UUID,
    current_user: Users = Depends(get_current_user),
    recommend_lessons_controller: RecommendLessonsController = Depends(InternalProvider().get_recommendlessons_controller),
):
    # Fetch the lesson recommendation details
    recommend_lesson = await recommend_lessons_controller.recommend_lessons_repository.first(
        where_=[RecommendLessons.id == recommendLessonId],
        relations=[RecommendLessons.modules, RecommendLessons.learning_path],
    )

    if not recommend_lesson:
        raise NotFoundException(message="Recommend Lesson not found for the given ID.")

    if not recommend_lesson.learning_path.user_id == current_user.id:
        raise NotFoundException(message="You are not authorized to access this recommend lesson.")

    get_modules = recommend_lesson.modules
    if not get_modules:
        raise NotFoundException(message="Modules not found for the given Recommend Lesson.")

    response_data = RecommendLessonResponse(
        id=recommend_lesson.id,
        title=recommend_lesson.title,
        learning_outcomes=recommend_lesson.learning_outcomes or [],
        description=recommend_lesson.description,
        progress=recommend_lesson.progress,
        status=str(recommend_lesson.status),
        recommend_content=recommend_lesson.recommended_content,
        explain=recommend_lesson.explain,
        start_date=recommend_lesson.start_date,
        end_date=recommend_lesson.end_date,
        duration_notes=recommend_lesson.duration_notes,
        modules=[
            ModuleResponse(
                module_id=module.id,
                title=module.title,
                progress=module.progress,
                objectives=[objective for objective in module.objectives],
            )
            for module in get_modules
        ],
    )

    return Ok(data=response_data, message="Successfully fetched the recommended lesson.")

@router.get("/{recommendLessonId}/bookmark")
async def bookmark_recommend_lesson(
    recommendLessonId: str,
    current_user: Users = Depends(get_current_user),
    recommend_lessons_controller: RecommendLessonsController = Depends(InternalProvider().get_recommendlessons_controller),
):
    recommend_lesson = await recommend_lessons_controller.recommend_lessons_repository.first(
        where_=[RecommendLessons.id == recommendLessonId]
    )

    if not recommend_lesson:
        raise NotFoundException(message="Recommend Lesson not found for the given ID.")
    
    update_bookmark = not recommend_lesson.bookmark
    updated_recommend_lesson = await recommend_lessons_controller.recommend_lessons_repository.update(
        where_=[RecommendLessons.id == recommendLessonId],
        attributes={
            "bookmark": update_bookmark,
        },
        commit=True,
    )
    
    if not updated_recommend_lesson:
        raise NotFoundException(message="Bookmark not found for the given Recommend Lesson.")
    
    result = {
        "id": str(updated_recommend_lesson.id),
        "bookmark": updated_recommend_lesson.bookmark,
    }
    
    return Ok(data=result, message="Successfully toggled the bookmark status of the recommended lesson.")