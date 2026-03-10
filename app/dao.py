from sqlalchemy import select

from app.database import async_session_maker


class BaseDAO:
    model = None

    @classmethod
    async def get_one(cls, **kwargs):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**kwargs)
            result = await session.execute(query)
            result = result.scalar()
            if not result:
                raise ValueError(f'В модели {repr(cls.model)} нет такой строки.')
            return result
        
    @classmethod
    async def get_all(cls, **kwargs):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**kwargs)
            result = await session.execute(query)
            result = result.scalars().all()
            print(result)
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
            