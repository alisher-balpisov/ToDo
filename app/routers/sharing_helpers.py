from fastapi import HTTPException

from app.db.models import session, ToDo, User, TaskShare


def get_owned_task(task_id: int, current_user: User) -> None | HTTPException:
    task = session.query(ToDo).filter(
        ToDo.id == task_id,
        ToDo.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или вам не принадлежит")


def get_existing_user(username: str) -> User | HTTPException:
    shared_with_user = session.query(User).filter(User.username == username).first()
    if not shared_with_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return shared_with_user


def get_shared_access(task_id: int, current_user: User, shared_with_user: User) -> TaskShare | HTTPException:
    share = session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.owner_id == current_user.id,
        TaskShare.shared_with_id == shared_with_user.id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="Доступ не найден")
    return share
