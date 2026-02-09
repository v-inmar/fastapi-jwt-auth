from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security_util import auth_required
from app.utils.db_util import get_transaction_session
from app.models.user import UserModel

router = APIRouter()

@router.get("/me")
async def protected(
        current_user: UserModel = Depends(auth_required), 
        session = Annotated[AsyncSession, Depends(get_transaction_session)]
    ):

    return {
        "message": "This is a protected route. Bearer access token is required",
        "payload": {
            "id": current_user.id,
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
            "pid": current_user.pid,
            "email": current_user.email
        }
    }