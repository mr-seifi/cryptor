from django.db import models
from django.core.validators import EmailValidator
from uuid import uuid4
from simple_history.models import HistoricalRecords


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

    history = HistoricalRecords()


class User(BaseUser):
    class UserManager(models.Manager):
        def vip(self):
            return self.filter(vip=True)

        def active(self):
            return self.filter(vip=True, user_apply=True)

    user_trader = models.ForeignKey(to=Trader, on_delete=models.CASCADE, related_name='army')
    vip = models.BooleanField(default=False)
    user_apply = models.BooleanField(default=False)
    history = HistoricalRecords()
    objects = UserManager()

    def vip_expiration_date(self):
        return getattr(self.payments.last(), 'expired')

    def active_plan(self):
        return getattr(self.payments.last(), 'plan')
    # strategy = models.ForeignKey


class Wallet(models.Model):
    class WalletChoices(models.TextChoices):
        BEP_2 = 'bep-2', 'BEP-2'
        BEP_20 = 'bep-20', 'BEP-20'
        TRC_20 = 'trc-20', 'TRC-20'
        ERC_20 = 'erc-20', 'ERC-20'

    trader = models.ForeignKey(to=Trader, on_delete=models.CASCADE, related_name='wallets')
    network = models.CharField(choices=WalletChoices.choices, max_length=10)
    address = models.CharField(max_length=150)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.network}:{self.address}'
