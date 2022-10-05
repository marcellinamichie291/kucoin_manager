import asyncio
import base64
import hashlib
import hmac
import json
import logging
import re
import time
from typing import List
from urllib.parse import urljoin
from uuid import uuid1

import httpx
from fastapi.concurrency import run_in_threadpool
from kucoin_futures.client import Trade
from requests import exceptions

from kucoin_manager.db.models.kucoin import Account, Orders

logger = logging.getLogger(__name__)
sem = asyncio.Semaphore(25)
base_url = "https://api-futures.kucoin.com"

FIX_MAX_LEVERAGE_ERROR = True


def read_api_credentials_from_file(file_name):
    """
    Reads API credentials from file.

    :param file_name: name of the credentials file.
    :Returns: list of dict containing account credentials.
    """
    with open(file_name, "a+") as credentials_file:
        credentials_file.seek(0)
        accounts = []
        for line in credentials_file.readlines():
            if line:
                acc = dict(
                    zip( # noqa WPS317
                        (
                            "key",
                            "secret",
                            "passphrase",
                        ),
                        line.split(":"),
                    ),
                )
                accounts.append(acc)
            else:
                credentials_file.write("key:secret:passphrase\n")
                break
    return accounts


def check_for_leverage_limit(exception_message):
    """
    Checks if the exception caused by leverage max limit.

    Then try to set the maximum leverage limit.

    :param exception_message: Exception message string
    :Returns: maximum leverage or None
    """
    if FIX_MAX_LEVERAGE_ERROR:
        max_leverage_check = re.findall(
            r"The leverage cannot be greater than (\d+)", exception_message,
        )
        if max_leverage_check:
            lever = int(max_leverage_check[0])
            logger.error(
                f"Found leverage error. Reset the leverage to: {lever}!",
            )
            return lever
    return None


def place_future_limit_order( # noqa WPS231 it's not actually that complex :)
    client: Trade,
    symbol: str,
    side: str,
    size: str,
    price: str = None,
    lever: int = 1,
):
    """
    Trade on specified account for symbol.

    :param secret: secret.
    :param passphrase: passphrase.
    :param key: key.
    :param symbol: like XBTUSDTM
    :param side: buy or sell
    :param size: amount of currency you want to trade
    :param price: price for each unit of the currency
    :param lever: leverage, 0 to 100
    :Returns: order id
    """
    counter = 0
    while True:
        try:
            if price:
                order_id = client.create_limit_order(
                    symbol=symbol,
                    side=side,
                    lever=lever,
                    size=size,
                    price=price,
                )
            else:
                order_id = client.create_market_order(
                    symbol=symbol,
                    side=side,
                    lever=lever,
                    size=size,
                )
            logger.debug(f"\n-=-\nOrder [[[ Done ]]]: {symbol}.\n-=-\n")
            return order_id
        except exceptions.ReadTimeout as exccep:
            logger.error(str(exccep))
            counter += 1
            if counter > 3:
                return None
        except Exception as exccep:
            logger.error(str(exccep))
            # noqa new_lever = check_for_leverage_limit(str(exccep))
            # if new_lever:
            # noqa      lever = new_lever
            if "200" in str(exccep) or "401" in str(exccep):
                logger.error(f"Stopped loop of retrying on err: {exccep}")
                return None
            counter += 1
            if counter > 3:
                return None


async def async_place_limit_order(
    client: httpx.AsyncClient,
    secret: str,
    passphrase: str,
    key: str,
    symbol: str,
    side: str,
    size: str,
    price: str = None,
    lever: int = 1,
):
    params = {
        "symbol": symbol,
        "size": size,
        "side": side,
        "price": price,
        "leverage": lever,
        "type": "limit" if price else "market",
        "clientOid": return_unique_id(),
    }
    data_json= json.dumps(params)

    uri = "/api/v1/orders"
    uri_path = uri + data_json

    headers = create_headers(secret, key, passphrase, uri_path)
    url = urljoin(base_url, uri)

    counter = 0
    while True:
        async with sem:
            try:
                response_data = await client.post(url, headers=headers, data=data_json, timeout=100)
                data = check_response_data(response_data)
                logger.debug(f"Got this data for placing order: {data}")
                logger.debug(f"\n-=-\nOrder [[[ Done ]]]: {symbol}.\n-=-\n")
                # return order_id
            except exceptions.ReadTimeout as exccep:
                logger.error(str(exccep))
                counter += 1
                if counter > 3:
                    return None
            except Exception as exccep:
                logger.error(str(exccep))
                # noqa new_lever = check_for_leverage_limit(str(exccep))
                # if new_lever:
                # noqa      lever = new_lever
                if "200" in str(exccep) or "401" in str(exccep):
                    logger.error(f"Stopped loop of retrying on err: {exccep}")
                    return None
                counter += 1
                if counter > 3:
                    return None


