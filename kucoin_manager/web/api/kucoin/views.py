import json
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Form, Request
from fastapi.param_functions import Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from kucoin_manager.db.dao.account_dao import AccountDAO
from kucoin_manager.db.models.kucoin_model import AccountModel
from kucoin_manager.web.api.kucoin.schema import AccountModelDTO

router = APIRouter()


@router.get("/", response_model=List[AccountModelDTO])
async def get_account_models(
    limit: int = 10,
    offset: int = 0,
    account_dao: AccountDAO = Depends(),
) -> List[AccountModel]:
    """
    Retrieve all account objects from the database.

    :param limit: limit of account objects, defaults to 10.
    :param offset: offset of account objects, defaults to 0.
    :param account_dao: DAO for account models.
    :return: list of account objects from database.
    """
    return await account_dao.get_all_accounts(limit=limit, offset=offset)


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


@router.get("/index", response_class=HTMLResponse)
async def read_item(
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
