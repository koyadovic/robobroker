from datetime import datetime, timedelta
from json import JSONDecodeError

import pytz
from matplotlib.dates import DateFormatter

from shared.domain.configurations import server_get, server_set
from shared.domain.dependencies import dependency_dispatcher
from shared.domain.periodic_tasks import schedule
from shared.domain.system_logs import add_system_log
from trading.domain.entities import Cryptocurrency, Package
from trading.domain.interfaces import ILocalStorage, ICryptoCurrencySource
import matplotlib.pyplot as plt
from typing import List

import statistics
import math

from trading.domain.tools.money import two_decimals_floor
from trading.domain.tools.prices import PricesQueryset
from trading.domain.tools.stats import profit_difference_percentage

COMMON_CURRENCY = 'EUR'


@schedule(minute='*', unique_name='trade', priority=5)
def sell():
    enable_trading_data = server_get('enable_trading', default_data={'activated': False}).data
    enable_trading = enable_trading_data.get('activated')
    if not enable_trading:
        return

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)

    now = pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()

    trading_source.start_conversions()

    for currency in trading_cryptocurrencies:
        prices = trading_source.get_last_month_prices(currency)
        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            continue

        current_sell_price = prices[-1].sell_price
        packages = storage.get_cryptocurrency_packages(currency)

        """
        1.- Para vender, rentabilidad últimas 4h tendría que ser < -5 y tener paquetes que cumplan:
                + Que alguno ofrezca una rentabilidad de > 20%
                + Que alguno tenga 2 semanas o más con rentabilidad entre 5% y 20%
                + Que tengan más de n meses de antiguedad. Que sea configurable.
        """
        profit_4d = qs.profit_percentage(timedelta(days=4), now=now)
        if profit_4d < -5:
            amount = 0.0
            remove_packages = []
            profits = []

            for package in packages:
                package_profit = profit_difference_percentage(package.bought_at_price, current_sell_price)
                sell_it = False
                if package_profit > 20:
                    sell_it = True
                elif 5 <= package_profit <= 20 and now - timedelta(days=7) >= package.operation_datetime:
                    sell_it = True
                # TODO add auto_sell

                if sell_it:
                    profits.append(package_profit)
                    remove_packages.append(package)
                    amount += package.currency_amount

            if len(profits) == 0:
                profits = [0.0]

            if round(amount) > 0.0:
                amount = two_decimals_floor(amount)
                target = trading_source.get_stable_cryptocurrency()
                trading_source.convert(currency, amount, target)
                for package in remove_packages:
                    storage.delete_package(package)
                add_system_log(f'SELL', f'SELL {currency.symbol} {amount} profit: {statistics.mean(profits)}%')

    trading_source.finish_conversions()


@schedule(minute='0', unique_name='trade', priority=4)
def purchase():
    enable_trading_data = server_get('enable_trading', default_data={'activated': False}).data
    enable_trading = enable_trading_data.get('activated')
    if not enable_trading:
        return

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)

    source_cryptocurrency = trading_source.get_stable_cryptocurrency()
    source_amount = trading_source.get_amount_owned(source_cryptocurrency)
    if round(source_amount) <= 1:
        return

    now = pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    purchase_currency_data = []

    for currency in trading_cryptocurrencies:
        prices = trading_source.get_last_month_prices(currency)
        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            continue

        packages = storage.get_cryptocurrency_packages(currency)
        current_sell_price = prices[-1].sell_price

        native_total = 0
        for package in packages:
            native_total += package.currency_amount * current_sell_price
        if native_total == 0:
            native_total = 1
        profitability = qs.profit_percentage(timedelta(days=7), now=now)
        score = profitability / native_total
        if score < 0:
            purchase_currency_data.append({
                'score': score,
                'currency': currency
            })

    purchase_currency_data.sort(key=lambda item: item['score'])
    for_purchase = [item['currency'] for item in purchase_currency_data[0: 10]]

    parts = len(for_purchase)
    if parts == 0:
        parts = 1
    source_fragment_amount = math.floor((source_amount / parts) * 100.0) / 100.0
    # max of 10 DAI
    if source_fragment_amount > 10:
        source_fragment_amount = 10

    trading_source.start_conversions()

    for target_currency in for_purchase:
        prices = trading_source.get_last_month_prices(target_currency)
        current_buy_price = prices[-1].buy_price
        trading_source.convert(source_cryptocurrency, source_fragment_amount, target_currency)
        package = Package(
            currency_symbol=target_currency.symbol,
            currency_amount=source_fragment_amount,
            bought_at_price=current_buy_price,
            operation_datetime=pytz.utc.localize(datetime.utcnow()),
        )
        storage.save_package(package)
        add_system_log(f'BUY', f'BUY {target_currency.symbol} {source_fragment_amount}')

    trading_source.finish_conversions()


