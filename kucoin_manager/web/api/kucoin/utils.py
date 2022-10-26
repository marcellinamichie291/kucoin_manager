import json
import logging
import re
import subprocess
import time
from typing import List

from kucoin_futures.client import Trade
from requests import exceptions

from kucoin_manager.db.models.kucoin import Account, Orders

logger = logging.getLogger(__name__)
find_node = subprocess.Popen(
    ["which", "node"],
    stdout=subprocess.PIPE
)
node_js_path = find_node.stdout.read().decode().strip()


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

    :param client: Trade object that contains API credentials.
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
            lever = check_for_leverage_limit(str(exccep)) or lever
            counter += 1
            if counter > 3:
                return None


async def place_limit_order_on_all_accounts(accounts: List[Account], *args, **kwargs):
    """
    Place order for multiple account.

    :param accounts: List of accounts.
    :param *args: List of arguments passed to order placement function.
    :param **kwargs: Dict of keyword arguments passed to order placement function.
    """
    account_order_id = []
    for acc in accounts:
        logger.error(f"-\n-\n\n{acc}\n-\n-\n")
        client = Trade(
            key=acc.api_key,
            secret=acc.api_secret,
            passphrase=acc.api_passphrase,
            is_sandbox=False,
        )

        logger.error(f"\nplace_limit_order_on_all_accounts => {kwargs}")
        order = place_future_limit_order(client, *args, **kwargs)
        if order:
            account_order_id.append([acc, order['orderId']])
            await Orders.create(
                order_id = order['orderId'],
                account = acc,
                symbol = kwargs["symbol"],
                side = kwargs["side"],
                size = kwargs["size"],
                price = kwargs.get("price"),
                leverage = kwargs["lever"],
            )

    return account_order_id


async def js_bulk_place_limit_order(accounts: List[Account], *args, **kwargs):
    accounts_and_order_data = {
        "accounts": [
            {
                "api_key": acc.api_key,
                "api_secret": acc.api_secret,
                "api_passphrase": acc.api_passphrase,
            } for acc in accounts
        ],
        "side": kwargs["side"],
        "symbol": kwargs["symbol"],
        "type": "limit",
        "leverage": kwargs["lever"],
        "size": kwargs["size"],
        "price": kwargs.get("price"),
    }
    
    order_results = run_js_code("place_order", accounts_and_order_data)

    failed_orders = []
    if order_results:
        for order in order_results:
            if order["status"] == "success":
                await Orders.create(
                    account = Account.get(api_key=order['api_key']),
                    order_id = order['order_id'],
                    symbol = order["symbol"],
                    side = order["side"],
                    size = order["size"],
                    price = order.get("price"),
                    leverage = order["leverage"],
                )
            else:
                failed_orders.append(order)

    return failed_orders


def run_js_code(js_file_name, in_data):
    js_base_path = "kucoin_manager/js/"
    with open(js_base_path + f"data/{js_file_name}_in.json", "w") as f:
        json.dump(in_data, f)

    p = subprocess.Popen(
        [
            node_js_path,
            js_base_path + f"{js_file_name}.js"
        ],
        stdout=subprocess.PIPE
    )
    out = p.stdout.read().decode()
    print(out)

    with open(js_base_path + f"data/{js_file_name}_out.json") as f:
        order_results = json.load(f)

    return order_results


async def kucoin_cancel_all_order(account: Account):
    try:
        client = Trade(
            key=account.api_key,
            secret=account.api_secret,
            passphrase=account.api_passphrase,
            is_sandbox=False,
        )

        cancel_ids = client.cancel_all_limit_order()
        return cancel_ids
    except Exception as e:
        logger.error(f"Cancel failed, account name: {account.name}, e: {e}")
        if "The order cannot be canceled." in str(e):
            return True
    

def kucoin_cancel_order(account, order_id):
    try:
        client = Trade(
            key=account.api_key,
            secret=account.api_secret,
            passphrase=account.api_passphrase,
            is_sandbox=False,
        )

        canceled = client.cancel_order(orderId=order_id)
        return canceled
    except Exception as e:
        logger.error(f"Cancel failed, order_id: {order_id}, e: {e}")
        if "The order cannot be canceled." in str(e):
            return True


def js_get_open_orders(accounts, symbol):
    accounts_and_symbol = {
        "accounts": [
            {
                "name": acc.name,
                "api_key": acc.api_key,
                "api_secret": acc.api_secret,
                "api_passphrase": acc.api_passphrase,
            } for acc in accounts
        ],
        "symbol": symbol,
    }
    
    account_details = run_js_code("get_open_orders", accounts_and_symbol)
    cleansed_data = []
    for acc in account_details:
        if acc['status'] == "success":
            cleansed_data.append({
                "name": acc['name'],
                "buy_size": acc['data']['openOrderBuySize'],
                "sell_size": acc['data']['openOrderSellSize'],
                "buy_cost": acc['data']['openOrderBuyCost'],
                "sell_cost": acc['data']['openOrderSellCost'],
                "currency":acc['data']['settleCurrency'],
                "symbol": acc['symbol'],
            })
        else:
            cleansed_data.insert(0, {
                "name": acc['name'],
                "buy_size": acc['status'],
                "sell_size": acc['msg'],
                "buy_cost": acc['retry_count'],
                "sell_cost": acc.get('code') or "",
                "symbol": acc['symbol'],
            })

    return cleansed_data
        # client = Trade(
        #     key=account.api_key,
        #     secret=account.api_secret,
        #     passphrase=account.api_passphrase,
        #     is_sandbox=False,
        # )

        # detail = client.get_open_order_details(symbol=symbol)
        # return {
        #     "buy_size": detail["openOrderBuySize"],
        #     "sell_size": detail["openOrderSellSize"],
        #     "buy_cost": detail["openOrderBuyCost"],
        #     "sell_cost": detail["openOrderSellCost"],
        #     "currency": detail["settleCurrency"],
        # }
    
    # return {
    #     "buy_size": str(err_msg),
    #     "sell_size": f"Retry: {retry_count}",
    #     "buy_cost": "",
    #     "sell_cost": "",
    #     "currency": "",
    # }


# class acc:
#     name = "test"
#     api_key = "6347f074d8b5a600010d5c73"
#     api_secret = "e8483378-3b96-4f6b-83d1-a48734e74691"
#     api_passphrase = "dtNe6tF6Sy4PtXV"

# a = kucoin_get_open_orders(acc, "XBTUSDTM")
# b = 3
