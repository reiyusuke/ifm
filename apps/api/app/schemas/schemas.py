from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Literal["SELLER", "BUYER"] = "SELLER"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class IdeaIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(min_length=3)
    body: str = Field(min_length=3)
    price: float = 0
    resale_allowed: bool = False
    exclusive_option_price: Optional[float] = None

class IdeaOut(BaseModel):
    id: int
    seller_id: int
    title: str
    summary: str
    body: str
    price: float
    resale_allowed: bool
    exclusive_option_price: Optional[float]
    status: str

class ScoreIn(BaseModel):
    logic: int = Field(ge=0, le=20)
    originality: int = Field(ge=0, le=20)
    market: int = Field(ge=0, le=20)
    concreteness: int = Field(ge=0, le=20)
    extensibility: int = Field(ge=0, le=20)
