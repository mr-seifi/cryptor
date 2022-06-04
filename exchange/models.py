from django.db import models
from account.models import User
from simple_history.models import HistoricalRecords


class KuCoin(models.Model):

    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    api_passphrase = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
