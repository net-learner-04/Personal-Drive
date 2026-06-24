from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    name: str
    passwd1: str
    passwd2: str
    email: EmailStr


    @field_validator('name', 'passwd1', 'passwd2', 'email')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Blank entries are not allowed.")
        return v
    

    @field_validator('passwd2')
    def passwd_check(cls, v, info:FieldValidationInfo):
        if 'passwd1' in info.data and v != info.data['passwd1']:
            raise ValueError("Password does not match.")
        return v