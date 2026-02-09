from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import TIMESTAMP, BigInteger
from sqlalchemy.sql import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import TypeVar, Type
from app.utils.result_util import Result, Ok, Error

T = TypeVar("T", bound="BaseModel")

class BaseModel(DeclarativeBase):
    __abstract__ = True
    datetime_created: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class BaseModelWithId(BaseModel):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    @classmethod
    async def get_by_id(cls: Type[T], session: AsyncSession, id: int) -> Result[T|None, SQLAlchemyError]:
        try:
            stmt = select(cls).where(cls.id == id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            return Ok(obj)
        except SQLAlchemyError as e:
            return Error(e)


class ValueBaseModel(BaseModelWithId):
    __abstract__ = True

    @classmethod
    async def create(cls: Type[T], session: AsyncSession, value: str) -> Result[T, SQLAlchemyError]:
        try:
            new_obj = cls(value=value)
            session.add(new_obj) # caller commits
            await session.flush()
            await session.refresh(new_obj)
            return Ok(new_obj)
        except SQLAlchemyError as e:
            return Error(e)


    @classmethod
    async def get_by_value(cls: Type[T], session: AsyncSession, value: str) -> Result[T|None, SQLAlchemyError]:
        try:
            stmt = select(cls).where(cls.value == value)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            return Ok(obj)
        except SQLAlchemyError as e:
            return Error(e)
    