import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from kucoin_manager.db.models.kucoin import Account, Orders
from kucoin_manager.web.api.kucoin.utils import (
    kucoin_cancel_order,
    place_limit_order_on_all_accounts,
)

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

    accounts = await Account.all()

    return templates.TemplateResponse(
        "accounts.html",
        {
            "request": request,
            "accounts": accounts,
        }
    )


@router.post("/accounts")
async def create_account_form(
    name: str = Form(""),
    api_key: str = Form(None),
    api_secret: str = Form(None),
    api_passphrase: str = Form(None),
) -> Any:
    """
    Creates account model in the database.

    :param name: name.
    :param api_key: key.
    :param api_secret: secret.
    :param api_passphrase: password.
    :Returns: Template response
    """

    await Account.get_or_create(
        name= name,
        api_key= api_key,
        api_secret= api_secret,
        api_passphrase= api_passphrase,
        api_type= "future",
    )

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
    accounts = await Account.all()

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
    form: dict = await request.form()
    form = jsonable_encoder(form)

    form_account_ids = []
    if form.get("acc_all") != "on":
        for key in form.keys():
            if key.startswith("acc_"):
                acc_id = int(key.replace("acc_", ""))
                form_account_ids.append(acc_id)

    if form_account_ids:
        accounts = await Account.in_bulk(form_account_ids)
        accounts = accounts.values()
    else:
        accounts = await Account.all()

    print("[future_trade_form], accounts: ", accounts)

    account_order_id = place_limit_order_on_all_accounts(
        accounts,
        symbol=form["symbol"],
        side=form["sell-buy"],
        lever=form.get("leverage"),
        size=form["size"],
        price=form.get("price"),
    )
    if not account_order_id:
        return RedirectResponse(
            router.url_path_for("future_trade"),
            status_code=status.HTTP_302_FOUND,
        )
    print("account_order_id, ", account_order_id)
    created_orders = await Orders.bulk_create([
        Orders(
            order_id = order_id,
            account = account,
            symbol = form["symbol"],
            side = form["sell-buy"],
            size = form["size"],
            price = form.get("price"),
            leverage = form.get("leverage"),
        )

        for account, order_id in account_order_id
    ])

    print("[future_trade_form], created_orders: ", created_orders)

    return RedirectResponse(
        router.url_path_for("future_trade"),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/order", response_class=HTMLResponse, )
async def list_orders(
    request: Request,
):
    orders = await Orders.filter(status="open")
    logger.info(f"list_orders, orders: {orders}")
    print(f"\n\n\n=-=-\n canceled \n {(await Orders.first()).status} \n")

    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": orders,
        },
    )


@router.get("/order/cancel/{order_id}", response_class=HTMLResponse)
async def cancel_orders(
    order_id: int,
):
    order = await Orders.get_or_none(id=order_id)
    if order:
        await kucoin_db_cancel_order(
            account=await order.account,
            order=order
        )
    return RedirectResponse(
        router.url_path_for("list_orders"),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/order/cancel-all/", response_class=HTMLResponse)
async def cancel_all_orders():
    orders = await Orders.filter(status="open")
    for order in orders:
        await kucoin_db_cancel_order(
            account=await order.account,
            order=order
        )

    return RedirectResponse(
        router.url_path_for("list_orders"),
        status_code=status.HTTP_302_FOUND,
    )


async def kucoin_db_cancel_order(account, order: Orders):
    canceled = kucoin_cancel_order(account=account, order_id=order.order_id)
    if canceled:
        await order.update_from_dict({"status": "canceled"})
        await order.save()


@router.get("/account/import/", response_class=HTMLResponse)
async def import_accounts():
    with open("account.json") as f:
        accounts = json.load(f)
        await Account.bulk_create([
            Account(
                name=i,
                api_key=acc['api_key'],
                api_secret=acc['api_secret'],
                api_passphrase=acc['api_passphrase'],
            )
            for i, acc in enumerate(accounts)
        ])