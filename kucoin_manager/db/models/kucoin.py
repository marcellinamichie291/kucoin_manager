from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class Orders(models.Model):
    """
    The Order model
    """
    id = fields.IntField(pk=True)

    order_id = fields.CharField(max_length=50)
    symbol = fields.CharField(max_length=20)
    side = fields.CharField(max_length=4)
    size = fields.CharField(max_length=10)
    price = fields.CharField(max_length=10)
    leverage = fields.CharField(max_length=3)
    status = fields.CharField(max_length=10, default="open")

    account = fields.ForeignKeyField('models.Account', related_name='orders')

    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)


class Account(models.Model):
    """
    The Account model
    """
    id = fields.IntField(pk=True)

    name = fields.CharField(max_length=50)
    api_key = fields.CharField(max_length=255, unique=True)
    api_secret = fields.CharField(max_length=255)
    api_passphrase = fields.CharField(max_length=255)
    api_type = fields.CharField(max_length=20, default="future")
    group =  fields.CharField(max_length=20, null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)


Order_Pydantic = pydantic_model_creator(Orders, name="Order")
OrderIn_Pydantic = pydantic_model_creator(Orders, name="OrderIn", exclude_readonly=True)
