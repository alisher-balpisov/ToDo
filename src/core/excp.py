from fastapi import HTTPException, status

from src.core.config import settings

# TASK_NOT_FOUND = HTTPException(
#     status_code=status.HTTP_404_NOT_FOUND,
#     detail={"msg": "Задача не найдена"}
# )

# TASK_NAME_REQUIRED = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "Имя задачи не задано"}
# )

# FILE_EMPTY = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "файл пуст"}
# )

# TASK_ACCESS_FORBIDDEN = HTTPException(
#     status_code=status.HTTP_403_FORBIDDEN,
#     detail={"msg": "Задача не найдена или не принадлежит вам"}
# )

# USER_NOT_FOUND = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": f"Пользователь не найден"}
# )


# NO_EDIT_ACCESS = HTTPException(
#     status_code=status.HTTP_403_FORBIDDEN,
#     detail={"msg": "Нет доступа для редактирования задачи"}
# )


# def task_already_shared(username):
#     return HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail={"msg": f"Доступ к задаче уже предоставлен пользователю '{username}'"}
#     )


# def task_not_shared_with_user(username):
#     return HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail={"msg": f"Эта задача не расшарена с пользователем {username}"}
#     )


# LIST_EMPTY = HTTPException(
#     status_code=status.HTTP_404_NOT_FOUND,
#     detail={"msg": "Список пуст"}
# )

# USER_DATA_ERROR = HTTPException(
#     status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#     detail={
#         "msg": "Пользователь с такими данными уже существует или введенные данные некорректны."},
# )

# INVALID_TOKEN = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail={"msg": "Недействительный токен"}
# )

# EXPIRED_TOKEN = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail={"msg": "Токен истек"}
# )
# FUTURE_TOKEN = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail={"msg": "Токен выдан в будущем"}
# )
# INVALID_TOKEN_STRUCTURE = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail={"msg": "Некорректная структура токена"}
# )

# INVALID_CREDENTIALS = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail={"msg": "Неверное имя пользователя или пароль"},
#     headers={"WWW-Authenticate": "Bearer"},
# )
# USER_DISABLED = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail={"msg": "Учетная запись пользователя отключена"}
# )

# INVALID_CURRENT_PASSWORD = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "Неверный текущий пароль"},
# )
# FILE_NAME_MISSING = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "Файл не имеет имени"},
# )

# INVALID_FILE_NAME = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "Недопустимое имя файла"},
# )


# INVALID_FILE_EXTENSION = HTTPException(
#     status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#     detail={"msg": f"Недопустимое расширение файла"},
# )


# INVALID_FILE_TYPE = HTTPException(
#     status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#     detail={"msg": f"Недопустимый тип файла"},
# )


# FILE_TOO_LARGE = HTTPException(
#     status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#     detail={
#         "msg": f"Размер файла превышает максимально допустимый ({settings.MAX_FILE_SIZE_MB}MB)"
#     },
# )


# def SESSION_ARGUMENT_MISSING(func) -> ValueError:
#     return ValueError(
#         f"[transactional] В функции '{func.__name__}' не найден аргумент 'session'. "
#         f"Передайте его как первый позиционный аргумент или keyword-аргумент."
#     )


# def INVALID_SESSION_TYPE(func, session) -> TypeError:
#     return TypeError(
#         f"[transactional] В функции '{func.__name__}' ожидается объект класса 'Session', "
#         f"но получен {type(session).__name__}."
#     )


# TASK_SELF_ACCESS_CHANGE = HTTPException(
#     status_code=status.HTTP_403_FORBIDDEN,
#     detail={"msg": "Нельзя изменять доступ к своей собственной задаче"}
# )


# def TASK_PERMISSION_ALREADY_SET(permission):
#     return HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail={"msg": f"permission_level уже {permission.value}"}
#     )


# TASK_NO_EDIT_ACCESS = HTTPException(
#     status_code=status.HTTP_403_FORBIDDEN,
#     detail={"msg": "Нет доступа для редактирования задачи"}
# )

# TASK_SHARE_WITH_SELF = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "Нельзя делиться задачей с самим собой"}
# )

# TASK_QUERY_TOO_LONG = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail={"msg": "Слишком длинный поисковый запрос"}
# )

# PASSWORD_TOO_SHORT = ValueError(
#     f"Длина пароля должна быть не менее {settings.PASSWORD_MIN_LENGTH} символов")
# PASSWORD_HAS_SPACES = ValueError("Пароль не должен содержать пробелы")
# PASSWORD_NO_DIGIT = ValueError("Пароль должен содержать хотя бы одну цифру")
# PASSWORD_NO_UPPER = ValueError(
#     "Пароль должен содержать хотя бы одну заглавную букву")
# PASSWORD_NO_LOWER = ValueError(
#     "Пароль должен содержать хотя бы одну строчную букву")
# NEW_PASSWORD_NOT_PROVIDED = ValueError("Вы не ввели новый пароль")
# PASSWORD_CURRENT_REQUIRED = ValueError("Требуется текущий пароль")
# PASSWORD_CONFIRM_REQUIRED = ValueError("Подтвердите новый пароль")
# PASSWORD_CONFIRM_MISMATCH = ValueError(
#     "new_password и confirm_password не совпадают")
# PASSWORD_SAME_AS_OLD = ValueError("Новый пароль не должен совпадать с текущим")


# def TOKEN_TYPE_MISMATCH(expected_type, resulting_type):
#     return HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail={
#             "msg": f"Ожидался токен типа '{expected_type}', получен '{resulting_type}'"}
#     )


# def USER_LOCKED(user):
#     return HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail={"msg": f"Учётная запись временно заблокирована \
#                   до {user.locked_until.isoformat()}"},
#     )


# def MUTUALLY_EXCLUSIVE_PARAMS(a, b):
#     return ValueError(
#         f"Нельзя использовать одновременно '{a}' и '{b}'")
