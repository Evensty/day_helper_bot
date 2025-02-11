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
    text, func, Date, Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base, str_256
from .orm import ORM

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
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    # is_admin = Column(Boolean, default=False)

    # Связи с таблицами
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    task_text = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP(0)")
)

    # Связь с таблицей User
    user = relationship("User", back_populates="tasks")


class Link(Base):
    __tablename__ = 'links'

    link_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    link = Column(String, nullable=False)

    # Связь с таблицей User
    user = relationship("User", back_populates="links")

asyncio.run(ORM.create_tables())

