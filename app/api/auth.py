from typing import Annotated
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, status, Depends, HTTPException, Response, Form, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import (
    LoginRequestSchema, 
    SignupRequestSchema, 
    LoginResponseSchema,
    SignupResponseSchema,
    AccessToken
)

from app.models.user import UserModel, AuthidModel
from app.models.revoked_token import RevokedTokenModel
from app.utils.db_util import get_transaction_session
from app.utils.result_util import Error, Result
from app.utils.jwt_util import JwtUtil
from app.utils.bcrypt_util import BcryptUtil

router = APIRouter()

@router.post("/login", response_model=LoginResponseSchema)
async def login(
        response: Response, 
        login_data: Annotated[LoginRequestSchema, Form()], 
        session: AsyncSession = Depends(get_transaction_session)
    ):

    # check user exist
    email_check_result = await UserModel.get_by_email(session, login_data.email.lower())
    if isinstance(email_check_result, Error):
        raise HTTPException(status_code=500)
    
    if email_check_result.data is None:
        raise HTTPException(status_code=401, detail="email and/or password is invalid")
    
    user_model: UserModel = email_check_result.data
    if not BcryptUtil().verify_password(login_data.password, user_model.password):
        raise HTTPException(status_code=401, detail="email and/or password is invalid")
    
    # TODO: check if user has been deleted - Stop login
    # TODO: check if user was deactivated - Reactivate user
    
    jwt_util = JwtUtil()
    access_token_result = jwt_util.generate_access_token(authid_value=user_model.authid.value)
    if isinstance(access_token_result, Error):
        raise HTTPException(status_code=500, detail="Unable to create access token.")
    
    refresh_token_result = jwt_util.generate_refresh_token(authid_value=user_model.authid.value)
    if isinstance(refresh_token_result, Error):
        raise HTTPException(status_code=500, detail="Unable to create refresh token.")
    
    AccessToken(
        access=access_token_result.data
    )

    

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_result.data,
        httponly=True,           # JS cannot read it
        secure=False,             # HTTPS only (True in prod)
        samesite="lax",          # or "strict"
        max_age=60 * 60 * 24 * 7,  # 7 days in seconds
        path="/api/auth/"
    )

    return LoginResponseSchema(
        payload=AccessToken(
            access=access_token_result.data
        ),
        code=status.HTTP_200_OK
    )


@router.post("/signup", response_model=SignupResponseSchema)
async def signup(response: Response, signup_data: SignupRequestSchema, session: AsyncSession = Depends(get_transaction_session)):

    email_check_result = await UserModel.get_by_email(session, signup_data.email.lower())
    if isinstance(email_check_result, Error):
        raise HTTPException(status_code=500)
    
    if email_check_result.data is not None:
        raise HTTPException(status_code=409, detail="Email address already in use")

    new_user_result = await UserModel.create(session, signup_data)
    if isinstance(new_user_result, Error):
        raise HTTPException(status_code=500)
    
    
    user_model: UserModel = new_user_result.data

    jwt_util = JwtUtil()

    access_token_result = jwt_util.generate_access_token(authid_value=user_model.authid.value)
    if isinstance(access_token_result, Error):
        raise HTTPException(status_code=500, detail="Unable to create access token. Please try to login.")
    
    refresh_token_result = jwt_util.generate_refresh_token(authid_value=user_model.authid.value)
    if isinstance(refresh_token_result, Error):
        raise HTTPException(status_code=500, detail="Unable to create refresh token. Please try to login.")


    response.set_cookie(
        key="refresh_token",
        value=refresh_token_result.data,
        httponly=True,           # JS cannot read it
        secure=False,             # HTTPS only (in prod)
        samesite="lax",          # or "strict"
        max_age=60 * 60 * 24 * 7,  # 7 days in seconds
        path="/api/auth/"
    )

    return SignupResponseSchema(
        payload=AccessToken(
            access=access_token_result.data
        ),
        code=status.HTTP_201_CREATED
    )


