import os
from typing import List

from trading.domain.entities import Cryptocurrency
from trading.domain.interfaces import ICryptoCurrencySource
from coinbase.wallet.client import Client

# Clave de API: yd6NvRoFxxs49ltF

"""
Clave de API: l2K0zrPHmNpoqYLF

Secreto de API: 88d3YY1J6zLurU4yvtKihLBrMIJxDMp8
"""

c = Client('Rmy8oFA5O3RwCUnJ', 'ov04t7dpzlHV36Jznt4Zjp6JIYdI9zp2', api_version='2016-04-12')
c.send_money()
c.transfer_money()


class CoinbaseCryptoCurrencySource(ICryptoCurrencySource):
    def __init__(self):
        api_key = os.environ['API_KEY']
        api_secret = os.environ['API_SECRET']
        self.client = Client(api_key, api_secret, api_version='2016-04-12')

    def get_trading_cryptocurrencies(self) -> List[Cryptocurrency]:
        pass

    def get_stable_cryptocurrency(self) -> Cryptocurrency:
        pass

    def get_amount_owned(self, cryptocurrency) -> float:
        pass

    def get_current_sell_price(self, cryptocurrency, common_currency) -> float:
        pass

    def get_current_buy_price(self, cryptocurrency, common_currency) -> float:
        pass

    def get_last_month_prices(self, cryptocurrency, common_currency) -> List[dict]:
        pass

    def convert(self, source_cryptocurrency, source_amount, target_cryptocurrency):
        pass
