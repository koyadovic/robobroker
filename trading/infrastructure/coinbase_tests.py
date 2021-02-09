import time
import unittest
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException

from trading.domain.tools.browser import get_current_browser_driver
from trading.infrastructure.coinbase import _get_current_prices_key, _get_previous_prices_key, \
    coinbase_attribute_conv_table, CoinbaseCryptoCurrencySource


class CoinbaseTests(unittest.TestCase):
    def test_get_current_prices_key(self):
        key = _get_current_prices_key(datetime(2020, 1, 1))
        self.assertEqual(key, 'prices_2020_0')
        key = _get_current_prices_key(datetime(2020, 2, 1))
        self.assertEqual(key, 'prices_2020_0')
        key = _get_current_prices_key(datetime(2020, 3, 1))
        self.assertEqual(key, 'prices_2020_1')
        key = _get_current_prices_key(datetime(2020, 4, 1))
        self.assertEqual(key, 'prices_2020_1')
        key = _get_current_prices_key(datetime(2020, 5, 1))
        self.assertEqual(key, 'prices_2020_2')
        key = _get_current_prices_key(datetime(2020, 6, 1))
        self.assertEqual(key, 'prices_2020_2')
        key = _get_current_prices_key(datetime(2020, 7, 1))
        self.assertEqual(key, 'prices_2020_3')
        key = _get_current_prices_key(datetime(2020, 8, 1))
        self.assertEqual(key, 'prices_2020_3')
        key = _get_current_prices_key(datetime(2020, 9, 1))
        self.assertEqual(key, 'prices_2020_4')
        key = _get_current_prices_key(datetime(2020, 10, 1))
        self.assertEqual(key, 'prices_2020_4')
        key = _get_current_prices_key(datetime(2020, 11, 1))
        self.assertEqual(key, 'prices_2020_5')
        key = _get_current_prices_key(datetime(2020, 12, 1))
        self.assertEqual(key, 'prices_2020_5')

    def test_get_previous_prices_key(self):
        key = _get_previous_prices_key(datetime(2020, 1, 1))
        self.assertEqual(key, 'prices_2019_5')
        key = _get_previous_prices_key(datetime(2020, 2, 1))
        self.assertEqual(key, 'prices_2019_5')
        key = _get_previous_prices_key(datetime(2020, 3, 1))
        self.assertEqual(key, 'prices_2020_0')
        key = _get_previous_prices_key(datetime(2020, 4, 1))
        self.assertEqual(key, 'prices_2020_0')
        key = _get_previous_prices_key(datetime(2020, 5, 1))
        self.assertEqual(key, 'prices_2020_1')
        key = _get_previous_prices_key(datetime(2020, 6, 1))
        self.assertEqual(key, 'prices_2020_1')
        key = _get_previous_prices_key(datetime(2020, 7, 1))
        self.assertEqual(key, 'prices_2020_2')
        key = _get_previous_prices_key(datetime(2020, 8, 1))
        self.assertEqual(key, 'prices_2020_2')
        key = _get_previous_prices_key(datetime(2020, 9, 1))
        self.assertEqual(key, 'prices_2020_3')
        key = _get_previous_prices_key(datetime(2020, 10, 1))
        self.assertEqual(key, 'prices_2020_3')
        key = _get_previous_prices_key(datetime(2020, 11, 1))
        self.assertEqual(key, 'prices_2020_4')
        key = _get_previous_prices_key(datetime(2020, 12, 1))
        self.assertEqual(key, 'prices_2020_4')

    def test_logged_in_coinbase(self):
        driver = get_current_browser_driver(headless=True)
        driver.get("https://www.coinbase.com/dashboard")
        with self.assertRaises(NoSuchElementException):
            driver.find_element_by_id("email")
            driver.find_element_by_id("password")
        driver.quit()

    def test_convert_currency(self):
        source: CoinbaseCryptoCurrencySource = CoinbaseCryptoCurrencySource(native_currency='EUR')
        source.start_conversions()
        sour = source.get_trading_cryptocurrency('ALGO')
        target = source.get_trading_cryptocurrency('DAI')
        real_source, real_target = source.convert(sour, 10.0, target, test=True)
        print(real_source, real_target)
        source.finish_conversions()
