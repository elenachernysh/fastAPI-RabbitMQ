from typing import Optional
from datetime import datetime
from pydantic import UUID4, BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserBase(BaseModel):
    id: int
    email: EmailStr
    name: str


class TokenBase(BaseModel):
    token: UUID4 = Field(..., alias="access_token")
    expires: datetime
    token_type: Optional[str] = "bearer"

    class Config:
        allow_population_by_field_name = True

    @validator("token")
    def hexlify_token(cls, value):
        return value.hex


class User(UserBase):
    token: TokenBase = {}
