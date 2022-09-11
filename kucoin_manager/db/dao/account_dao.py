from typing import List

from kucoin_manager.db.models.kucoin_model import AccountModel


class AccountDAO:
    """Class for accessing account table."""

    async def create_account_model(
        self,
        name: str,
        api_key: str,
        api_secret: str,
        api_passphrase: str,
    ) -> None:
        """
        Add single account to session.

        :param name: name of a account.
        :param api_key: for kucoin api access.
        :param api_secret: for kucoin api access.
        :param api_passphrase: for kucoin api access.
        """
        await AccountModel.create(
            name=name,
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
        )

    async def get_all_accounts(self, limit: int, offset: int) -> List[AccountModel]:
        """
        Get all account models with limit/offset pagination.

        :param limit: limit of accounts.
        :param offset: offset of accounts.
        :return: stream of accounts.
        """
        return await AccountModel.all().offset(offset).limit(limit)
