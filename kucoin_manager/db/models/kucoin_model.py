from tortoise import fields, models


class AccountModel(models.Model):
    """Model for demo purpose."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=200)  # noqa: WPS432
    api_key = fields.CharField(max_length=200)  # noqa: WPS432
    api_secret = fields.CharField(max_length=200)  # noqa: WPS432
    api_passphrase = fields.CharField(max_length=200)  # noqa: WPS432

    def __str__(self) -> str:
        return self.name
