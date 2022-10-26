import json
import logging
from pathlib import Path
from time import sleep
from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from kucoin_manager.settings import settings
from kucoin_manager.web.api.auth.views import manager
from kucoin_manager.db.models.kucoin import Account, Orders
from kucoin_manager.web.api.kucoin.utils import (
    js_bulk_place_limit_order,
    kucoin_cancel_all_order,
    kucoin_cancel_order,
    js_get_open_orders,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))
logger = logging.getLogger(__name__)


@router.get("/accounts", response_class=HTMLResponse)
async def create_account(
    request: Request,
    user=Depends(manager),
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
    user=Depends(manager),
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
    user=Depends(manager),
) -> Any:
    """
    Test.

    :param request: request object
    :Returns: Template response
    """
    accounts = await Account.all().order_by("-created_at")

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
    user=Depends(manager),
) -> Any:
    """
    Test.

    :param request: request object
    :Returns: Template response
    """
    form: dict = await request.form()
    form = jsonable_encoder(form)
    accounts = []
    form_account_ids = []
    for key in form.keys():
        if key.startswith("acc_"):
            acc_id = int(key.replace("acc_", ""))
            form_account_ids.append(acc_id)

    if form_account_ids:
        accounts = await Account.in_bulk(form_account_ids)
        accounts = accounts.values()
    elif not accounts:
        return "Please select some account."

    await js_bulk_place_limit_order(
        accounts,
        symbol=form["symbol"],
        side=form["sell-buy"],
        lever=form["leverage"],
        size=form["size"],
        price=form.get("price"),
    )

    return RedirectResponse(
        router.url_path_for("future_trade"),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/order", response_class=HTMLResponse, )
async def list_orders(
    request: Request,
    user=Depends(manager),
):
    orders = await Orders.exclude(status="canceled").values()
    logger.info(f"list_orders, orders: {orders}")

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
    user=Depends(manager),
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


@router.get("/order/cancel-db/", response_class=HTMLResponse)
async def cancel_db_orders(
    user=Depends(manager),
):
    orders = await Orders.exclude(status="canceled")
    for order in orders:
        await kucoin_db_cancel_order(
            account=await order.account,
            order=order
        )

    return RedirectResponse(
        router.url_path_for("list_orders"),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/order/cancel-all/", response_class=HTMLResponse)
async def cancel_all_orders(
    user=Depends(manager),
):
    accounts = await Account.filter(name="erfan")
    for account in accounts:
        cancel_ids = await kucoin_cancel_all_order(account)

        if type(cancel_ids) == dict:
            ids = cancel_ids.get('cancelledOrderIds', [])
            await Orders.filter(order_id__in=ids).update(status="canceled")
    
    return RedirectResponse(
        router.url_path_for("list_orders"),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/order/detail/", response_class=HTMLResponse)
async def orders_detail(
    request: Request,
    symbol: str = "",
    page: int = 1,
    user=Depends(manager),
):
    symbol = symbol or "XBTUSDTM"
    accounts = await Account.all().order_by("name").offset((page-1)*settings.PAGE_SIZE).limit(settings.PAGE_SIZE)

    account_details = js_get_open_orders(
        accounts=accounts,
        symbol=symbol
    )

    return templates.TemplateResponse(
        "order_details.html",
        {
            "request": request,
            "accounts": account_details,
        },
    )


async def kucoin_db_cancel_order(account, order: Orders):
    if order.status == "fail":
        await order.update_from_dict({"status": "canceled"})
        await order.save()
        return

    canceled = kucoin_cancel_order(account=account, order_id=order.order_id)
    if canceled:
        await order.update_from_dict({"status": "canceled"})
        await order.save()


@router.get("/account/import/", response_class=HTMLResponse)
async def import_accounts(
    user=Depends(manager),
):
    with open("account.json") as f:
        accounts = json.load(f)
        for i, acc in enumerate(accounts):
            try:
                await Account.get_or_create(
                    name=i,
                    api_key=acc['api_key'],
                    api_secret=acc['api_secret'],
                    api_passphrase=acc['api_passphrase'],
                )
            except Exception as e:
                print("=======")
                print(e)
                print("=======")
    
    return RedirectResponse(
        router.url_path_for("create_account"),
        status_code=status.HTTP_302_FOUND,
    )

        # await Account.bulk_create(
        #     account_obj
        # )


@router.get("/account/delete/{api_key}/", response_class=HTMLResponse)
async def delete_account(
    api_key: str,
    user=Depends(manager),
):
    account = await Account.get_or_none(api_key=api_key)
    if account:
        await account.delete()
    
    return RedirectResponse(
        router.url_path_for("create_account"),
        status_code=status.HTTP_302_FOUND,
    )