@router.post("/logout")
async def logout(
        refresh_token: str | None = Cookie(None),
        session: AsyncSession = Depends(get_transaction_session)
    ):

    # this helps with user experience.
    # no cookie, nothing to revoke, logout successful
    if refresh_token is None:
        return {
            "payload": {
                "message": "Logout successful"
            },
            "code": status.HTTP_200_OK
        }
    

    decode_result = JwtUtil().decode_refresh_token(token=refresh_token)
    if isinstance(decode_result, Error): # expired token will also hit this
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{decode_result.error}"
        )
    
    revoked_token_result = await RevokedTokenModel.get_by_value(
        session=session,
        value=refresh_token
    )

    if isinstance(revoked_token_result, Error):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error. Try again later"
        )
    
    if revoked_token_result.data is not None: # already in db, nothing more to revoke.

        return {
            "payload": {
                "message": "Logout successful"
            },
            "code": status.HTTP_200_OK
        }
    
    # Everything checks out, revoke token
    
    # since refresh token's life is 7 days from creation
    # ttl is 8 days whether refresh token's life is still 7 days or 7 seconds left
    # this ensures that refresh token had already expired before it gets cleanup from the database
    ttl = datetime.now(timezone.utc) + timedelta(days=8)

    new_revoked_token_result = await RevokedTokenModel.create(
        session=session,
        value=refresh_token,
        ttl=ttl
    )

    if isinstance(new_revoked_token_result, Error):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error. Try again later"
        )
    
    
    return {
        "payload": {
            "message": "Logout successful"
        },
        "code": status.HTTP_200_OK
    }


@router.post("/refresh")
async def refresh(
        response: Response,
        refresh_token: str | None = Cookie(None),
        session: AsyncSession = Depends(get_transaction_session)
    ):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid refresh token"
        )
    
    decode_result = JwtUtil().decode_refresh_token(token=refresh_token)
    if isinstance(decode_result, Error): # expired token will also hit this
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{decode_result.error}"
        )
    
    revoked_token_result = await RevokedTokenModel.get_by_value(
        session=session,
        value=refresh_token
    )

    if isinstance(revoked_token_result, Error):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error. Try again later"
        )
    
    # if it is already in db
    if revoked_token_result.data is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid refresh token"
        )
    
    # get user 
    payload: dict = decode_result.data
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid refresh token"
        )
    
    authid_result = await AuthidModel.get_by_value(
        session=session,
        value=sub
    )
    if isinstance(authid_result, Error):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error. Try again later"
        )
    
    if authid_result.data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid refresh token"
        )
    
    user_model: UserModel = authid_result.data.user
    if user_model.datetime_deactivated or user_model.datetime_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid refresh token"
        )
    
    # create new access and refresh token
    jwt_util = JwtUtil()
    access_token_result = jwt_util.generate_access_token(authid_value=user_model.authid.value)
    if isinstance(access_token_result, Error):
        raise HTTPException(status_code=500, detail="Unable to create access token.")
    
    refresh_token_result = jwt_util.generate_refresh_token(authid_value=user_model.authid.value)
    if isinstance(refresh_token_result, Error):
        raise HTTPException(status_code=500, detail="Unable to create refresh token.")
    
    # revoke old refresh token
    ttl = datetime.now(timezone.utc) + timedelta(days=8)

    new_revoked_token_result = await RevokedTokenModel.create(
        session=session,
        value=refresh_token,
        ttl=ttl
    )

    if isinstance(new_revoked_token_result, Error):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error. Try again later"
        )
    
    AccessToken(
        access=access_token_result.data
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_result.data,
        httponly=True,           # JS cannot read it
        secure=False,             # HTTPS only (True in prod)
        samesite="lax",          # or "strict"
        max_age=60 * 60 * 24 * 7,  # 7 days in seconds
        path="/api/auth/"
    )

    return LoginResponseSchema(
        payload=AccessToken(
            access=access_token_result.data
        ),
        code=status.HTTP_200_OK
    )