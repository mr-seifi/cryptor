from django.utils import timezone
from cryptor.settings import RELEASE_DATE


class DateTimeService:

    @staticmethod
    def diff_days(since=RELEASE_DATE, until=timezone.now()) -> int:
        return (until - since).days
