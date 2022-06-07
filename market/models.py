from django.db import models
from account.models import Trader, User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords


class Signal(models.Model):
    class OrderChoices(models.TextChoices):
        LIMIT = 'limit', 'LIMIT'
        MARKET = 'market', 'MARKET'

    class TypeChoices(models.TextChoices):
        LONG = 'long', 'LONG'
        SHORT = 'short', 'SHORT'

    class RiskChoices(models.TextChoices):
        LOW = 'low', 'LOW'
        MEDIUM = 'medium', 'MEDIUM'
        HIGH = 'high', 'HIGH'

    class TimeframeChoices(models.TextChoices):
        M_1 = '1m', '1M'
        M_5 = '5m', '5M'
        M_15 = '15m', '15M'
        M_30 = '30m', '30M'
        M_45 = '45m', '45M'
        H_1 = '1h', '1H'
        H_2 = '2h', '2H'
        H_3 = '3h', '3H'
        H_4 = '4h', '4H'
        H_8 = '8h', '8H'
        D_1 = '1d', '1D'
        W_1 = '1w', '1W'
        MONTH_1 = '1mo', '1MO'

    class StatusChoices(models.TextChoices):
        NOT_FILLED = 'not_filled', 'NOT_FILLED'
        FILLED = 'filled', 'FILLED'
        TARGETED = 'targeted', 'TARGETED'
        STOPPED = 'stopped', 'STOPPED'

    trader = models.ForeignKey(to=Trader, on_delete=models.CASCADE, related_name='signals')
    pair = models.CharField(max_length=20)
    order_type = models.CharField(choices=OrderChoices.choices, max_length=8)
    type = models.CharField(choices=TypeChoices.choices, max_length=8)
    entry = models.FloatField(max_length=20)
    targets = ArrayField(models.FloatField(max_length=20))
    stop_loss = models.FloatField(max_length=20)
    capital = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    risk = models.CharField(choices=RiskChoices.choices, default=RiskChoices.MEDIUM, max_length=8)
    risk_reward = models.FloatField(blank=True)
    leverage = models.PositiveIntegerField(default=1, validators=[MaxValueValidator(100)])
    timeframe = models.CharField(choices=TimeframeChoices.choices, max_length=8)
    status = models.CharField(choices=StatusChoices.choices, default=StatusChoices.NOT_FILLED, max_length=12)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.pair}:{self.type}'

    def _calculate_risk_reward(self) -> float:
        target_avg = sum(self.targets) / len(self.targets)
        return abs((target_avg - self.entry) / (self.entry - self.stop_loss))

    def save(self, *args, **kwargs):
        self.risk_reward = self._calculate_risk_reward()
        super(Signal, self).save(*args, **kwargs)


class Trade(models.Model):

    signal = models.ForeignKey(to=Signal, on_delete=models.CASCADE, related_name='trades')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='trades')
    net = models.FloatField(blank=True, max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
