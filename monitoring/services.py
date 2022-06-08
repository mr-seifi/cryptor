from _helpers import CacheService
from .models import Action
from django.utils import timezone


class ActionService:

    ACTION_PREFIX = 'A'
    REDIS_KEYS = {
        'action': f'{ACTION_PREFIX}:ACTION:''{action}'
    }

    @classmethod
    def cache_action(cls, user_id, action: str):
        key = cls.REDIS_KEYS.get('action').format(action=action.upper())
        service: CacheService = CacheService()
        service.cache_push(key, f'{user_id}:{timezone.now().timestamp()}')

    @classmethod
    def pop_actions(cls) -> dict:
        all_actions = {key[1]: [] for key in Action.ActionChoices.choices}
        service: CacheService = CacheService()

        for action, label in Action.ActionChoices.choices:
            key = cls.REDIS_KEYS.get('action').format(action=label)
            all_actions[label].append(service.pop(key=key))

        return all_actions
