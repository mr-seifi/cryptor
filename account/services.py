from .models import User
from _helpers import singleton, DateTimeService, CacheService
from django.utils import timezone
from cryptor.settings import RELEASE_DATE
from django.db.models import Min


@singleton
class AccountService:

    @staticmethod
    def calculate_signups(start=RELEASE_DATE, end=timezone.now, queryset=None) -> int:
        if queryset:
            return queryset.filter(created__gte=start, created__lte=end).count()
        return User.objects.filter(created__gte=start, created__lte=end).count()

    @classmethod
    def calculate_daily_signups(cls, queryset=None) -> int:
        return cls.calculate_signups(start=timezone.now() - timezone.timedelta(days=1),
                                     end=timezone.now(),
                                     queryset=queryset)

    @classmethod
    def calculate_weekly_signups(cls, queryset=None) -> int:
        return cls.calculate_signups(start=timezone.now() - timezone.timedelta(days=7),
                                     end=timezone.now(),
                                     queryset=queryset)

    @classmethod
    def calculate_monthly_signups(cls, queryset=None) -> int:
        return cls.calculate_signups(start=timezone.now() - timezone.timedelta(days=30),
                                     end=timezone.now(),
                                     queryset=queryset)

    @staticmethod
    def calculate_actives(queryset=None) -> int:
        if queryset:
            return queryset.active().filter().count()
        return User.objects.active().filter().count()

    @classmethod
    def calculate_sgpd(cls, queryset=None) -> float:
        """
        SGPD: Signup per Day
        :param queryset: User queryset to specify signups
        :return: float
        """
        signups = cls.calculate_signups(queryset=queryset)
        since = RELEASE_DATE
        if queryset and queryset.exists():
            since = queryset.aggregate(Min('created')).get('created__min')
        days = DateTimeService.diff_days(since=since)
        return signups / days

    @staticmethod
    def check_vip(user: User) -> bool:
        if not user.payments.exists():
            return False
        last_payment = user.payments.last()
        if last_payment.is_accepted and not last_payment.is_expired():
            return True
        return False


class ProfileService:

    PROFILE_PREFIX = 'P'
    REDIS_KEYS = {
        'wallet_network': f'{PROFILE_PREFIX}:WALLET:''{user_id}',
        'api_key': f'{PROFILE_PREFIX}:API_KEY:''{user_id}',
        'api_secret': f'{PROFILE_PREFIX}:API_SECRET:''{user_id}',
    }
    EX = 60 * 60

    @classmethod
    def _cache(cls, key, user_id, value):
        key = cls.REDIS_KEYS[key].format(user_id=user_id)
        service: CacheService = CacheService()
        service.cache(key=key, value=value, ex=cls.EX)

    @classmethod
    def _get(cls, key, user_id):
        key = cls.REDIS_KEYS[key].format(user_id=user_id)
        service: CacheService = CacheService()
        return service.get(key=key)

    @classmethod
    def cache_wallet_network(cls, user_id, wallet_network):
        cls._cache(key='wallet_network', user_id=user_id, value=wallet_network)

    @classmethod
    def get_wallet_network(cls, user_id):
        return cls._get(key='wallet_network', user_id=user_id)

    @classmethod
    def cache_api_key(cls, user_id, api_key):
        cls._cache(key='api_key', user_id=user_id, value=api_key)

    @classmethod
    def get_api_key(cls, user_id):
        return cls._get(key='api_key', user_id=user_id)

    @classmethod
    def cache_api_secret(cls, user_id, api_secret):
        cls._cache(key='api_secret', user_id=user_id, value=api_secret)

    @classmethod
    def get_api_secret(cls, user_id):
        return cls._get(key='api_secret', user_id=user_id)
