from django.db import models
from account.models import BaseUser


class Action(models.Model):
    class ActionChoices(models.TextChoices):
        BLIND_DATE = 'blind_date', 'BLIND_DATE'
        MENU = 'menu', 'MENU'
        INITIATE_WALLET = 'initiate_wallet', 'INITIATE_WALLET'
        INITIATE_EXCHANGE = 'initiate_exchange', 'INITIATE_EXCHANGE'

    user = models.ForeignKey(to=BaseUser, on_delete=models.CASCADE, related_name='actions')
    action = models.CharField(choices=ActionChoices.choices, max_length=30)
    created = models.DateTimeField()