async def place_limit_order_on_all_accounts(accounts: List[Account], *args, **kwargs):
    """
    Place order for multiple account.

    :param accounts: List of accounts.
    :param *args: List of arguments passed to order placement function.
    :param **kwargs: Dict of keyword arguments passed to order placement function.
    :Returns: 2D list each item contain account and created order id.
    """
    account_order_id = []
    async with httpx.AsyncClient() as client:
        calls = [
            asyncio.create_task(async_place_order_save_to_db(args, kwargs, account_order_id, client, acc))
            for acc in accounts
        ]
    
        print("All task created.")

        account_order_id = await asyncio.gather(*calls)

    return account_order_id


async def async_place_order_save_to_db(args, kwargs, account_order_id, client, acc):
    order = async_place_limit_order(
            client=client,
            key=acc.api_key,
            secret=acc.api_secret,
            passphrase=acc.api_passphrase,
            *args, **kwargs
        )
    if order:
        await Orders.create(
                order_id=order["orderId"],
                account=acc,
                symbol=kwargs["symbol"],
                side=kwargs["side"],
                size=kwargs["size"],
                price=kwargs.get("price"),
                leverage=kwargs["lever"],
            )
        return [acc, order["orderId"]]


def kucoin_cancel_order(account, order_id):
    try:
        client = Trade(
            key=account.api_key,
            secret=account.api_secret,
            passphrase=account.api_passphrase,
            is_sandbox=False,
        )

        return client.cancel_order(orderId=order_id)
    except Exception as e:
        logger.error(f"Cancel failed, order_id: {order_id}, e: {e}")
        if "The order cannot be canceled." in str(e):
            return True

## Utils for utils :) ##

def return_unique_id():
    return "".join([each for each in str(uuid1()).split("-")])


def create_headers(secret, key, uri_path):
    headers = {}
    now_time = int(time.time()) * 1000
    str_to_sign = str(now_time) + "POST" + uri_path
    sign = base64.b64encode(
        hmac.new(secret.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).digest())
    passphrase = base64.b64encode(
        hmac.new(secret.encode("utf-8"), passphrase.encode("utf-8"), hashlib.sha256).digest())
    print(f"[{key}]")
    headers = {
        "KC-API-SIGN": str(sign),
        "KC-API-TIMESTAMP": str(now_time),
        "KC-API-KEY": str(key),
        "KC-API-PASSPHRASE": str(passphrase),
        "Content-Type": "application/json",
        "KC-API-KEY-VERSION": "2"
    }
    headers["User-Agent"] = "kucoin-futures-python-sdk/v1.0.6"
    return headers



def check_response_data(response_data):
    if response_data.status_code == 200:
        try:
            data = response_data.json()
        except ValueError:
            raise Exception(response_data.content)
            print(response_data.content)
        else:
            if data and data.get("code"):
                if data.get("code") == "200000":
                    if data.get("data"):
                        return data["data"]
                    else:
                        return data
                else:
                    raise Exception("{}-{}".format(response_data.status_code, response_data.text))
                    print("{}-{}".format(response_data.status_code, response_data.text))
    else:
        raise Exception("{}-{}".format(response_data.status_code, response_data.text))
        print("{}-{}".format(response_data.status_code, response_data.text))


# TODO Login / delete account

# TODO what we can do to improve performance:
# if we reach the api limit then we can test proxy ip
# if can not reach the api limit we can test async and then node js

# def place_stop_order()
