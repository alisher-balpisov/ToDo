from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.models import SharedAccessEnum


class ToDoSchema(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    text: str | None = Field(default=None, max_length=4096)
    completion_status: bool | None = Field(default=None)

    
class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class UserCreateSchema(BaseModel):
    username: str = Field(min_length=3, max_length=20,
                          description="Имя пользователя")
    email: EmailStr = Field(description="Email в формате user@example.com")
    password: str = Field(
        min_length=6, max_length=20, description="Пароль (6–20 символов)"
    )

    @field_validator("email")
    def email_length(cls, v):
        if len(v) > 50:
            raise ValueError("Email должен быть короче 50 символов")
        return v


class TaskShareSchema(BaseModel):
    task_id: int
    shared_with_username: str
    permission_level: SharedAccessEnum = Field(default=SharedAccessEnum.VIEW)
