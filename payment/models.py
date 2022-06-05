from django.db import models
from account.models import Trader, User
from simple_history.models import HistoricalRecords
from uuid import uuid4
from django.utils import timezone


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
    class PaymentManager(models.Manager):
        def queue(self):
            return self.filter(is_accepted__isnull=True)

    plan = models.ForeignKey(to=Plan, on_delete=models.DO_NOTHING, related_name='payments')
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='payments')
    transaction_hash = models.CharField(max_length=100)
    is_accepted = models.BooleanField(blank=True)
    token = models.UUIDField(default=uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    expired = models.DateTimeField(blank=True)
    history = HistoricalRecords()
    objects = PaymentManager()

    def __str__(self):
        return f'{self.token[:6]}'

    def _calculate_expiration_date(self):
        return self.created + timezone.timedelta(days=self.plan.days)

    def save(self, *args, **kwargs):  # TODO: Move to a receiver
        is_created = not Payment.objects.filter(pk=self.id).exists()
        has_changed_is_accepted = not is_created and Payment.objects.get(pk=self.id).is_accepted != self.is_accepted

        if is_created:
            self.expired = self._calculate_expiration_date()

        super(Payment, self).save(*args, **kwargs)
        if has_changed_is_accepted:
            self.user.vip = True
            self.user.save()

    def is_expired(self) -> bool:
        return self.is_accepted and timezone.now() > self.expired
