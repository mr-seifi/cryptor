from .models import Action
from .services import ActionService


class ActionTask:

    # ApplyAsync Per 1 Hour
    @staticmethod
    def insert_actions():
        actions = ActionService.pop_actions()
        events = [{'action': key,
                   'user_id': actions[key].split(':')[0],
                   'created': actions[key].split(':')[1]} for key in actions]

        Action.objects.bulk_create(events)
