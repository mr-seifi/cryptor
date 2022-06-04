import logging
from .models import User
from .services import AccountService


def update_vip_status():
    service: AccountService = AccountService()

    expired = []
    for user in User.objects.vip():
        if not service.check_vip(user):
            expired.append(user.id)

    User.objects.filter(user_id__in=expired).update(vip=False)
    logging.info('user status updated!', extra={'count': len(expired)})
