from sqlalchemy import and_, inspect, or_
from app.users.models import Role, User
from app.dao import BaseDAO, async_session_maker
from app.users.rb import RBRegistration
from fastapi.exceptions import HTTPException

class DAORole(BaseDAO):
    model = Role
    relationships = [model.users]
    DEFAULT_ROLE = "DOCTOR"


class DAOUser(BaseDAO):
    model = User
    relationships = [model.role, model.applications, model.performed_applications]
    
    @classmethod
    async def search_users(cls, limit, offset, **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = await cls._create_select_query()
            query = query.filter(await cls._create_user_search_condition(**filter))
            query = query.limit(limit).offset(offset)
            result = await session.execute(query)
            result = result.scalars().all()
            if not result:
                raise ValueError(f'В модели {repr(cls.model)} нет таких строк.')
            return result
    
    @classmethod
    async def _create_user_search_condition(cls, **filter):
        mapper = inspect(cls.model)
        or_query_columns = ['email', 'username', 'phone']
        query = []
        query_or = []
        for col in or_query_columns:
            if filter.get(col):
                query_or.append(mapper.columns[col].contains(filter[col]))
                filter.pop(col)
        for k, v in filter.items():
            query.append(mapper.columns[k].contains(v))
        return and_(or_(*query_or), *query)
    

    async def validate_register_form(cls, register_form: RBRegistration) -> bool:
        if cls.check(username=register_form.username):
            raise HTTPException(status_code=422, detail='Пользователь с таким именем уже существует')
    