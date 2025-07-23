# ToDo приложение на FastAPI

## Описание
Простое ToDo приложение с возможностью:
- Создания/удаления задач
- Аутентификации пользователей (JWT)
- Совместного доступа к задачам

## Технологии
- Python 3.13+
- FastAPI
- SQLAlchemy (PostgreSQL)
- JWT аутентификация
- Uvicorn сервер

## Установка и запуск

1. Клонировать репозиторий:
```bash
git clone https://github.com/alisher-balpisov/ToDo.git
cd ToDo
```

2. Установить зависимости:
```
pip install -r requirements.txt
```

3. Настроить переменные окружения (создать файл `.env`):
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
```

4. Запустить приложение:
```
uvicorn app.main:app --reload
```

## API документация
После запуска приложения документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## Конфигурация Docker
Для запуска через Docker:
```bash
docker-compose up --build
```
