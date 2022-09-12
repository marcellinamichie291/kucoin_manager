import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


@router.get("/create-user", response_class=HTMLResponse)
async def create_account(
    request: Request,
) -> Any:
    """
    Creates account model in the database.

    :param request: new account model item.
    :Returns: TEmplate response
    """
    return templates.TemplateResponse(
        "create-user.html",
        {
            "request": request,
        },
    )


@router.post("/create-user")
async def create_account_form(
    name: str = Form(None),
    api_key: str = Form(None),
    api_secret: str = Form(None),
    api_passphrase: str = Form(None),
) -> Any:
    """
    Creates account model in the database.

    :param name: new account model item.
    :param api_key: new account model item.
    :param api_secret: new account model item.
    :param api_passphrase: new account model item.
    :Returns: TEmplate response
    """
    return {
        "name": name,
        "api_key": api_key,
        "api_secret": api_secret,
        "api_passphrase": api_passphrase,
    }


@router.get("/future-trade", response_class=HTMLResponse)
async def future_trade(
    request: Request,
) -> Any:
    """
    Test.

    :param request: request object
    :Returns: TEmplate response
    """
    with open("account.json", "a+") as accounts_file:
        accounts_file.seek(0)
        line = accounts_file.readline()
        if line:
            accounts_file.seek(0)
            accounts = json.load(accounts_file)
        else:
            accounts_file.write("[]")
            accounts = []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "accounts": accounts,
        },
    )


@router.post("/future-trade", response_class=HTMLResponse)
async def future_trade_form(
    request: Request,
) -> Any:
    """
    Test.

    :param request: request object
    :Returns: TEmplate response
    """
    with open("account.json", "a+") as accounts_file:
        accounts_file.seek(0)
        line = accounts_file.readline()
        if line:
            accounts_file.seek(0)
            accounts = json.load(accounts_file)
        else:
            accounts_file.write("[]")
            accounts = []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "accounts": accounts,
        },
    )
