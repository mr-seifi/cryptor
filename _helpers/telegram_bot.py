import django

django.setup()
from account.models import User, Trader


class TelegramService:
    MANAGERS = {
        'user': User.objects,
        'trader': Trader.objects
    }

    @staticmethod
    def who_is(user_id) -> str:
        if User.objects.filter(user_id__exact=user_id).exists():
            return 'user'
        elif Trader.objects.filter(user_id__exact=user_id).exists():
            return 'trader'
        return 'anonymous'

    @classmethod
    def get_queryset(cls, user_id):
        return cls.MANAGERS[cls.who_is(user_id)].get(user_id=user_id)
