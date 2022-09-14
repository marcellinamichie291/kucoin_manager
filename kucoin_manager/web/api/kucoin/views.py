import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from kucoin_manager.settings import settings

from kucoin_manager.web.api.kucoin.exceptions import NoAccountFoundError
from kucoin_manager.web.api.kucoin.utils import get_accounts_from_db, db_list_open_orders, place_limit_order_on_all_accounts

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))
logger = logging.getLogger(__name__)


@router.get("/accounts", response_class=HTMLResponse)
async def create_account(
    request: Request,
) -> Any:
    """
    Creates account model in the database.

    :param request: new account model item.
    :Returns: Template response
    """
    return templates.TemplateResponse(
        "accounts.html",
        {
            "request": request,
            "accounts": get_accounts_from_db(),
        },
    )


@router.post("/accounts")
async def create_account_form(
    name: str = Form(""),
    api_key: str = Form(None),
    api_secret: str = Form(None),
    api_passphrase: str = Form(None),
    is_sandbox: bool = Form(False),
) -> Any:
    """
    Creates account model in the database.

    :param name: name.
    :param api_key: key.
    :param api_secret: secret.
    :param api_passphrase: password.
    :param is_sandbox: should sandbox endpoints be used for this account.
    :Returns: Template response
    """
    accounts = get_accounts_from_db()
    ids = [_["id"] for _ in accounts]
    next_id = len(accounts)
    while next_id in ids:
        next_id += 1

    for acc in accounts:
        if acc["api_key"] == api_key:
            break
    else:
        accounts.append(
            {
                "id": next_id,
                "name": name,
                "api_key": api_key,
                "api_secret": api_secret,
                "api_passphrase": api_passphrase,
                "is_sandbox": is_sandbox,
                "api_type": "future",
            },
        )

    with open("account.json", "w") as out_file:
        json.dump(accounts, out_file)

    logger.debug(f"Form Matched accounts: {accounts}.")
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
    :Returns: Template response
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


@router.post("/future-trade")
async def future_trade_form(
    request: Request,
) -> Any:
    """
    Test.

    :param request: request object
    :Returns: Template response
    """
    db_accounts = get_accounts_from_db()
    da: dict = await request.form()
    da = jsonable_encoder(da)

    if not db_accounts:
        raise NoAccountFoundError

    form_accounts = db_accounts
    if da.get("acc_all") != "on":
        form_accounts = []
        form_account_ids = []

        for key in da.keys():
            if key.startswith("acc_"):
                acc_id = int(key.replace("acc_", ""))
                form_account_ids.append(acc_id)

        for acc in db_accounts:
            if acc["id"] in form_account_ids:
                form_accounts.append(acc)

    form_accounts = form_accounts or db_accounts

    order_id = place_limit_order_on_all_accounts(
        form_accounts,
        symbol=da["symbol"],
        side=da["sell-buy"],
        lever=da.get("leverage"),
        size=da["size"],
        price=da.get("price"),
        is_sandbox=settings.is_sandbox
    )
    if order_id is None:
        return RedirectResponse(
            router.url_path_for("future_trade"),
            status_code=status.HTTP_302_FOUND,
        )
 
    logger.debug("input: ", da, "\nselected accounts: ", form_accounts)

    return RedirectResponse(
        router.url_path_for("future_trade"),
        status_code=status.HTTP_302_FOUND,
    )