"""
Specific commands
"""


def reset_trading():
    enable_trading_data = server_get('enable_trading', default_data={'activated': False}).data
    server_set('enable_trading', {
        'activated': False
    })

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    now = pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()

    trading_source.start_conversions()

    for currency in trading_cryptocurrencies:
        amount = trading_source.get_amount_owned(currency)
        if round(amount) == 0.0:
            continue
        prices = trading_source.get_last_month_prices(currency)
        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            continue
        packages = storage.get_cryptocurrency_packages(currency)
        amount = two_decimals_floor(amount)
        target = trading_source.get_stable_cryptocurrency()
        trading_source.convert(currency, amount, target)
        for package in packages:
            storage.delete_package(package)

    trading_source.finish_conversions()

    server_set('enable_trading', {
        'activated': enable_trading_data.get('activated')
    })


"""
Obsolete
"""


def _sample():
    now = pytz.utc.localize(datetime.utcnow())
    current = now - timedelta(hours=36)
    while current < now:
        _discriminate_by_sell_and_purchase_2(current)
        current += timedelta(minutes=5)


def _discriminate_by_sell_and_purchase_2(now=None):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)

    for_sell = []
    purchase_currency_data = []

    now = now or pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()

    for currency in trading_cryptocurrencies:
        print('=' * 80)
        print(f'[{now}] Checking currency {currency}')
        prices = trading_source.get_last_month_prices(currency)
        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            continue
        packages = storage.get_cryptocurrency_packages(currency)
        current_sell_price = prices[-1].sell_price

        """
        1.- Para vender, rentabilidad últimas 4h tendría que ser < -5 y tener paquetes que cumplan:
                + Que alguno ofrezca una rentabilidad de > 20%
                + Que alguno tenga 2 semanas o más con rentabilidad entre 5% y 20%
                + Que tengan más de n meses de antiguedad. Que sea configurable.
        """
        profit_4d = qs.profit_percentage(timedelta(days=4), now=now)
        if profit_4d < -5:
            for package in packages:
                package_profit = profit_difference_percentage(package.bought_at_price, current_sell_price)
                sell_it = False
                if package_profit > 20:
                    sell_it = True
                elif 5 <= package_profit <= 20 and now - timedelta(days=7) >= package.operation_datetime:
                    sell_it = True
                # TODO add auto_sell

                if sell_it:
                    for_sell.append(currency)

        """
        2.- Para comprar:
                + La que menos pasta tenga invertida?
                + La que más haya caido?
                + Ambas, rentabilidad / dinero en ella, filtra por < 0, ordena por ello
        """
        # evaluate purchase
        native_total = 0
        for package in packages:
            native_total += package.currency_amount * current_sell_price
        profitability = qs.profit_percentage(timedelta(days=7), now=now)
        if native_total == 0.0 or profitability / native_total < 0:
            score = profitability / native_total if native_total != 0.0 else -10
            purchase_currency_data.append({
                'score': score,
                'currency': currency
            })

    purchase_currency_data.sort(key=lambda item: item['score'])
    for_purchase = [item['currency'] for item in purchase_currency_data[0: 3]]

    _plot_prices(for_sell, f'For sell {now}', now)
    _plot_prices(for_purchase, f'For purchase {now}', now)

    return for_sell, for_purchase


def _discriminate_by_sell_and_purchase(now=None):
    # consume un máximo de 89 peticiones al API

    # get_trading_cryptocurrencies
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    for_sell = []
    for_purchase = []

    now = now or pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    for currency in trading_cryptocurrencies:
        prices = trading_source.get_last_month_prices(currency)
        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            continue

        last_24h_prices = qs.filter_by_last(timedelta(hours=24), now=now)
        last_1h_prices = qs.filter_by_last(timedelta(hours=1), now=now)

        current_sell_price = prices[-1].sell_price
        if current_sell_price is None:
            continue

        # Si el precio actual está por encima del precio mediano + stdev último mes,
        # y la rentabilidad 6h es < 0, vender!
        last_24h_profit = profit_difference_percentage(last_24h_prices[0].sell_price, last_24h_prices[-1].sell_price)
        last_1h_profit = profit_difference_percentage(last_1h_prices[0].sell_price, last_1h_prices[-1].sell_price)
        if last_24h_profit > 5 and last_1h_profit < 5:
            for_sell.append(currency)
            continue

        # Si el precio actual está por debajo del precio mediano - stdev último mes,
        # y la rentabilidad 6h es > 0, comprar!
        current_buy_price = prices[-1].buy_price
        if current_buy_price is None:
            continue

        buy_prices_month = [price.buy_price for price in prices]
        buy_prices_median = statistics.median(buy_prices_month)
        buy_prices_stdev = statistics.stdev(buy_prices_month)
        last_1h_profit = profit_difference_percentage(last_1h_prices[0].buy_price, last_1h_prices[-1].buy_price)
        if current_buy_price < buy_prices_median - (buy_prices_stdev / 2.0) and last_1h_profit > 5:
            for_purchase.append(currency)
            continue

    _plot_prices(for_sell, f'For sell {now}', now)
    _plot_prices(for_purchase, f'For purchase {now}', now)

    return for_sell, for_purchase


