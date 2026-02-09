from typing import Annotated
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_util import JwtUtil
from app.utils.db_util import get_transaction_session
from app.models.user import AuthidModel, UserModel
from app.utils.result_util import Error

oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/api/auth/login",
        auto_error=True
    )
# auto_error=False if i want to customize the response errors i.e. missing "Bearer" keyword
# but for now, this is ok

class AuthRequired:

    async def __call__(
            self, 
            token: str = Depends(oauth2_scheme), 
            session: AsyncSession = Depends(get_transaction_session)
        ) -> UserModel:
        try:
            payload = JwtUtil().decode_access_token(token=token)
            if isinstance(payload, Error):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{payload.error}"
                )
             
            authid_value = payload.data.get("sub")
            if authid_value is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )
            
            authid_model_result = await AuthidModel.get_by_value(session=session, value=authid_value)
            if isinstance(authid_model_result, Error):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Server error. Try again later"
                )
            
            if authid_model_result.data is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )
            
            authid_model: AuthidModel = authid_model_result.data
            user_model: UserModel = authid_model.user

            if user_model.datetime_deactivated or user_model.datetime_deleted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )
            
            return user_model
        except Exception as e:
            # anything unexpected is caught here
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server error. Try again later"
            )


auth_required = AuthRequired()