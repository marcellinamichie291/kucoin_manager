import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status

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
        "create_user.html",
        {
            "request": request,
        },
    )


@router.post("/create-user-form")
async def create_account_form(
    api_key: str = Form(None),
    api_secret: str = Form(None),
    api_passphrase: str = Form(None),
) -> Any:
    """
    Creates account model in the database.

    :param api_key: new account model item.
    :param api_secret: new account model item.
    :param api_passphrase: new account model item.
    :Returns: TEmplate response
    """
    with open("account.json", "a+") as input_file:
        input_file.seek(0)
        line = input_file.readline()
        if line:
            input_file.seek(0)
            accounts = json.load(input_file)
        else:
            input_file.write("[]")
            accounts = []

    for acc in accounts:
        if acc["api_key"] == api_key:
            break
    else:
        accounts.append(
            {
                "api_key": api_key,
                "api_secret": api_secret,
                "api_passphrase": api_passphrase,
                "api_type": "future",
            },
        )

    with open("account.json", "w") as out_file:
        json.dump(accounts, out_file)

    print(accounts)  # noqa: WPS421
    return RedirectResponse(
        router.url_path_for("create_account"),
        status_code=status.HTTP_302_FOUND,
    )


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
        "future_trade.html",
        {
            "request": request,
            "accounts": accounts,
        },
    )


@router.post("/future-trade-form", response_class=HTMLResponse)
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
