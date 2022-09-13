import logging
import re

from kucoin_futures.client import Trade
from requests import exceptions

logger = logging.getLogger(__name__)

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
            logger.warning(
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
            return order_id
        except exceptions.ReadTimeout as exccep:
            logger.exception(exccep)
        except Exception as exccep:
            lever = check_for_leverage_limit(str(exccep)) or lever


def place_limit_order_on_all_accounts(accounts, *args, is_sandbox=True, **kwargs):
    """
    Place order for multiple account.

    :param accounts: List of accounts in dict with keys: key, secret, passphrase.
    :param is_sandbox: Indicates if it should use sandbox api or not. # noqa RST213 cannot parse *args correctly
    :param *args: List of arguments passed to order placement function.
    :param **kwargs: Dict of keyword arguments passed to order placement function.
    """
    for acc in accounts:
        client = Trade(
            key=acc["key"],
            secret=acc["secret"],
            passphrase=acc["passphrase"],
            is_sandbox=is_sandbox,
        )
        place_future_limit_order(client, *args, **kwargs)


def get_accounts_from_db():
    """
    Gets accounts data from database and put then in json format.

    :Returns: List of account dict.
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

    return accounts


# TODO what we can do to improve performance:
# if we reach the api limit then we can test proxy ip
# if can not reach the api limit we can test async and then node js

# def place_stop_order()
