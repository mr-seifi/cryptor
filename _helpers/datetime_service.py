from django.utils import timezone
from cryptor.settings import DEV_DATE


class DateTimeService:

    @staticmethod
    def diff_days(since=DEV_DATE, until=timezone.now()) -> int:
        return (until - since).days
