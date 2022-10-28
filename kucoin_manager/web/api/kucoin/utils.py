import json
import logging
import subprocess
from typing import List

from kucoin_futures.client import Trade

from kucoin_manager.db.models.kucoin import Account, Orders

logger = logging.getLogger(__name__)
find_node = subprocess.Popen(
    ["which", "node"],
    stdout=subprocess.PIPE
)
node_js_path = find_node.stdout.read().decode().strip()


FIX_MAX_LEVERAGE_ERROR = True


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

    for order in order_results:
        order_id = order.get('order_id')
        status = "open" if order["status"] == "success" else "fail"

        await Orders.create(
            account = await Account.get(api_key=order['account']['api_key']),
            order_id = order_id,
            symbol = order["symbol"],
            side = order["side"],
            size = order["size"],
            price = order.get("price"),
            leverage = order["leverage"],
            status = status,
            message = order["msg"],
        )


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

        cancel_ids = client.cancel_all_limit_order("XBTUSDTM") #TODO
        return cancel_ids
    except Exception as e:
        if "The order cannot be canceled." in str(e):
            logger.error(f"Cancel failed - Cancel is not possible - account name: {account.name}")
            return True
        if "html" in str(e):
            logger.error(f"Cancel failed - [Rate Limit] - account name: {account.name}")
            return True
        logger.error(f"Cancel failed, account name: {account.name}, e: {e}")
    

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
