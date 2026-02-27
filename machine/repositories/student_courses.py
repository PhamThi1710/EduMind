from sqlalchemy import Select
from core.repository import BaseRepository
from machine.models import StudentCourses, Courses, Users
from sqlalchemy.orm import aliased


class StudentCoursesRepository(BaseRepository[StudentCourses]):
    def _join_courses(self, query: Select, join_params: dict) -> Select:
        join_type = join_params.get('type', 'inner')
        alias = join_params.get('table', Courses)

        if join_type == 'left':
            return query.outerjoin(alias, alias.id == self.model_class.course_id)
        return query.join(alias, alias.id == self.model_class.course_id)

    def _join_user(self, query: Select, join_params: dict) -> Select:
        join_type = join_params.get('type', 'inner')
        alias = join_params.get('table', Users)

        query = query.select_from(StudentCourses)

        if join_type == 'left':
            return query.outerjoin(alias, alias.id == StudentCourses.user_id)
        return query.join(alias, alias.id == StudentCourses.user_id)
