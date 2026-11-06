"""
Pydantic schemas for authentication.
"""

from pydantic import BaseModel, ConfigDict


class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

