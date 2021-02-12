from typing import List, Optional

from trading.domain.entities import Cryptocurrency, Package, CryptocurrencyPrice


class ICryptoCurrencySource:
    def __init__(self, native_currency='EUR'):
        self.native_currency = native_currency

    def get_trading_cryptocurrencies(self) -> List[Cryptocurrency]:
        raise NotImplementedError

    def get_trading_cryptocurrency(self, symbol: str) -> Optional[Cryptocurrency]:
        raise NotImplementedError

    def get_stable_cryptocurrency(self) -> Cryptocurrency:
        raise NotImplementedError

    def get_amount_owned(self, cryptocurrency: Cryptocurrency) -> float:
        raise NotImplementedError

    def get_native_amount_owned(self, cryptocurrency: Cryptocurrency) -> float:
        raise NotImplementedError

    def get_current_sell_price(self, cryptocurrency: Cryptocurrency) -> Optional[float]:
        raise NotImplementedError

    def get_current_buy_price(self, cryptocurrency: Cryptocurrency) -> Optional[float]:
        raise NotImplementedError

    def get_last_month_prices(self, cryptocurrency: Cryptocurrency) -> List[CryptocurrencyPrice]:
        raise NotImplementedError

    def get_all_currency_prices(self) -> dict:
        raise NotImplementedError

    def start_conversions(self):
        raise NotImplementedError

    def finish_conversions(self):
        raise NotImplementedError

    def convert(self, source_cryptocurrency: Cryptocurrency, source_amount: float,
                target_cryptocurrency: Cryptocurrency) -> tuple:
        # must return real_source_amount, target_amount tuple
        raise NotImplementedError


class ILocalStorage:
    def save_package(self, package: Package):
        raise NotImplementedError

    def delete_package(self, package: Package):
        raise NotImplementedError

    def get_package_by_id(self, pk: int) -> Optional[Package]:
        raise NotImplementedError

    def get_cryptocurrency_packages(self, cryptocurrency: Cryptocurrency) -> List[Package]:
        raise NotImplementedError
