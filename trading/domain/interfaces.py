from typing import List

from trading.domain.entities import Cryptocurrency


class ICryptoCurrencySource:
    def get_trading_cryptocurrencies(self) -> List[Cryptocurrency]:
        raise NotImplementedError

    def get_stable_cryptocurrency(self) -> Cryptocurrency:
        raise NotImplementedError

    def get_amount_owned(self, cryptocurrency) -> float:
        raise NotImplementedError

    def get_current_sell_price(self, cryptocurrency, common_currency) -> float:
        raise NotImplementedError

    def get_current_buy_price(self, cryptocurrency, common_currency) -> float:
        raise NotImplementedError

    def get_last_month_prices(self, cryptocurrency, common_currency) -> List[dict]:  # TODO crear entidad para esto
        raise NotImplementedError

    def convert(self, source_cryptocurrency, source_amount, target_cryptocurrency):  # si todo OK, crear paquete
        raise NotImplementedError
