import os
import time
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import List, Optional

import pytz
import requests
from coinbase.wallet.error import NotFoundError
from requests.auth import HTTPBasicAuth

from shared.domain.configurations import server_get, server_set
from shared.domain.periodic_tasks import schedule
from trading.domain.entities import Cryptocurrency, CryptocurrencyPrice
from trading.domain.interfaces import ICryptoCurrencySource
from coinbase.wallet.client import Client

from trading.domain.tools.browser import get_current_browser_driver
from trading.domain.tools.executions import execution_with_attempts
from trading.domain.tools.money import two_decimals_floor

coinbase_attribute_conv_table = {
    'BTC': 'convert-to-select-bitcoin',
    'ETH': 'convert-to-select-ethereum',
    'LTC': 'convert-to-select-litecoin',
    'BCH': 'convert-to-select-bitcoin-cash',
    'EOS': 'convert-to-select-eos',
    'XLM': 'convert-to-select-stellar',
    'ETC': 'convert-to-select-ethereum-classic',
    'ZEC': 'convert-to-select-zcash',
    'BAT': 'convert-to-select-basic-attention-token',
    'REP': 'convert-to-select-augur',
    'ZRX': 'convert-to-select-0x',
    'DAI': 'convert-to-select-dai',
    'MANA': 'convert-to-select-decentraland',
    'DNT': 'convert-to-select-district0x',
    'CVC': 'convert-to-select-civic',
    'MKR': 'convert-to-select-maker',
    'OMG': 'convert-to-select-omg-network',
    'KNC': 'convert-to-select-kyber-network',
    'LINK': 'convert-to-select-chainlink',
    'XTZ': 'convert-to-select-tezos',
    'DASH': 'convert-to-select-dash',
    'ATOM': 'convert-to-select-cosmos',
    'BAND': 'convert-to-select-band-protocol',
    'NMR': 'convert-to-select-numeraire',
    'OXT': 'convert-to-select-orchid',
    'COMP': 'convert-to-select-compound',
    'CGLD': 'convert-to-select-celo',
    'YFI': 'convert-to-select-yearn-finance',
    'UNI': 'convert-to-select-uniswap',
    'LRC': 'convert-to-select-loopring',
    'UMA': 'convert-to-select-uma',
    'BAL': 'convert-to-select-balancer',
    'REN': 'convert-to-select-ren',
    'WBTC': 'convert-to-select-wrapped-bitcoin',
    'NU': 'convert-to-select-nucypher',
    'FIL': 'convert-to-select-filecoin',
    'AAVE': 'convert-to-select-aave',
    'GRT': 'convert-to-select-the-graph',
    'BNT': 'convert-to-select-bancor-network-token',
    'SNX': 'convert-to-select-synthetix-network-token',
}


