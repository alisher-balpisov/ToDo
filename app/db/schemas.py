from pydantic import BaseModel, Field


class ToDoSchema(BaseModel):
    name: str = Field(max_length=20)
    text: str = Field(max_length=4096)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
