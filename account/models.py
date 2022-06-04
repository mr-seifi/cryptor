from django.db import models
from django.core.validators import EmailValidator
from uuid import uuid4


class Wallet(models.Model):

    class WalletChoices(models.TextChoices):
        bep_2 = 'bep-2', 'BEP-2'
        bep_20 = 'bep-20', 'BEP-20'
        trc_20 = 'trc-20', 'TRC-20'
        erc_20 = 'erc-20', 'ERC-20'

    network = models.CharField(choices=WalletChoices.choices, max_length=10)
    address = models.CharField(max_length=150)


class BaseUser(models.Model):

    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, validators=[EmailValidator])
    number = models.CharField(unique=True, max_length=15)
    user_id = models.CharField(unique=True, db_index=True, max_length=25)
    username = models.CharField(blank=True, max_length=50)
    token = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.token[:6]}:{self.name}'


class Trader(BaseUser):

    wallet = models.ManyToManyField(to=Wallet, related_name='trader')


class User(BaseUser):

    user_trader = models.ForeignKey(to=Trader, on_delete=models.CASCADE, related_name='army')
    # strategy = models.ForeignKey
