from redis import Redis
from .singleton import singleton
from django.conf import settings


@singleton
class RedisClient:

    def __init__(self):
        self.client = Redis(settings.REDIS_HOST,
                            settings.REDIS_PORT)


def get_redis_client() -> Redis:
    return RedisClient().client
