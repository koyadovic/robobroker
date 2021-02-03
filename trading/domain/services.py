from datetime import datetime, timedelta

from shared.domain.configurations import server_get
from shared.domain.dependencies import dependency_dispatcher
from shared.domain.periodic_tasks import schedule
from shared.domain.system_logs import add_system_log
from trading.domain.entities import Cryptocurrency, Package
from trading.domain.interfaces import ILocalStorage, ICryptoCurrencySource
from trading.domain.tools import profit_difference_percentage

from typing import List

import statistics
import math

COMMON_CURRENCY = 'EUR'


def trade():
    enable_trading_data = server_get('enable_trading', default_data={'activated': False}).data
    enable_trading = enable_trading_data.get('activated')
    if not enable_trading:
        return

    """
    El proceso es:
    1.- El Discriminator cataloga candidates_for_purchase y candidates_for_sell
    2.- Primero se ejecuta una a una check_sell(single_candidate_for_sell)
    3.- Se finaliza llamando check_purchase(candidates_for_purchase)
    """
    for_sell, for_purchase = _discriminate_by_sell_and_purchase()
    for currency in for_sell:
        _check_sell(currency)
    _check_buy(for_purchase)


def _discriminate_by_sell_and_purchase():
    # get_trading_cryptocurrencies
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    for_sell = []
    for_purchase = []

    now = datetime.utcnow()
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    for currency in trading_cryptocurrencies:
        prices = trading_source.get_last_month_prices(currency)
        last_week_prices = [price for price in prices if now - timedelta(days=7) <= price.instant]
        last_6h_prices = [price for price in prices if now - timedelta(hours=6) <= price.instant]

        # Si el precio actual está por encima del precio mediano + stdev último mes,
        # y la rentabilidad 6h es < 0, vender!
        current_sell_price = trading_source.get_current_sell_price(currency)
        sell_prices = [price.sell_price for price in prices]
        sell_prices_median = statistics.median(sell_prices)
        sell_prices_stdev = statistics.stdev(sell_prices)
        last_6h_profit = profit_difference_percentage(last_6h_prices[0].sell_price, last_6h_prices[-1].sell_price)
        if current_sell_price > sell_prices_median + sell_prices_stdev and last_6h_profit < 5:
            for_sell.append(currency)
            continue

        # Si el precio actual está por debajo del precio mediano - stdev último mes,
        # y la rentabilidad 6h es > 0, comprar!
        current_buy_price = trading_source.get_current_buy_price(currency)
        buy_prices = [price.buy_price for price in prices]
        buy_prices_median = statistics.median(buy_prices)
        buy_prices_stdev = statistics.stdev(buy_prices)
        last_6h_profit = profit_difference_percentage(last_6h_prices[0].buy_price, last_6h_prices[-1].buy_price)
        if current_buy_price < buy_prices_median - buy_prices_stdev and last_6h_profit > 5:
            for_purchase.append(currency)
            continue

        # TODO pensar en esto
        # last_week_profit = profit_difference_percentage(last_week_prices[0].buy_price, last_week_prices[-1].buy_price)
        # if last_week_profit > 5 and last_6h_profit > 5:
        #     for_purchase.append(currency)
        #     continue

        print(f'{currency} untouched. '
              f'sell_prices_median: {sell_prices_median}, current_sell_price: {current_sell_price}, '
              f'buy_prices_median: {buy_prices_median}, current_buy_price: {current_buy_price}, ')

    # TODO si tenemos currencies por un determinado tiempo que no vendemos y que no sacamos rentabilidad
    #  tocaría vender sí o sí.

    return for_sell, for_purchase


def _check_sell(candidate_currency: Cryptocurrency):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    packages = storage.get_cryptocurrency_packages(candidate_currency)
    amount = 0.0

    current_sell_price = trading_source.get_current_sell_price(candidate_currency)

    delete_packages = []
    for package in packages:
        profit_difference = profit_difference_percentage(package.bought_at_price, current_sell_price)
        if profit_difference > 10.0:
            delete_packages.append(package)
            amount += package.currency_amount

    if amount > 0.0:
        amount = math.floor(amount * 100.0) / 100.0
        target = trading_source.get_stable_cryptocurrency()
        trading_source.convert(candidate_currency, amount, target)
        for package in delete_packages:
            storage.delete_package(package)
        add_system_log(f'SELL', f'SELL {candidate_currency.symbol} {amount}')


def _check_buy(candidate_currencies: List[Cryptocurrency]):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    # stable currency
    source_cryptocurrency = trading_source.get_stable_cryptocurrency()
    source_amount = trading_source.get_amount_owned(source_cryptocurrency)
    if round(source_amount) <= 1:
        return

    parts = len(candidate_currencies)
    # queremos diversificación, no jugárnosla convirtiendo all a una única moneda
    if parts < 3:
        parts = 3
    source_fragment_amount = math.floor((source_amount / parts) * 100.0) / 100.0

    for target_currency in candidate_currencies:
        trading_source.convert(source_cryptocurrency, source_fragment_amount, target_currency)
        target_currency_buy_price = trading_source.get_current_buy_price(target_currency)
        package = Package(
            currency_symbol=target_currency.symbol,
            currency_amount=source_fragment_amount,
            bought_at_price=target_currency_buy_price,
            operation_datetime=datetime.utcnow(),
        )
        storage.save_package(package)
        add_system_log(f'BUY', f'BUY {target_currency.symbol} {source_fragment_amount}')


@schedule(hour='0', unique_name='trade_0')
def _trade_0():
    trade()


@schedule(hour='2', unique_name='trade_2')
def _trade_2():
    trade()


@schedule(hour='4', unique_name='trade_4')
def _trade_4():
    trade()


@schedule(hour='6', unique_name='trade_6')
def _trade_6():
    trade()


@schedule(hour='8', unique_name='trade_8')
def _trade_8():
    trade()


@schedule(hour='10', unique_name='trade_10')
def _trade_10():
    trade()


@schedule(hour='12', unique_name='trade_12')
def _trade_12():
    trade()


@schedule(hour='14', unique_name='trade_14')
def _trade_14():
    trade()


@schedule(hour='16', unique_name='trade_16')
def _trade_16():
    trade()


@schedule(hour='18', unique_name='trade_18')
def _trade_18():
    trade()


@schedule(hour='20', unique_name='trade_20')
def _trade_20():
    trade()


@schedule(hour='22', unique_name='trade_22')
def _trade_22():
    trade()
