# 🚀 Todo API

> **Масштабируемый REST API для управления задачами с продвинутыми функциями совместной работы**

Enterprise-grade приложение для управления задачами, построенное на современном Python стеке с акцентом на безопасность, производительность и масштабируемость.

## ✨ **Ключевые особенности**

### 🔐 **Безопасность & Аутентификация**
- **JWT токены** с refresh механизмом
- **Защита от брутфорса** (account lockout)
- **Безопасное хеширование паролей** (bcrypt с настраиваемыми rounds)
- **Rate limiting** для API endpoints
- **CORS конфигурация** для production

### 📋 **Управление задачами**
- **CRUD операции** с валидацией данных
- **Умный поиск** по названию и содержимому
- **Многоуровневая сортировка** с конфликт-валидацией
- **Статистика задач** с аналитикой завершений
- **Файловые вложения** с типизированной загрузкой

### 🤝 **Система совместной работы**
- **Гибкие права доступа** (view/edit permissions)
- **Безопасное sharing** между пользователями
- **Управление коллабораторами** с audit trail
- **Динамический контроль доступа** на уровне ресурсов

### 🏗️ **Архитектура**
- **Чистая архитектура** с разделением слоев (Controller → Service → Repository)
- **Domain-Driven Design** принципы
- **Dependency Injection** через FastAPI
- **Модульная структура** по доменным областям

## 🛠️ **Технический стек**

### Backend
- **FastAPI** - Async веб-фреймворк с автоматической документацией
- **SQLAlchemy** - ORM с поддержкой async/await
- **PostgreSQL** - Реляционная база данных
- **Alembic** - Система миграций БД
- **Redis** - Кеширование и сессии

### DevOps & Инфраструктура
- **Docker** + **Docker Compose** - Контейнеризация
- **GitHub Actions** - CI/CD pipeline
- **Nginx** - Reverse proxy и load balancer
- **pytest** - Тестирование с 80%+ coverage

### Код-качество
- **Pre-commit hooks** - Автоматические проверки кода
- **Black** + **isort** - Форматирование кода
- **mypy** - Статическая типизация
- **Bandit** + **Safety** - Аудит безопасности

## 🚀 **Быстрый старт**

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/todo-api.git
cd todo-api

# Настройка окружения
python3.13 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск миграций
alembic upgrade head

# Запуск сервера разработки
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker (рекомендуется)

```bash
# Разработка
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### 📡 **API Документация**

После запуска приложения:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 **Тестирование**

```bash
# Запуск всех тестов
pytest

# С покрытием кода
pytest --cov=src --cov-report=html

# Только unit тесты
pytest -m unit

# Только integration тесты  
pytest -m integration
```

## 📊 **Производительность**

### Нагрузочное тестирование
```bash
# Установка k6
brew install k6  # macOS
# или скачайте с https://k6.io/

# Запуск нагрузочных тестов
k6 run tests/performance/load_test.js
```

### Оптимизации
- **Database indexing** для критических запросов
- **Connection pooling** для БД
- **Async processing** для I/O операций
- **Response caching** для статистик

## 🔧 **Конфигурация**

### Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `JWT_SECRET` | Секретный ключ для JWT | (генерируется) |
| `JWT_EXPIRATION_MINUTES` | Время жизни access токена | 30 |
| `MAX_FILE_SIZE_MB` | Максимальный размер файла | 10 |
| `RATE_LIMIT_PER_MINUTE` | Лимит запросов в минуту | 60 |

### Настройка базы данных

```sql
-- Создание пользователя и базы данных
CREATE USER todoapp WITH ENCRYPTED PASSWORD 'secure_password';
CREATE DATABASE todoapp OWNER todoapp;
GRANT ALL PRIVILEGES ON DATABASE todoapp TO todoapp;
```

## 📈 **Мониторинг**

### Health checks
- `GET /health` - Общий статус приложения
- `GET /health/db` - Состояние базы данных
- `GET /health/redis` - Состояние кеша

### Логирование
Структурированное логирование с уровнями:
- **DEBUG** - Детальная отладочная информация
- **INFO** - Общая информация о работе
- **WARNING** - Предупреждения
- **ERROR** - Ошибки выполнения
- **CRITICAL** - Критические ошибки системы

## 🔒 **Безопасность**

### Implemented Security Measures
- ✅ **Input Validation** - Pydantic models с кастомными валидаторами
- ✅ **SQL Injection Prevention** - SQLAlchemy ORM параметризованные запросы  
- ✅ **Password Security** - bcrypt hashing с salt
- ✅ **JWT Security** - Подписанные токены с expiration
- ✅ **Rate Limiting** - Защита от DDoS атак
- ✅ **File Upload Security** - Валидация типов и размеров файлов
- ✅ **CORS Configuration** - Настроенные домены для production

### Security Headers
```python
# Автоматически добавляются middleware
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## 🚀 **Deployment**

### Production готовность
- ✅ **Docker multi-stage builds** для оптимизации размера
- ✅ **Health checks** для orchestration
- ✅ **Graceful shutdown** handling
- ✅ **Environment-based configuration**
- ✅ **Database migrations** в startup процессе
- ✅ **Reverse proxy** конфигурация

### CI/CD Pipeline
1. **Code Quality** - Linting, formatting, type checking
2. **Security Scan** - Dependency vulnerabilities, code analysis
3. **Testing** - Unit, integration, performance tests
4. **Build** - Docker image creation
5. **Deploy** - Automated deployment на staging/production

## 👥 **Архитектурные решения**

### Принципы дизайна
- **SOLID принципы** - Чистый, maintainable код
- **DRY (Don't Repeat Yourself)** - Переиспользование компонентов
- **KISS (Keep It Simple)** - Простота в сложности
- **Fail Fast** - Ранняя валидация и обработка ошибок

### Паттерны
- **Repository Pattern** - Абстракция доступа к данным
- **Service Layer** - Бизнес-логика отделена от контроллеров  
- **Dependency Injection** - Слабая связанность компонентов
- **Factory Pattern** - Создание сложных объектов

## 📝 **Планы развития**

### v2.0 Roadmap
- [ ] **WebSocket поддержка** для real-time уведомлений
- [ ] **Elasticsearch интеграция** для продвинутого поиска
- [ ] **Task templates** и automation
- [ ] **Mobile API** endpoints
- [ ] **GraphQL** endpoint как альтернатива REST

### Техническое развитие
- [ ] **Kubernetes** deployment конфигурация
- [ ] **Prometheus** metrics и **Grafana** dashboards
- [ ] **Distributed caching** с Redis Cluster
- [ ] **Message queue** для async задач (Celery + Redis)

## 🤝 **Contributing**

Этот проект следует принципам [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Установка pre-commit hooks
pre-commit install

# Создание feature branch
git checkout -b feature/awesome-feature

# Commit с conventional format
git commit -m "feat: add awesome feature"
```