def _plot_prices(currencies, title, now):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    if len(currencies) > 0:
        fig, axs = plt.subplots(len(currencies))
        fig.suptitle(title)
        for n, currency in enumerate(currencies):
            prices = trading_source.get_last_month_prices(currency)
            prices = [price for price in prices if now - timedelta(days=30) <= price.instant <= now]
            if len(prices) == 0:
                continue

            x = [p.instant for p in prices]
            y = [p.sell_price for p in prices]
            try:
                axs[n].plot(x, y)
                axs[n].set_xlabel(currency.symbol)
                axs[n].xaxis.set_label_coords(0.5, 0.5)
                axs[n].xaxis.set_major_formatter(DateFormatter('%H:%M'))
            except TypeError:
                axs.plot(x, y)
                axs.set_xlabel(currency.symbol)
                axs.xaxis.set_label_coords(0.5, 0.5)
                axs.xaxis.set_major_formatter(DateFormatter('%H:%M'))
        plt.tight_layout()
        plt.show()


def _get_global_market_profit(time_delta=None):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    time_delta = time_delta or timedelta(hours=24)
    now = pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    profits = []
    for currency in trading_cryptocurrencies:
        prices = trading_source.get_last_month_prices(currency)
        prices = [price for price in prices if now - time_delta <= price.instant]
        if len(prices) == 0:
            continue
        profit = profit_difference_percentage(prices[0].buy_price, prices[-1].buy_price)
        profits.append(profit)
    if len(profits) == 0:
        return 0.0
    return statistics.mean(profits)


def _check_sell(candidate_currency: Cryptocurrency):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    now = pytz.utc.localize(datetime.utcnow())

    packages = storage.get_cryptocurrency_packages(candidate_currency)
    delete_packages = []
    profits = []
    if len(packages) == 0:
        amount = trading_source.get_amount_owned(candidate_currency)
    else:
        amount = 0.0
        current_sell_price = trading_source.get_current_sell_price(candidate_currency)
        for package in packages:
            profit_difference = profit_difference_percentage(package.bought_at_price, current_sell_price)
            if profit_difference > 20:
                profits.append(profit_difference)
                delete_packages.append(package)
                amount += package.currency_amount
            elif 5 <= profit_difference <= 20 and now - timedelta(days=7) >= package.operation_datetime:
                profits.append(profit_difference)
                delete_packages.append(package)
                amount += package.currency_amount

    if len(profits) == 0:
        profits = [0.0]

    if round(amount) > 0.0:
        amount = two_decimals_floor(amount)
        target = trading_source.get_stable_cryptocurrency()
        trading_source.convert(candidate_currency, amount, target)
        for package in delete_packages:
            storage.delete_package(package)

        add_system_log(f'SELL', f'SELL {candidate_currency.symbol} {amount} profit: {statistics.mean(profits)}%')


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
            operation_datetime=pytz.utc.localize(datetime.utcnow()),
        )
        storage.save_package(package)
        add_system_log(f'BUY', f'BUY {target_currency.symbol} {source_fragment_amount}')


@schedule(minute='*', unique_name='trade', priority=6)
def fetch_prices():
    now = pytz.utc.localize(datetime.utcnow())
    if now.minute % 5 != 0:
        return

    enable_fetch_prices_data = server_get('enable_fetch_prices', default_data={'activated': False}).data
    enable_fetch_prices = enable_fetch_prices_data.get('activated')
    if not enable_fetch_prices:
        return
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    from trading.application.django_models import DCryptocurrencyPrice

    for cryptocurrency in trading_source.get_trading_cryptocurrencies():
        try:
            sell_price = trading_source.get_current_sell_price(cryptocurrency)
            buy_price = trading_source.get_current_buy_price(cryptocurrency)
        except JSONDecodeError:
            continue
        if sell_price is None or buy_price is None:
            continue
        now = pytz.utc.localize(datetime.utcnow())

        DCryptocurrencyPrice.objects.create(
            symbol=cryptocurrency.symbol,
            instant=now,
            sell_price=sell_price,
            buy_price=buy_price,
        )
