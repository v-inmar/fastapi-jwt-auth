from __future__ import annotations
from datetime import datetime
from app.models.base import ValueBaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select
from sqlalchemy import String, DateTime
from app.utils.result_util import Result, Ok, Error

class RevokedTokenModel(ValueBaseModel):
    __tablename__ = "revoked_token_model"
    value: Mapped[str] = mapped_column(String(2048))
    datetime_ttl: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @classmethod
    async def create(cls: RevokedTokenModel, session: AsyncSession, value: str, ttl: datetime) -> Result[RevokedTokenModel, SQLAlchemyError]:
        try:
            new_obj = cls(value=value, datetime_ttl=ttl)
            session.add(new_obj)
            await session.flush()
            await session.refresh(new_obj)
            return Ok(new_obj)
        except SQLAlchemyError as e:
            return Error(e)


