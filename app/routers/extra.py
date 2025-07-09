from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from app.db.models import session, ToDo, User, TaskShare
from app.db.schemas import TaskShareSchema
from app.auth.jwt_handler import get_current_active_user
from app.routers.crud import handle_exception

router = APIRouter(prefix="/tasks")


@router.get("/search/")
def search_tasks(search_query: str, current_user: User = Depends(get_current_active_user)):
    try:
        tasks = session.query(ToDo).filter(
            or_(
                ToDo.name.ilike(f"%{search_query}%"),
                ToDo.text.ilike(f"%{search_query}%")
            )
        ).filter(ToDo.user_id == current_user.id).all()
        return [
            {
                'id': task.id, 'task_name': task.name,
                'completion_status': task.completion_status,
                'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
                'text': task.text
            } for task in tasks
        ]
    except Exception as e:
        handle_exception(e, "Ошибка сервера при поиске задачи")


@router.get("/stats")
def get_tasks_stats(current_user: User = Depends(get_current_active_user)):
    try:
        query = session.query(ToDo).filter(ToDo.user_id == current_user.id)

        total = query.count()
        completed = query.filter(ToDo.completion_status == True).count()
        uncompleted = query.filter(ToDo.completion_status == False).count()
        completion_percentage = round((completed / total) * 100 if total > 0 else 0, 2)
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "uncompleted_tasks": uncompleted,
            "completion_percentage": completion_percentage
        }
    except Exception as e:
        handle_exception(e, "Ошибка сервера при выводе статистики")


@router.post("/share")
def share_task(
        share_data: TaskShareSchema,
        current_user: User = Depends(get_current_active_user)
):
    try:
        # Проверяем, что задача существует и принадлежит текущему пользователю
        task = session.query(ToDo).filter(
            ToDo.id == share_data.task_id,
            ToDo.user_id == current_user.id
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена или вам не принадлежит")

        # Проверяем, что пользователь, с которым делимся, существует
        shared_with_user = session.query(User).filter(
            User.username == share_data.shared_with_username
        ).first()
        if not shared_with_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Проверяем, что не делимся с самим собой
        if shared_with_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Нельзя поделиться задачей с самим собой")

        # Проверяем, что такой доступ уже не предоставлен
        existing_share = session.query(TaskShare).filter(
            TaskShare.task_id == share_data.task_id,
            TaskShare.shared_with_id == shared_with_user.id
        ).first()
        if existing_share:
            raise HTTPException(status_code=400, detail="Доступ уже предоставлен этому пользователю")

        # Создаем запись о совместном доступе
        new_share = TaskShare(
            task_id=share_data.task_id,
            owner_id=current_user.id,
            shared_with_id=shared_with_user.id,
            permission_level=share_data.permission_level
        )
        session.add(new_share)
        session.commit()

        return {"message": "Задача успешно расшарена с пользователем"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка при предоставлении доступа к задаче")


@router.get("/shared")
def get_shared_tasks(current_user: User = Depends(get_current_active_user)):
    try:
        # Задачи, которые расшарили с текущим пользователем
        shared_tasks = session.query(ToDo).join(
            TaskShare,
            TaskShare.task_id == ToDo.id
        ).filter(
            TaskShare.shared_with_id == current_user.id
        ).all()

        return [
            {
                'id': task.id,
                'task_name': task.name,
                'completion_status': task.completion_status,
                'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
                'text': task.text,
                'owner_username': session.query(User.username).filter(User.id == task.user_id).scalar(),
                'permission_level': session.query(TaskShare.permission_level).filter(
                    TaskShare.task_id == task.id,
                    TaskShare.shared_with_id == current_user.id
                ).scalar()
            } for task in shared_tasks
        ]
    except Exception as e:
        handle_exception(e, "Ошибка при получении расшаренных задач")


@router.delete("/unshare")
def unshare_task(
        task_id: int,
        username: str,
        current_user: User = Depends(get_current_active_user)
):
    try:
        # Проверяем, что задача принадлежит текущему пользователю
        task = session.query(ToDo).filter(
            ToDo.id == task_id,
            ToDo.user_id == current_user.id
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена или вам не принадлежит")

        # Находим пользователя, с которым нужно прекратить делиться
        shared_with_user = session.query(User).filter(
            User.username == username
        ).first()
        if not shared_with_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Удаляем запись о совместном доступе
        share = session.query(TaskShare).filter(
            TaskShare.task_id == task_id,
            TaskShare.owner_id == current_user.id,
            TaskShare.shared_with_id == shared_with_user.id
        ).first()

        if not share:
            raise HTTPException(status_code=404, detail="Доступ не найден")

        session.delete(share)
        session.commit()

        return {"message": "Доступ к задаче успешно отозван"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка при отзыве доступа к задаче")


@router.put("/share/update")
def update_share_permission(
        task_id: int,
        username: str,
        new_permission: str = Query(pattern='^(view|edit)$'),
        current_user: User = Depends(get_current_active_user)
):
    try:
        # Проверяем, что задача принадлежит текущему пользователю
        task = session.query(ToDo).filter(
            ToDo.id == task_id,
            ToDo.user_id == current_user.id
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена или вам не принадлежит")

        # Находим пользователя
        shared_with_user = session.query(User).filter(
            User.username == username
        ).first()
        if not shared_with_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Находим запись о совместном доступе
        share = session.query(TaskShare).filter(
            TaskShare.task_id == task_id,
            TaskShare.owner_id == current_user.id,
            TaskShare.shared_with_id == shared_with_user.id
        ).first()

        if not share:
            raise HTTPException(status_code=404, detail="Доступ не найден")

        # Обновляем уровень доступа
        share.permission_level = new_permission
        session.commit()

        return {"message": "Уровень доступа успешно обновлен"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка при обновлении уровня доступа")
