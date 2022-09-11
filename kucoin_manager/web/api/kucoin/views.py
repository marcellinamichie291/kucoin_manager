from typing import Any, List

from fastapi import APIRouter, Request
from fastapi.param_functions import Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from kucoin_manager.db.dao.account_dao import AccountDAO
from kucoin_manager.db.models.kucoin_model import AccountModel
from kucoin_manager.web.api.kucoin.schema import AccountModelDTO, AccountModelInputDTO

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


@router.put("/")
async def create_account_model(
    new_account_object: AccountModelInputDTO,
    account_dao: AccountDAO = Depends(),
) -> None:
    """
    Creates account model in the database.

    :param new_account_object: new account model item.
    :param account_dao: DAO for account models.
    """
    await account_dao.create_account_model(**new_account_object.dict())


templates = Jinja2Templates(directory="templates")


@router.get("/index", response_class=HTMLResponse)
async def read_item(
    request: Request,
    account_dao: AccountDAO = Depends(),
) -> Any:
    """
    Test.

    :param request: request object
    :param account_dao: DAO for account models.
    :Returns: TEmplate response
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "accounts": await account_dao.get_all_accounts(limit=0, offset=10),
        },
    )
