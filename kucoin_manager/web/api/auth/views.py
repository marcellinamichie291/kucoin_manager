from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from starlette import status

from kucoin_manager.settings import settings
from kucoin_manager.web.api.auth.exceptions import NotAuthenticatedException

DEFAULT_TOKEN_EXPIRATION_HOUR = 12
manager = LoginManager(
    settings.secret,
    token_url="/auth/login",
    custom_exception=NotAuthenticatedException,
    use_cookie=True,
    use_header=True,
    default_expiry=timedelta(hours=DEFAULT_TOKEN_EXPIRATION_HOUR),
)

DB = {
    "users": {
        "johndoe@mail.com": {
            "name": "John Doe",
            "password": "hunter2",
        },
    },
}


@manager.user_loader()
def query_user(user_id: str):
    """
    Get a user from the db.

    :param user_id: E-Mail of the user
    :return: None or the user object
    """
    return DB["users"].get(user_id)


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


@router.get("/login")
def login_form(
    request: Request,
):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
        },
    )


@router.post("/login")
def login(data: OAuth2PasswordRequestForm = Depends()):
    email = data.username
    password = data.password

    user = query_user(email)
    if not user:
        # you can return any response or error of your choice
        raise InvalidCredentialsException
    elif password != user["password"]:
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data={"sub": email},
    )

    response = RedirectResponse(
        "/future-trade",
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(key="access-token", value=access_token)
    return response


@router.get("/test")
def my_test(user=Depends(manager)):
    return "Yeay"