class CoinbaseCryptoCurrencySource(ICryptoCurrencySource):
    driver = None

    @property
    def _client(self):
        api_key = os.environ['API_KEY']
        api_secret = os.environ['API_SECRET']
        return Client(api_key, api_secret, api_version='2016-04-12')

    def get_trading_cryptocurrencies(self) -> List[Cryptocurrency]:
        ignored_coinbase_currencies_data = server_get('ignored_coinbase_currencies', default_data={'items': []}).data
        ignored_coinbase_currencies = ignored_coinbase_currencies_data.get('items')

        now_ts = pytz.utc.localize(datetime.utcnow()).timestamp()
        trading_cryptocurrencies_data = server_get('trading_cryptocurrencies', default_data={}).data
        last_ts = trading_cryptocurrencies_data.get('ts', None)
        cryptocurrencies = trading_cryptocurrencies_data.get('cryptocurrencies', [])
        if not (last_ts is not None and last_ts + (3600*24) > now_ts):
            accounts = self._client.get_accounts(limit=100).data
            cryptocurrencies = []
            for account in accounts:
                symbol = account.balance.currency
                if symbol in ignored_coinbase_currencies:
                    continue
                cryptocurrencies.append({
                    'symbol': symbol,
                    'metadata': {'id': account.id}
                })
            server_set('trading_cryptocurrencies', {
                'ts': now_ts,
                'cryptocurrencies': cryptocurrencies
            })
        return [Cryptocurrency(**c) for c in cryptocurrencies]

    def get_trading_cryptocurrency(self, symbol: str) -> Optional[Cryptocurrency]:
        for currency in self.get_trading_cryptocurrencies():
            if currency.symbol == symbol:
                return currency
        return None

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
        return self._get_last_month_prices_remote(cryptocurrency)

        # if cryptocurrency is None:
        #     return []
        #
        # now = pytz.utc.localize(datetime.utcnow())
        #
        # current_prices_data = server_get(_get_current_prices_key(), default_data={}).data
        # previous_prices_data = server_get(_get_previous_prices_key(), default_data={}).data
        #
        # current_prices = current_prices_data.get('current_prices', [])
        # current_prices += previous_prices_data.get('current_prices', [])
        #
        # native_prices = []
        # for price in current_prices:
        #     if price['symbol'] != cryptocurrency.symbol:
        #         continue
        #     instant = pytz.utc.localize(datetime.utcfromtimestamp(price['instant']))
        #     if instant < now - timedelta(days=30):
        #         continue
        #     native_prices.append(CryptocurrencyPrice(
        #         symbol=price['symbol'],
        #         instant=instant,
        #         sell_price=price['sell_price'],
        #         buy_price=price['buy_price'],
        #     ))
        # native_prices.sort(key=lambda p: p.instant)
        # return native_prices
    
    def _get_last_month_prices_remote(self, cryptocurrency: Cryptocurrency):
        auth = HTTPBasicAuth(os.environ.get('REMOTE_USER'), os.environ.get('REMOTE_PASS'))
        try:
            response = requests.get(f'https://rob.idiet.fit/api/month-prices/{cryptocurrency.symbol}/', auth=auth)
        except Exception as e:
            print(e)
            return []

        data = response.json()
        return [CryptocurrencyPrice(
            symbol=p['symbol'],
            instant=pytz.utc.localize(datetime.utcfromtimestamp(p['instant'])),
            sell_price=p['sell_price'],
            buy_price=p['buy_price'],
        ) for p in data]

    def start_conversions(self):
        # TODO test login
        # TODO get headless from database setting
        self.driver = get_current_browser_driver(headless=False)

    def finish_conversions(self):
        self.driver.quit()

    @execution_with_attempts(attempts=3)
    def convert(self, source_cryptocurrency: Cryptocurrency, source_amount: float,
                target_cryptocurrency: Cryptocurrency, test=False) -> float:

        target_cryptocurrency_html_element_attr = coinbase_attribute_conv_table[target_cryptocurrency.symbol]

        sell_price = self.get_current_sell_price(source_cryptocurrency)
        buy_price = self.get_current_buy_price(source_cryptocurrency)
        current_price = (sell_price + buy_price) / 2.0

        source_id = source_cryptocurrency.metadata.get("id", None)
        if source_id is None:
            source_id = self._client.get_account(source_cryptocurrency.symbol).id

        auto_finish = False
        if self.driver is None:
            auto_finish = True
            self.start_conversions()

        self.driver.get(f'https://www.coinbase.com/accounts/{source_id}')

        time.sleep(5)

        # Vista detallada
        for element in self.driver.find_elements_by_css_selector('div[data-is-active="0"]'):
            if element.text.lower().strip() == 'vista detallada':
                element.click()
                break
        else:
            raise Exception()

        # convertir!
        for element in self.driver.find_elements_by_css_selector('div[data-element-handle="folder-tab-convert"]'):
            if element.is_displayed():
                element.click()
                break
        else:
            raise Exception()

        # click en cambiar moneda
        # convert-to-selector
        for element in self.driver.find_elements_by_css_selector('div[data-element-handle="convert-to-selector"]'):
            if element.is_displayed():
                element.click()
                break
        else:
            raise Exception()

        # find the currency
        self.driver.find_element_by_xpath(
            '//div[@data-element-handle="' + target_cryptocurrency_html_element_attr + '"]').click()

        # introduces cantidad
        real_source_amount = None
        for element in self.driver.find_elements_by_css_selector('input[minlength="1"]'):
            if element.is_displayed():
                element.click()
                native_amount = (source_amount * current_price) + 0.1
                while real_source_amount is None or real_source_amount > source_amount:
                    element.clear()
                    element.send_keys(two_decimals_floor(native_amount))
                    time.sleep(2)
                    convert_from_element = self.driver.find_element_by_css_selector('div[data-element-handle="convert-from-selector"]')
                    for paragraph_element in convert_from_element.find_elements_by_xpath('.//p'):
                        if source_cryptocurrency.symbol in paragraph_element.text:
                            real_value = str(paragraph_element.text.split(source_cryptocurrency.symbol)[0]).strip()
                            real_value = real_value.replace(',', '.')
                            real_source_amount = float(real_value)
                            if real_source_amount > source_amount:
                                native_amount -= 0.05
                            break
                    else:
                        raise Exception(f'Cannot find paragraph with real source amount')
                break
        else:
            raise Exception()

        # vista previa de la conversión
        self.driver.find_element_by_css_selector('button[data-element-handle="convert-preview-button"]').click()

        time.sleep(15)

        # convertir ahora
        convert_button = self.driver.find_elements_by_css_selector('button[data-element-handle="convert-confirm-button"]')
        if not test:
            convert_button.click()

        if auto_finish:
            self.finish_conversions()
        return real_source_amount

    def _get_account_id(self, currency: Cryptocurrency):
        id_ = currency.metadata.get('id')
        if id_ is not None:
            return id_
        account = self._client.get_account(currency.symbol)
        currency.metadata['id'] = account.id
        return account.id


def _get_current_prices_key(now=None):
    now = now or pytz.utc.localize(datetime.utcnow())
    year = now.year
    month = now.month - 1
    if month < 0:
        month += 12
        year -= 1
    month = month // 2
    current_key = f'prices_{year}_{month}'
    return current_key


def _get_previous_prices_key(now=None):
    now = now or pytz.utc.localize(datetime.utcnow())
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
    now = pytz.utc.localize(datetime.utcnow())
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
        try:
            sell_price = trading_source.get_current_sell_price(cryptocurrency)
            buy_price = trading_source.get_current_buy_price(cryptocurrency)
        except JSONDecodeError:
            continue
        if sell_price is None or buy_price is None:
            continue
        now = pytz.utc.localize(datetime.utcnow())
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
