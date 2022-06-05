from .models import Signal, Trade
from _helpers import singleton, DateTimeService
from cryptor.settings import RELEASE_DATE
from django.utils import timezone
from django.db.models import Min, Sum


@singleton
class MarketService:

    @staticmethod
    def calculate_signals(start=RELEASE_DATE, end=timezone.now, queryset=None) -> int:
        if queryset:
            return queryset.filter(created__gte=start, created__lte=end).count()
        return Signal.objects.filter(created__gte=start, created__lte=end).count()

    @classmethod
    def calculate_daily_signals(cls, queryset=None) -> int:
        return cls.calculate_signals(start=timezone.now() - timezone.timedelta(days=1),
                                     end=timezone.now(),
                                     queryset=queryset)

    @classmethod
    def calculate_weekly_signals(cls, queryset=None) -> int:
        return cls.calculate_signals(start=timezone.now() - timezone.timedelta(days=7),
                                     end=timezone.now(),
                                     queryset=queryset)

    @classmethod
    def calculate_monthly_signals(cls, queryset=None) -> int:
        return cls.calculate_signals(start=timezone.now() - timezone.timedelta(days=30),
                                     end=timezone.now(),
                                     queryset=queryset)

    @classmethod
    def calculate_spd(cls, queryset=None) -> float:
        """
        SPD: Signal per Day
        :param queryset: Signal queryset to specify signals
        :return: float
        """
        signals = cls.calculate_signals(queryset=queryset)
        since = RELEASE_DATE
        if queryset and queryset.exists():
            since = queryset.aggregate(Min('created')).get('created__min')
        days = DateTimeService.diff_days(since=since)
        return signals / days

    @staticmethod
    def calculate_net(start=RELEASE_DATE, end=timezone.now, queryset=None) -> float:
        if queryset:
            return queryset.filter(created__gte=start, created__lte=end).aggregate(s=Sum('net'))['s'] or 0
        return Trade.objects.filter(created__gte=start, created__lte=end).aggregate(s=Sum('net'))['s'] or 0

    @classmethod
    def calculate_daily_net(cls, queryset=None) -> float:
        return cls.calculate_net(start=timezone.now() - timezone.timedelta(days=1),
                                 end=timezone.now(),
                                 queryset=queryset)

    @classmethod
    def calculate_weekly_net(cls, queryset=None) -> float:
        return cls.calculate_net(start=timezone.now() - timezone.timedelta(days=7),
                                 end=timezone.now(),
                                 queryset=queryset)

    @classmethod
    def calculate_monthly_net(cls, queryset=None) -> float:
        return cls.calculate_net(start=timezone.now() - timezone.timedelta(days=30),
                                 end=timezone.now(),
                                 queryset=queryset)
