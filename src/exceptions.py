from fastapi import HTTPException, status

TASK_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"msg": "Задача не найдена"}
)

TASK_NAME_REQUIRED = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={"msg": "Имя задачи не задано"}
)

FILE_EMPTY = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={"msg": "файл пуст"}
)

TASK_ACCESS_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail={"msg": "Задача не найдена или не принадлежит вам"}
)

USER_NOT_FOUND = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={"msg": f"Пользователь не найден"}
)


NO_EDIT_ACCESS = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail={"msg": "Нет доступа для редактирования задачи"}
)


def task_already_shared(username): return HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={"msg": f"Доступ к задаче уже предоставлен пользователю '{username}'"}
)


def task_not_shared_with_user(username): return HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={"msg": f"Эта задача не расшарена с пользователем {username}"}
)


LIST_EMPTY = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"msg": "Список пуст"}
)
