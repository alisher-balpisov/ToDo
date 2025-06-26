from fastui import FastUI, Page, components as c, events as e
from fastui.components.display import Alert
from fastapi.responses import RedirectResponse
from fastapi import Depends, Request
from fastui.middleware import FastUIMiddleware

app.add_middleware(FastUIMiddleware)
frontend = FastUI()

@app.get("/ui/", response_model=Page)
def homepage():
    return Page(
        title="ToDo App",
        content=[
            c.Heading(text="Добро пожаловать в ToDo", level=1),
            c.Link(url="/ui/tasks", text="Посмотреть задачи"),
            c.Link(url="/ui/login", text="Войти", style="margin-left: 1rem")
        ]
    )

@app.get("/ui/login", response_model=Page)
def login_page():
    return Page(
        title="Login",
        content=[
            c.Heading(text="Вход", level=2),
            c.Form(
                on_submit=e.Post(
                    url="/ui/login/submit",
                    replace_url="/ui/tasks"
                ),
                fields=[
                    c.TextField(name="username", label="Имя пользователя"),
                    c.PasswordField(name="password", label="Пароль"),
                ],
                submit_text="Войти"
            )
        ]
    )

@app.post("/ui/login/submit")
def login_submit(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    if username == "test" and password == "test":
        token = security.create_access_token(uid="12345")
        response = RedirectResponse(url="/ui/tasks", status_code=302)
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        return response
    return Page(title="Ошибка", content=[Alert(text="Неправильный логин/пароль", type="error")])


@app.get("/ui/tasks", response_model=Page)
def tasks_ui():
    tasks = session.query(ToDo).order_by(ToDo.date_time.desc()).all()
    return Page(
        title="Ваши задачи",
        content=[
            c.Heading(text="Список задач", level=2),
            *[
                c.Card(
                    title=task.name,
                    content=[
                        c.Text(f"Статус: {'✅' if task.completion_status else '❌'}"),
                        c.Text(f"Дата: {task.date_time.strftime('%Y-%m-%d %H:%M')}"),
                        c.Text(task.text)
                    ]
                )
                for task in tasks
            ],
            c.Link(url="/ui/add", text="➕ Добавить задачу")
        ]
    )

@app.get("/ui/add", response_model=Page)
def add_task_form():
    return Page(
        title="Добавить задачу",
        content=[
            c.Heading(text="Новая задача", level=2),
            c.Form(
                on_submit=e.Post(url="/ui/add/submit", replace_url="/ui/tasks"),
                fields=[
                    c.TextField(name="name", label="Название"),
                    c.TextAreaField(name="text", label="Описание"),
                ],
                submit_text="Создать"
            )
        ]
    )

@app.post("/ui/add/submit")
async def add_submit(request: Request):
    form = await request.form()
    new_task = ToDo(
        name=form.get("name"),
        text=form.get("text"),
        completion_status=False,
        date_time=datetime.now(pytz.timezone('Asia/Almaty'))
    )
    session.add(new_task)
    session.commit()
    return RedirectResponse(url="/ui/tasks", status_code=302)