from pydantic import BaseModel, Field, EmailStr, validator, field_validator
import re


class ToDoSchema(BaseModel):
    name: str = Field(max_length=20)
    text: str = Field(max_length=4096)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20, description="Имя пользователя")
    email: EmailStr = Field(description="Email в формате user@example.com")
    password: str = Field(min_length=6, max_length=20, description="Пароль (6–20 символов)")

    @field_validator("email")
    @classmethod
    def email_length(cls, v):
        if len(v) > 50:
            raise ValueError("Email должен быть короче 50 символов")
        return v
