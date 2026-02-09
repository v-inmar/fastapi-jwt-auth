import jwt
import datetime
from enum import Enum
from app.config import get_config
from app.utils.result_util import Result, Ok, Error

class JwtType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"

class JwtUtil:

    def _generate_token(self, key: str, sub: str, exp: datetime.datetime, token_type: JwtType) -> Result[str, Exception]:
        try:
            payload = {
                "sub": sub,
                "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
                "exp": int(exp.timestamp()),
                "token_type": token_type.value
            }

            token = jwt.encode(payload=payload, algorithm=get_config().ALGORITHM, key=key)
            return Ok(token)
        except Exception as e:
            return Error(e)
        
    def _decode_token(self, key: str, token: str, token_type: JwtType) -> Result[dict, Exception]:
        try:
            payload = jwt.decode(
                token,
                key=key,
                algorithms=[get_config().ALGORITHM],
                options={"verify_exp": True},  # ensure `exp` is checked
            )

            if payload["token_type"] != token_type.value:
                raise ValueError(f"Expected {token_type.value}, got {payload["token_type"]}")
            
            return Ok(payload)
        except Exception as e:
            return Error(e)
    
    def generate_access_token(self, authid_value: str) -> Result[str, Exception]:
        try:
            secret = get_config().JWT_ACCESS_SECRET
            exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=get_config().ACCESS_TOKEN_EXPIRE_MINUTES)
            token_type = JwtType.ACCESS

            token = self._generate_token(
                key=secret,
                sub=authid_value,
                exp=exp,
                token_type=token_type
            ).unwrap_or_raise()
            return Ok(token)
        except Exception as e:
            return Error(e)
    
    def generate_refresh_token(self, authid_value: str) -> Result[str, Exception]:
        try:
            secret = get_config().JWT_REFRESH_SECRET
            exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=get_config().REFRESH_TOKEN_EXPIRE_DAYS)
            token_type = JwtType.REFRESH
            token = self._generate_token(
                key=secret,
                sub=authid_value,
                exp=exp,
                token_type=token_type
            ).unwrap_or_raise()
            return Ok(token)
        except Exception as e:
            return Error(e)
    

    def decode_access_token(self, token: str) -> Result[dict, Exception]:
        try:
            payload = self._decode_token(
                key=get_config().JWT_ACCESS_SECRET,
                token=token,
                token_type=JwtType.ACCESS
            ).unwrap_or_raise()

            return Ok(payload)
        except Exception as e:
            return Error(e)
        
    
    def decode_refresh_token(self, token: str) -> Result[dict, Exception]:
        try:
            payload = self._decode_token(
                key=get_config().JWT_REFRESH_SECRET,
                token=token,
                token_type=JwtType.REFRESH
            ).unwrap_or_raise()

            return Ok(payload)
        except Exception as e:
            return Error(e)