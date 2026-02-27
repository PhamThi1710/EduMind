from sqlalchemy import Select
from core.repository.base import BaseRepository
from machine.models import Courses, Documents, Users


class CoursesRepository(BaseRepository[Courses]):
    def _join_owner(self, query: Select, join_params: dict) -> Select:
        """Join on owner_id to the users table."""
        join_type = join_params.get('type', 'inner')
        table = join_params.get('table', Users)

        if join_type == 'left':
            return query.outerjoin(table, self.model_class.owner_id == table.id)
        return query.join(table, self.model_class.owner_id == table.id)

    def _join_documents(self, query: Select, join_params: dict) -> Select:
        join_type = join_params.get('type', 'inner')
        alias = join_params.get('table', Documents)

        if join_type == 'left':
            return query.outerjoin(alias, alias.course_id == self.model_class.id)
        return query.join(alias, alias.course_id == self.model_class.id)