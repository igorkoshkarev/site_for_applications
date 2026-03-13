from sqlalchemy import select, inspect, or_
from app.database import async_session_maker


class BaseDAO:
    model = None

    @classmethod
    async def get_one(cls, **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter)
            result = await session.execute(query)
            result = result.scalar()
            if not result:
                raise ValueError(f'В модели {repr(cls.model)} нет такой строки.')
            return result
        
    @classmethod
    async def get_all(cls, **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter)
            result = await session.execute(query)
            result = result.scalars().all()
            if not result:
                raise ValueError(f'В модели {repr(cls.model)} нет таких строк.')
            return result
        
    @classmethod
    async def get_all_with_limit(cls, limit, offset, **filter):
        filter = cls._clear_filter(**filter)
        async with async_session_maker() as session:
            query = select(cls.model) \
                .filter(await cls._create_search_condition(**filter)) \
                .limit(limit) \
                .offset(offset)
            result = await session.execute(query)
            result = result.scalars().all()
            if not result:
                raise ValueError(f'В модели {repr(cls.model)} нет таких строк.')
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
    def _clear_filter(cls, **filter):
        filter_copy = filter.copy()
        for key, param in filter.items():
            if param is None or param == '':
                filter_copy.pop(key)
        return filter_copy
    
    @classmethod
    async def _create_search_condition(cls, **filter):
        mapper = inspect(cls.model)
        query = []
        for k, v in filter.items():
            query.append(mapper.columns[k].contains(v))
        return or_(*query)