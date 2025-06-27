from fastapi import HTTPException, Form
from app.models import session, User
from fastapi.security import OAuth2PasswordBearer
from app.auth.auth_backend import hash_password, verify_password, create_access_token, decode_access_token
from todos import router
oauth_scheme = OAuth2PasswordBearer(tokenUrl='/login')


@router.post("/register")
def register(username: str = Form(), password: str = Form()):
    if session.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    return {"message": "User создан"}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = session.query(User).filter_by(username=form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={'sub': user.username})
    return {'access_token': access_token, 'token_type': 'bearer'}
