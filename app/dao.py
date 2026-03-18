from sqlalchemy import select, inspect, or_, and_
from sqlalchemy.orm import selectinload
from app.database import async_session_maker


class BaseDAO:
    model = None

    relationships = []

    @classmethod
    async def get_one(cls, columns=[], **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = await cls._create_select_query(**filter)
            result = await session.execute(query)
            result = result.scalar()
            result = await cls._format_result(result, columns)
            return result
        
    @classmethod
    async def get_all(cls, columns=[], **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = await cls._create_select_query(**filter)
            result = await session.execute(query)
            result = result.scalars().all()
            result = await cls._format_result(result, columns)
            return result
        
    @classmethod
    async def get_all_with_limit(cls, limit, offset, columns=[], **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = await cls._create_select_query(**filter)
            query = query.limit(limit).offset(offset)
            result = await session.execute(query)
            result = result.scalars().all()
            result = await cls._format_result(result, columns)
            return result

    @classmethod
    async def check(cls, **kwargs):
        try:
            await cls.get_one(**kwargs)
        except ValueError:
            return False
        else:
            return True
        
    @classmethod
    async def create(cls, **kwargs):
        async with async_session_maker() as session:
            user = cls.model(**kwargs)
            session.add(user)
            await session.commit()
    
    @classmethod
    async def _create_select_query(cls, **filter):
        query = select(cls.model) \
                .filter(await cls._create_search_condition(**filter))
        if cls.relationships:
            query = query.options(*[selectinload(r) for r in cls.relationships])
        return query
    
    @classmethod
    async def _format_result(cls, result, columns=[]):
        if not result:
            raise ValueError(f'В модели {repr(cls.model)} нет таких строк.')
        if columns:
            return [{c: getattr(r, c) for c in columns} for r in result]
        return result
    
    @classmethod
    def _clear_filter(cls, **filter):
        filter_copy = filter.copy()
        for key, param in filter.items():
            if param is None or param == '' or param == 'None':
                filter_copy.pop(key)
        return filter_copy
    
    @classmethod
    async def _create_search_condition(cls, **filter):
        mapper = inspect(cls.model)
        query = []
        for k, v in filter.items():
            if type(v) == str:
                query.append(mapper.columns[k].contains(v))
            elif type(v) == int:
                query.append(mapper.columns[k] == v)
        return and_(*query)