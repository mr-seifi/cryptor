from django.db import models
from account.models import User
from simple_history.models import HistoricalRecords
from .services import KuCoinService
from market.models import Signal


class KuCoin(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='kucoin')
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    api_passphrase = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    @property
    def _service(self) -> KuCoinService:
        return KuCoinService()

    @property
    def _authenticate(self):
        return dict(api_key=self.api_key,
                    api_secret=self.api_secret,
                    api_passphrase=self.api_passphrase)

    def get_account_overview(self, **kwargs):
        return self._service.get_account_overview(**self._authenticate, **kwargs)

    def get_balance(self, currency='USDT') -> float:
        return self._service.get_balance(**self._authenticate, currency=currency)

    def get_order_list(self, **kwargs):
        return self._service.get_order_list(**self._authenticate, **kwargs)

    def get_lot_size(self, signal: Signal, balance: float) -> float:
        return self._service.get_lot_size(**self._authenticate,
                                          symbol=signal.pair,
                                          balance=balance,
                                          price=signal.entry,
                                          leverage=signal.leverage)

    def get_usable_balance(self, signal: Signal, currency='USDT') -> float:
        balance = self.get_balance(currency=currency)
        return balance * (self.user.cap, signal.capital)[not self.user.cap]

    def execute_signal(self, signal: Signal):
        usable_balance = self.get_usable_balance(signal=signal)
        return self._service.execute_signal(signal=signal, user=self.user, usable_balance=usable_balance)

    def get_active_contracts(self, **kwargs):
        return self._service.get_active_contracts(**self._authenticate, **kwargs)

