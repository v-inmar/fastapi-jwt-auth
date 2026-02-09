from __future__ import annotations
from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.models.base import BaseModelWithId, ValueBaseModel
from app.constants import (
    PID_MAX_LENGTH, PID_MIN_LENGTH,
    AUTHID_MAX_LENGTH, AUTHID_MIN_LENGTH,
    EMAIL_MAX_LENGTH, 
    NAME_MAX_LENGTH
)
from app.schemas.auth import SignupRequestSchema
from app.utils.result_util import Result, Ok, Error
from app.utils.string_util import StringUtil
from app.utils.bcrypt_util import BcryptUtil

# postgresql is case sensitive A != a

class AuthidModel(ValueBaseModel):
    __tablename__ = "authid_model"

    value: Mapped[str] = mapped_column(String(AUTHID_MAX_LENGTH), nullable=False, unique=True)
    datetime_ttl: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationship 1-to-1
    user: Mapped["UserModel | None"] = relationship(
        "UserModel", 
        back_populates="authid",
        uselist=False,
        lazy="selectin",
        single_parent=True  # Ensures only one user per authid
    )


class UserModel(BaseModelWithId):
    __tablename__ = "user_model"
    
    firstname: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH),nullable=False) 
    lastname: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    pid: Mapped[str] = mapped_column(String(PID_MAX_LENGTH), nullable=False, unique=True)
    
    datetime_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    datetime_deleted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    datetime_deactivated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    authid_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("authid_model.id"), 
        nullable=False, 
        unique=True
    )
    
    # relationship 1-to-1
    authid: Mapped["AuthidModel"] = relationship(
        back_populates="user",
        single_parent=True,
        lazy="selectin"
    )

    

    @classmethod
    async def create(cls: UserModel, session: AsyncSession, data: SignupRequestSchema) -> Result[UserModel, SQLAlchemyError]:
        try:

            string_util = StringUtil()
            
            # pid
            counter = 0
            while True:
                if counter > 4:
                    raise ValueError("Try limit has been reached trying to generate random value for pid.")
                
                counter += 1

                pid_value_result = string_util.generate_random(min_length=PID_MIN_LENGTH, max_length=PID_MAX_LENGTH)
                if isinstance(pid_value_result, Error):
                    raise ValueError(f"Unable to generate random string as pid value. {pid_value_result.error}")
                
                pid_user_result = await cls.get_by_pid(session, pid_value_result.data)
                if isinstance(pid_user_result, Error):
                    raise ValueError(f"Unable to determine availability of pid value: {pid_value_result.data}. {pid_user_result.error}")
                
                if pid_user_result.data is not None:
                    continue
                else:
                    break
                

            # authid
            counter = 0
            while True:
                if counter > 4:
                    raise ValueError("Try limit has been reached trying to create new authid.")
                
                counter += 1

                authid_value_result = string_util.generate_random(min_length=AUTHID_MIN_LENGTH, max_length=AUTHID_MAX_LENGTH)
                if isinstance(authid_value_result, Error):
                    raise ValueError(f"Unable to generate random string as authid value. {authid_value_result.error}")
                
                authid_result = await AuthidModel.get_by_value(session=session, value=authid_value_result.data)
                if isinstance(authid_result, Error):
                    raise ValueError(f"Unable to determine availability of authid value: {authid_value_result.data}. {authid_result.error}")
                
                if authid_result.data is not None:
                    continue
                else:
                    new_authid_result = await AuthidModel.create(session=session, value=authid_value_result.data)
                    if isinstance(new_authid_result, Error):
                        raise ValueError(f"Unable to create new authid. {new_authid_result.error}")
                    else:
                        await session.flush(new_authid_result.data)
                        break
        
            # hash password
            hashed = BcryptUtil().hash_password(data.password)
            new_user = cls(
                firstname=data.firstname.title(),
                lastname=data.lastname.title(),
                email=data.email.lower(),
                pid=pid_value_result.data,
                authid_id=new_authid_result.data.id,
                password=hashed
            )

            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            return Ok(new_user)
        except Exception as e:
            return Error(e)


    @classmethod
    async def get_by_email(cls: UserModel, session: AsyncSession, email: str) -> Result[UserModel|None, SQLAlchemyError]:
        try:
            stmt = select(cls).where(cls.email == email.strip().lower())
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return Ok(user)
        except SQLAlchemyError as e:
            return Error(e)
    

    @classmethod
    async def get_by_pid(cls: UserModel, session: AsyncSession, pid: str) -> Result[UserModel|None, SQLAlchemyError]:
        try:
            stmt = select(cls).where(cls.pid == pid.strip())
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return Ok(user)
        except SQLAlchemyError as e:
            return Error(e)


