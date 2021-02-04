import time
import unittest
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException

from trading.domain.tools.browser import get_current_browser_driver
from trading.infrastructure.coinbase import _get_current_prices_key, _get_previous_prices_key, \
    coinbase_attribute_conv_table


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
        # import ipdb;  ipdb.set_trace(context=10)
        driver = get_current_browser_driver(headless=False)
        driver.get("https://www.coinbase.com/accounts/b0f3f75f-f229-50db-9266-46b89aa6ee5a")

        time.sleep(5)

        # Vista detallada
        for element in driver.find_elements_by_css_selector('div[data-is-active="0"]'):
            if element.text.lower().strip() == 'vista detallada':
                element.click()
                break
        else:
            raise Exception()

        # convertir!
        for element in driver.find_elements_by_css_selector('div[data-element-handle="folder-tab-convert"]'):
            if element.is_displayed():
                element.click()
                break
        else:
            raise Exception()

        # click en cambiar moneda
        # convert-to-selector
        for element in driver.find_elements_by_css_selector('div[data-element-handle="convert-to-selector"]'):
            if element.is_displayed():
                element.click()
                break
        else:
            raise Exception()

        # find the currency
        attr = coinbase_attribute_conv_table['AAVE']
        driver.find_element_by_xpath('//div[@data-element-handle="' + attr + '"]').click()

        # introduces cantidad
        for element in driver.find_elements_by_css_selector('input[minlength="1"]'):
            if element.is_displayed():
                element.click()
                element.send_keys('12.12')
                break
        else:
            raise Exception()

        # vista previa de la conversión
        driver.find_element_by_css_selector('button[data-element-handle="convert-preview-button"]').click()

        # convertir ahora
        convert_button = driver.find_elements_by_css_selector('button[data-element-handle="convert-confirm-button"]')
        # convert_button.click()
        driver.quit()
