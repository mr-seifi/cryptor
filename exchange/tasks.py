from .services import KuCoinService
from market.models import Signal
from concurrent.futures import ThreadPoolExecutor
from account.models import User


class KuCoinTasks:

    @staticmethod
    def refresh_session():
        service: KuCoinService = KuCoinService()
        service.refresh_session()

    @staticmethod
    def _trade(signal: Signal, user: User):
        user.kucoin.execute_signal(signal)

    @classmethod
    def trade(cls, signal: Signal):
        users = signal.trader.army.active()

        with ThreadPoolExecutor() as executor:
            executor.map(cls._trade, [signal] * users.count(), users)
