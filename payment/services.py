from .models import Payment
from _helpers import singleton, DateTimeService
from django.db.models import Min, Sum
from django.utils import timezone
from cryptor.settings import RELEASE_DATE


@singleton
class PaymentService:

    @staticmethod
    def calculate_payments(start=RELEASE_DATE, end=timezone.now, queryset=None) -> int:
        if queryset:
            return queryset.filter(created__gte=start, created__lte=end).count()
        return Payment.objects.filter(created__gte=start, created__lte=end).count()

    @classmethod
    def calculate_daily_payments(cls, queryset=None) -> int:
        return cls.calculate_payments(start=timezone.now() - timezone.timedelta(days=1),
                                      end=timezone.now(),
                                      queryset=queryset)

    @classmethod
    def calculate_weekly_payments(cls, queryset=None) -> int:
        return cls.calculate_payments(start=timezone.now() - timezone.timedelta(days=7),
                                      end=timezone.now(),
                                      queryset=queryset)

    @classmethod
    def calculate_monthly_payments(cls, queryset=None) -> int:
        return cls.calculate_payments(start=timezone.now() - timezone.timedelta(days=30),
                                      end=timezone.now(),
                                      queryset=queryset)

    @classmethod
    def calculate_ppd(cls, queryset=None) -> float:
        """
        PPD: Payment per Day
        :param queryset: Payment queryset to specify payments
        :return: float
        """
        payments = cls.calculate_payments(queryset=queryset)
        since = RELEASE_DATE
        if queryset and queryset.exists():
            since = queryset.aggregate(Min('created')).get('created__min')
        days = DateTimeService.diff_days(since=since)
        return payments / days

    @staticmethod
    def calculate_income(start=RELEASE_DATE, end=timezone.now, queryset=None) -> float:
        if queryset:
            return queryset.filter(created__gte=start, created__lte=end).aggregate(sum=Sum('plan__price'))['sum'] or 0
        return Payment.objects.filter(created__gte=start, created__lte=end).aggregate(sum=Sum('plan__price'))['sum'] or 0

    @classmethod
    def calculate_daily_income(cls, queryset=None) -> float:
        return cls.calculate_income(start=timezone.now() - timezone.timedelta(days=1),
                                    end=timezone.now(),
                                    queryset=queryset)

    @classmethod
    def calculate_weekly_income(cls, queryset=None) -> float:
        return cls.calculate_income(start=timezone.now() - timezone.timedelta(days=7),
                                    end=timezone.now(),
                                    queryset=queryset)

    @classmethod
    def calculate_monthly_income(cls, queryset=None) -> float:
        return cls.calculate_income(start=timezone.now() - timezone.timedelta(days=30),
                                    end=timezone.now(),
                                    queryset=queryset)

