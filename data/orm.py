from sqlalchemy import Integer, and_, cast, func, insert, inspect, or_, select, text
from sqlalchemy.orm import aliased, contains_eager, joinedload, selectinload

from .database import engine, session_factory, Base


class ORM:
    @staticmethod
    async def create_tables():
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def insert_users(table_name, user_id, username):
        async with session_factory() as session:
            # Add new user to the database
            new_user = table_name(user_id=user_id, username = username )
            session.add(new_user)
            # flush взаимодействует с БД, поэтому пишем await
            # await session.flush()
            await session.commit()

    #
    # @staticmethod
    # async def select_users():
    #     async with session_factory() as session:
    #         query = select(User)
    #         result = await session.execute(query)
    #         users = result.scalars().all()
    #         return users

