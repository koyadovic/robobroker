import os
from datetime import datetime, timedelta
from typing import List

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
        trading_cryptocurrencies_data = server_get('trading_cryptocurrencies').data
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
        stable_cryptocurrency = server_get('stable_cryptocurrency').data
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

    def get_current_sell_price(self, cryptocurrency: Cryptocurrency) -> float:
        response = self._client.get_buy_price(currency_pair=f'{cryptocurrency.symbol}-{self.native_currency}')
        return float(response.amount)

    def get_current_buy_price(self, cryptocurrency: Cryptocurrency) -> float:
        response = self._client.get_buy_price(currency_pair=f'{cryptocurrency.symbol}-{self.native_currency}')
        return float(response.amount)

    def get_last_month_prices(self, cryptocurrency: Cryptocurrency) -> List[CryptocurrencyPrice]:
        now = datetime.utcnow()

        current_prices_data = server_get(_get_current_prices_key()).data
        previous_prices_data = server_get(_get_previous_prices_key()).data

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
        response = self._client.transfer_money(source_cryptocurrency.metadata.get('id'),
                                               to=target_cryptocurrency.metadata.get('id'),
                                               amount=formatted_amount, currency=source_cryptocurrency.symbol)


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


def fetch_prices():
    trading_source: ICryptoCurrencySource = CoinbaseCryptoCurrencySource()
    current_prices_data = server_get(_get_current_prices_key()).data
    current_prices = current_prices_data.get('current_prices', [])

    for cryptocurrency in trading_source.get_trading_cryptocurrencies():
        sell_price = trading_source.get_current_sell_price(cryptocurrency)
        buy_price = trading_source.get_current_buy_price(cryptocurrency)
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


@schedule(minute='0', unique_name='fetch_prices_0')
def _fetch_0():
    fetch_prices()


@schedule(minute='5', unique_name='fetch_prices_5')
def _fetch_5():
    fetch_prices()


@schedule(minute='10', unique_name='fetch_prices_10')
def _fetch_10():
    fetch_prices()


@schedule(minute='15', unique_name='fetch_prices_15')
def _fetch_15():
    fetch_prices()


@schedule(minute='20', unique_name='fetch_prices_20')
def _fetch_20():
    fetch_prices()


@schedule(minute='25', unique_name='fetch_prices_25')
def _fetch_25():
    fetch_prices()


@schedule(minute='30', unique_name='fetch_prices_30')
def _fetch_30():
    fetch_prices()


@schedule(minute='35', unique_name='fetch_prices_35')
def _fetch_35():
    fetch_prices()


@schedule(minute='40', unique_name='fetch_prices_40')
def _fetch_40():
    fetch_prices()


@schedule(minute='45', unique_name='fetch_prices_45')
def _fetch_45():
    fetch_prices()


@schedule(minute='50', unique_name='fetch_prices_50')
def _fetch_50():
    fetch_prices()


@schedule(minute='55', unique_name='fetch_prices_55')
def _fetch_55():
    fetch_prices()
