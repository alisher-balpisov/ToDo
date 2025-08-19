import factory
from factory.alchemy import SQLAlchemyModelFactory

from src.auth.models import ToDoUser
from src.common.models import Task
from src.sharing.models import Share, SharedAccessEnum


class UserFactory(SQLAlchemyModelFactory):
    """Фабрика для создания тестовых пользователей."""

    class Meta:
        model = ToDoUser
        sqlalchemy_session_persistence = "commit"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.LazyFunction(
        lambda: ToDoUser().set_password("Password123"))
    disabled = False


class TaskFactory(SQLAlchemyModelFactory):
    """Фабрика для создания тестовых задач."""

    class Meta:
        model = Task
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Task {n}")
    text = factory.Faker("text", max_nb_chars=200)
    completion_status = False
    user_id = factory.SubFactory(UserFactory)


class ShareFactory(SQLAlchemyModelFactory):
    """Фабрика для создания тестовых шар."""

    class Meta:
        model = Share
        sqlalchemy_session_persistence = "commit"

    task_id = factory.SubFactory(TaskFactory)
    owner_id = factory.SubFactory(UserFactory)
    target_user_id = factory.SubFactory(UserFactory)
    permission_level = SharedAccessEnum.view
