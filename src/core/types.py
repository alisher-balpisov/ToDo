from typing import Annotated

from fastapi import Depends, File, Path, UploadFile
from pydantic import BeforeValidator
from sqlalchemy.orm import Session

from src.auth.models import User
from src.auth.service import get_current_user
from src.common.constants import USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH
from src.core.database import get_db

PrimaryKey = Annotated[int, Path(gt=0, lt=2147483647)]
DbSession = Annotated[Session, Depends(get_db)]
UsernameStr = Annotated[str, BeforeValidator(
    lambda x: str.strip(x)), Path(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)]
UploadedFile = Annotated[UploadFile, File()]
CurrentUser = Annotated[User, Depends(get_current_user)]
