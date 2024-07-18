import asyncio
from typing import Annotated

from sqlalchemy import String, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
)


session_factory = async_sessionmaker(engine)

str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    pass
    # type_annotation_map = {
    #     str_256: String(256)
    # }
    #
    # repr_cols_num = 3
    # repr_cols = tuple()
    #
    # def __repr__(self):
    #     """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
    #     cols = []
    #     for idx, col in enumerate(self.__table__.columns.keys()):
    #         if col in self.repr_cols or idx < self.repr_cols_num:
    #             cols.append(f"{col}={getattr(self, col)}")
    #
    #     return f"<{self.__class__.__name__} {', '.join(cols)}>"
