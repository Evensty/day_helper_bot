import asyncio
import datetime
import enum
from typing import Annotated, Optional

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base, str_256
from .orm import AsyncORM

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(
    server_default=text("TIMEZONE('utc', now())"),
    onupdate=datetime.datetime.now,
)]


# class WorkersOrm(Base):
#     __tablename__ = "workers"
#
#     id: Mapped[intpk]
#     username: Mapped[str]



    # resumes: Mapped[list["ResumesOrm"]] = relationship(
    #     back_populates="worker",
    # )
    #
    # resumes_parttime: Mapped[list["ResumesOrm"]] = relationship(
    #     back_populates="worker",
    #     primaryjoin="and_(WorkersOrm.id == ResumesOrm.worker_id, ResumesOrm.workload == 'parttime')",
    #     order_by="ResumesOrm.id.desc()",
    # )

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    # name = Column(String, nullable=False)
    # tasks = relationship()

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True)
    # user_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    task_text = Column(String, nullable=False)


asyncio.run(AsyncORM.create_tables())

