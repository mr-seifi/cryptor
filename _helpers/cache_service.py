from .redis_client import get_redis_client
from .singleton import singleton


@singleton
class CacheService:

    def __init__(self):
        self.client = get_redis_client()

    def cache(self, key: str, value: str, ex: int):
        self.client.set(name=key,
                        value=value,
                        ex=ex)

    def get(self, key: str):
        return self.client.get(name=key)

    def cache_push(self, key: str, value: str):
        self.client.lpush(key, value)

    def len(self, key: str):
        return self.client.llen(name=key)

    def pop(self, key: str):
        result = [value.decode() for value in self.client.lrange(key, 0, self.len(key)) if value]
        self.client.delete(key)
        return result
