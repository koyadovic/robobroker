import os
from datetime import datetime, timedelta
from typing import List, Optional

from coinbase.wallet.error import NotFoundError

from shared.domain.configurations import server_get, server_set
from shared.domain.periodic_tasks import schedule
from trading.domain.entities import Cryptocurrency, CryptocurrencyPrice
from trading.domain.interfaces import ICryptoCurrencySource
from coinbase.wallet.client import Client


class CoinbaseCryptoCurrencySource(ICryptoCurrencySource):
    @property
    def _client(self):
        api_key = os.environ['API_KEY']
        api_secret = os.environ['API_SECRET']
        return Client(api_key, api_secret, api_version='2016-04-12')

    def get_trading_cryptocurrencies(self) -> List[Cryptocurrency]:
        now_ts = datetime.utcnow().timestamp()
        trading_cryptocurrencies_data = server_get('trading_cryptocurrencies', default_data={}).data
        last_ts = trading_cryptocurrencies_data.get('ts', None)
        cryptocurrencies = trading_cryptocurrencies_data.get('cryptocurrencies', [])
        if not (last_ts is not None and last_ts + (3600*24) > now_ts):
            accounts = self._client.get_accounts(limit=100).data
            cryptocurrencies = []
            for account in accounts:
                cryptocurrencies.append({
                    'symbol': account.balance.currency,
                    'metadata': {
                        'id': account.id
                    }
                })
            server_set('trading_cryptocurrencies', {
                'ts': now_ts,
                'cryptocurrencies': cryptocurrencies
            })
        return [Cryptocurrency(**c) for c in cryptocurrencies]

    def get_stable_cryptocurrency(self) -> Cryptocurrency:
        stable_cryptocurrency = server_get('stable_cryptocurrency', default_data={}).data
        if len(stable_cryptocurrency.keys()) > 0:
            return Cryptocurrency(**stable_cryptocurrency)
        account = self._client.get_account('DAI')
        stable_cryptocurrency = {
            'symbol': account.balance.currency,
            'metadata': {
                'id': account.id
            }
        }
        server_set('stable_cryptocurrency', stable_cryptocurrency)
        return Cryptocurrency(**stable_cryptocurrency)

    def get_amount_owned(self, cryptocurrency: Cryptocurrency) -> float:
        account = self._client.get_account(cryptocurrency.symbol)
        return float(account.balance.amount)

    def get_current_sell_price(self, cryptocurrency: Cryptocurrency) -> Optional[float]:
        try:
            response = self._client.get_buy_price(currency_pair=f'{cryptocurrency.symbol}-{self.native_currency}')
            return float(response.amount)
        except NotFoundError:
            return None

    def get_current_buy_price(self, cryptocurrency: Cryptocurrency) -> Optional[float]:
        try:
            response = self._client.get_buy_price(currency_pair=f'{cryptocurrency.symbol}-{self.native_currency}')
            return float(response.amount)
        except NotFoundError:
            return None

    def get_last_month_prices(self, cryptocurrency: Cryptocurrency) -> List[CryptocurrencyPrice]:
        now = datetime.utcnow()

        current_prices_data = server_get(_get_current_prices_key(), default_data={}).data
        previous_prices_data = server_get(_get_previous_prices_key(), default_data={}).data

        current_prices = current_prices_data.get('current_prices', [])
        current_prices += previous_prices_data.get('current_prices', [])

        native_prices = []
        for price in current_prices:
            if price['symbol'] != cryptocurrency.symbol:
                continue
            instant = datetime.utcfromtimestamp(price['instant'])
            if instant < now - timedelta(days=30):
                continue
            native_prices.append(CryptocurrencyPrice(
                symbol=price['symbol'],
                instant=instant,
                sell_price=price['sell_price'],
                buy_price=price['buy_price'],
            ))
        native_prices.sort(key=lambda p: p.instant)
        return native_prices

    def convert(self, source_cryptocurrency: Cryptocurrency, source_amount: float,
                target_cryptocurrency: Cryptocurrency):
        formatted_amount = '{:.2f}'.format(source_amount)
        response = self._client.transfer_money(self._get_account_id(source_cryptocurrency),
                                               to=self._get_account_id(target_cryptocurrency),
                                               amount=formatted_amount, currency=source_cryptocurrency.symbol)

    def _get_account_id(self, currency: Cryptocurrency):
        id_ = currency.metadata.get('id')
        if id_ is not None:
            return id_
        account = self._client.get_account(currency.symbol)
        currency.metadata['id'] = account.id
        return account.id


def _get_current_prices_key(now=None):
    now = now or datetime.utcnow()
    year = now.year
    month = now.month - 1
    if month < 0:
        month += 12
        year -= 1
    month = month // 2
    current_key = f'prices_{year}_{month}'
    return current_key


def _get_previous_prices_key(now=None):
    now = now or datetime.utcnow()
    year = now.year
    month = now.month - 1
    if month < 0:
        month += 12
        year -= 1
    month = month // 2
    month -= 1
    if month < 0:
        month = 5
        year -= 1
    current_key = f'prices_{year}_{month}'
    return current_key


@schedule(minute='*', unique_name='fetch_prices', priority=666)
def fetch_prices():
    now = datetime.utcnow()
    if now.minute % 5 != 0:
        return

    enable_fetch_prices_data = server_get('enable_fetch_prices', default_data={'activated': False}).data
    enable_fetch_prices = enable_fetch_prices_data.get('activated')
    if not enable_fetch_prices:
        return

    trading_source: ICryptoCurrencySource = CoinbaseCryptoCurrencySource()
    current_prices_data = server_get(_get_current_prices_key(), default_data={}).data
    current_prices = current_prices_data.get('current_prices', [])

    for cryptocurrency in trading_source.get_trading_cryptocurrencies():
        sell_price = trading_source.get_current_sell_price(cryptocurrency)
        buy_price = trading_source.get_current_buy_price(cryptocurrency)
        if sell_price is None or buy_price is None:
            continue
        now = datetime.utcnow()
        price = {
            'symbol': cryptocurrency.symbol,
            'instant': now.timestamp(),
            'sell_price': sell_price,
            'buy_price': buy_price,
        }
        current_prices.append(price)
        server_set(_get_current_prices_key(), {
            'current_prices': current_prices
        })
