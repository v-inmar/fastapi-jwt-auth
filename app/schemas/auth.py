from typing_extensions import Self
from pydantic import Field, BaseModel, EmailStr, model_validator, field_validator
from app.constants import NAME_MAX_LENGTH, NAME_MIN_LENGTH

class SignupRequestSchema(BaseModel):
    firstname: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH, example="John")
    lastname: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH, example="Doe")
    email: EmailStr = Field(..., min_length=5, max_length=255, example="john.doe@email.com")
    password: str = Field(..., min_length=8, max_length=72, example="strongpassword123")
    repeat: str = Field(..., min_length=8, example="strongpassword123")

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.repeat:
            raise ValueError('Passwords do not match')
        return self
    

    @model_validator(mode='before')
    @classmethod
    def strip_and_check(cls, data: dict) -> dict:
        if len(data["firstname"].strip()) < NAME_MIN_LENGTH:
            raise ValueError(f"firstname length must be inbetween {NAME_MIN_LENGTH} and {NAME_MAX_LENGTH} characters long.")
        
        if len(data["lastname"].strip()) < NAME_MIN_LENGTH:
            raise ValueError(f"lastname length must be inbetween {NAME_MIN_LENGTH} and {NAME_MAX_LENGTH} characters long.")
        
        return data
    
    

    



class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str

class AccessToken(BaseModel):
    access: str


class LoginResponseSchema(BaseModel):
    payload: AccessToken
    code: int

class SignupResponseSchema(LoginResponseSchema):
    pass