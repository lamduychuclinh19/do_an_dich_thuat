from pydantic import BaseModel, Field


class AdminLogin(BaseModel):
    username: str = Field(min_length=4)
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"