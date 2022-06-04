from django.db import models
from account.models import Trader, User
from simple_history.models import HistoricalRecords


class Plan(models.Model):
    trader = models.ForeignKey(to=Trader, on_delete=models.CASCADE, related_name='plans')
    days = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.days}:{self.price}$'


class Payment(models.Model):
    plan = models.ForeignKey(to=Plan, on_delete=models.DO_NOTHING, related_name='payments')
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='payments')
    transaction_hash = models.CharField(max_length=100)
    is_accepted = models.BooleanField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    expired = models.DateTimeField(blank=True)
    history = HistoricalRecords()
