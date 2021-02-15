import time
from datetime import datetime, timedelta
from typing import List

import numpy as np

import pytz
from celery.schedules import crontab
from celery.task import periodic_task
from matplotlib.dates import DateFormatter
from sentry_sdk import capture_exception

from shared.domain.configurations import server_get, server_set
from shared.domain.dependencies import dependency_dispatcher
from shared.domain.system_logs import add_system_log
from shared.domain.tools import filelocks
from trading.domain.entities import Package
from trading.domain.interfaces import ILocalStorage, ICryptoCurrencySource
import matplotlib.pyplot as plt
import statistics
from trading.domain.tools.prices import PricesQueryset
from trading.domain.tools.stats import profit_difference_percentage, cubic_splines_function, derivative
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def log(text):
    logger.info(text)
    print(text)


COMMON_CURRENCY = 'EUR'


_FILE_LOCK = '/tmp/.robobroker_trading'


@periodic_task(run_every=crontab(minute='*/5'), name="sell_operation_every_5_minutes", ignore_result=False)
def trade():
    with filelocks.acquire_single_access(_FILE_LOCK, exit_if_locked=True, raise_exception_if_locked=False):
        now = pytz.utc.localize(datetime.utcnow())
        trading_purchase_settings_data = server_get('trading_purchase_settings', default_data={
            'max_purchases_each_time': 10,
            'max_amount_per_purchase': 10,
            'execute_each_hours': 2
        }).data

        execute_each_hours = int(trading_purchase_settings_data.get('execute_each_hours', 2))
        do_purchase = now.hour % execute_each_hours == 0 and now.minute == 0

        enable_trading_data = server_get('enable_trading', default_data={'activated': False}).data
        enable_trading = enable_trading_data.get('activated')
        if not enable_trading:
            return

        log(f'Waiting 2 minutes to fetch prices ...')
        trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
        time.sleep(120)
        log(f'Fetching updated prices ...')
        all_prices = trading_source.get_all_currency_prices()
        currencies_sold = sell(all_prices=all_prices)
        if do_purchase:
            purchase(all_prices=all_prices, ignore_for_purchase=currencies_sold)


def sell(all_prices=None):
    now = pytz.utc.localize(datetime.utcnow())
    log(f'--- INIT SELL ---')

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    started_conversions = False

    currencies_sold = []

    try:
        for currency in trading_cryptocurrencies:
            packages = storage.get_cryptocurrency_packages(currency)
            if len(packages) == 0:
                continue

            if all_prices is None:
                prices = trading_source.get_last_month_prices(currency)
            else:
                prices = all_prices[currency.symbol]

            qs = PricesQueryset(prices)
            if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
                continue

            current_sell_price = prices[-1].sell_price

            """
            1.- Para vender, rentabilidad últimas 3h tendría que ser < -3 y tener paquetes que cumplan:
                + Que alguno ofrezca una rentabilidad de > 20%
                + Que alguno tenga 2 semanas o más con rentabilidad entre 5% y 20%
                + Que tengan más de n meses de antiguedad. Que sea configurable.
            """
            # price, ahead_derivative = get_last_inflexion_point_price(currency)

            profit_24h = qs.profit_percentage(timedelta(days=1))
            profit_1h = qs.profit_percentage(timedelta(hours=1))

            # if price is None:
            #     log(f'Currency {currency} has no inflexion point, ignoring it')
            #     continue
            if profit_1h < -1 or profit_24h < -1:  # ahead_derivative < 0
                log(f'Currency {currency} is currently going down. Vamos a buscar paquetes que se puedan vender')
                amount = 0.0
                remove_packages = []
                profits = []

                # weighted average for profits
                weighted_profits = 0.0
                total_amount_for_weighted_profit = 0.0
                for package in packages:
                    package_profit = profit_difference_percentage(package.bought_at_price, current_sell_price)
                    weighted_profits += package_profit * package.currency_amount * current_sell_price
                    total_amount_for_weighted_profit += package.currency_amount * current_sell_price

                weighted_profit = weighted_profits / total_amount_for_weighted_profit if total_amount_for_weighted_profit != 0.0 else 0.0
                if weighted_profit > 12:
                    log(f'Weighted profit for {currency} --> {round(weighted_profit, 2)}%. Vendiendo todos los paquetes')
                    for package in packages:
                        package_profit = profit_difference_percentage(package.bought_at_price, current_sell_price)
                        profits.append(package_profit)
                        remove_packages.append(package)
                        amount += package.currency_amount
                else:
                    # traditional profit code
                    for package in packages:
                        package_profit = profit_difference_percentage(package.bought_at_price, current_sell_price)

                        sell_it = False
                        if package_profit > 15:
                            log(f'Currency {currency} tiene paquete que nos da una rentabilidad de {package_profit}% !!')
                            sell_it = True
                        elif 3 <= package_profit <= 15 and now - timedelta(days=3) >= package.operation_datetime:
                            log(f'Currency {currency} tiene paquete que nos da una rentabilidad de {package_profit}% y ya es algo antiguo !!')
                            sell_it = True
                        # TODO add auto_sell

                        if sell_it:
                            profits.append(package_profit)
                            remove_packages.append(package)
                            amount += package.currency_amount

                if len(profits) == 0:
                    profits = [0.0]

                if round(amount * current_sell_price) > 1.0:
                    if not started_conversions:
                        trading_source.start_conversions()
                        started_conversions = True

                    target = trading_source.get_stable_cryptocurrency()
                    log(f'Currency {currency} convirtiendo {currency} {amount} en {target}')

                    try:
                        real_source_amount, _ = trading_source.convert(currency, amount, target)
                    except Exception as e:
                        capture_exception(e)
                        log(e)
                        continue

                    mean_bought_at_price = statistics.mean([package.bought_at_price for package in remove_packages])
                    remaining = amount - real_source_amount
                    operation_datetime = pytz.utc.localize(datetime.utcnow()) if len(remove_packages) == 0 else \
                        remove_packages[0].operation_datetime

                    package = Package(
                        currency_symbol=currency.symbol,
                        currency_amount=remaining,
                        bought_at_price=mean_bought_at_price,
                        operation_datetime=operation_datetime,
                    )
                    storage.save_package(package)
                    for package in remove_packages:
                        storage.delete_package(package)
                    currencies_sold.append(currency)
                    add_system_log(f'SELL', f'SELL {currency.symbol} {amount} profit: {round(statistics.mean(profits), 1)}%')
                else:
                    log(f'Currency {currency} La cantidad a vender {current_sell_price * amount} EUR no es suficiente. Ignorando')

            else:
                log(f'Currency {currency} is currently going up. Esperamos')
    finally:
        if started_conversions:
            trading_source.finish_conversions()
    log(f'--- FINISH SELL ---')
    return currencies_sold


def purchase(all_prices=None, ignore_for_purchase=None):
    log(f'--- INIT PURCHASE ---')

    ignore_for_purchase = ignore_for_purchase or []
    ignore_symbols = [c.symbol for c in ignore_for_purchase]

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)

    # get trading settings
    trading_purchase_settings_data = server_get('trading_purchase_settings', default_data={
        'max_purchases_each_time': 10,
        'max_amount_per_purchase': 10,
        'execute_each_hours': 2,
        'amount_reserved': 0,
    }).data
    amount_reserved = trading_purchase_settings_data.get('amount_reserved', 0)

    source_cryptocurrency = trading_source.get_stable_cryptocurrency()
    source_amount = trading_source.get_amount_owned(source_cryptocurrency)
    if round(source_amount) - amount_reserved <= 1:
        log(f'Amount of stable currency is {source_amount}. Reserved {amount_reserved}. Returning')
        return

    now = pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    purchase_currency_data = []

    for currency in trading_cryptocurrencies:
        if currency.symbol == source_cryptocurrency.symbol:
            log(f'Ignoring {currency} for purchase')
            continue

        if currency.symbol in ignore_symbols:
            log(f'Ignoring {currency} for purchase. Sold recently.')
            continue

        if all_prices is None:
            prices = trading_source.get_last_month_prices(currency)
        else:
            prices = all_prices[currency.symbol]

        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            log(f'Ignoring {currency} no prices')
            continue

        packages = storage.get_cryptocurrency_packages(currency)
        current_sell_price = prices[-1].sell_price

        # new
        price_profit = qs.profit_percentage(timedelta(hours=24), now=now)

        native_amount_owned = 0
        for package in packages:
            native_amount_owned += package.currency_amount * current_sell_price
        if native_amount_owned < 1:
            native_amount_owned = 1

        purchase_currency_data.append({
            'price_profit': price_profit,
            'native_amount_owned': native_amount_owned,
            'currency': currency
        })

    # sort by precedence
    purchase_currency_data.sort(key=lambda item: item['native_amount_owned'])

    max_purchases_each_time = trading_purchase_settings_data.get('max_purchases_each_time')
    max_amount_per_purchase = trading_purchase_settings_data.get('max_amount_per_purchase')

    # limit to elements specified
    purchase_currency_data = purchase_currency_data[0:max_purchases_each_time]

    parts = len(purchase_currency_data) if len(purchase_currency_data) != 0 else 1
    source_fragment_amount = (source_amount - amount_reserved) / parts
    if source_fragment_amount > max_amount_per_purchase:
        source_fragment_amount = max_amount_per_purchase
    if round(source_fragment_amount) == 0.0:
        return

    trading_source.start_conversions()

    try:
        for purchase_currency_data_item in purchase_currency_data:
            target_currency = purchase_currency_data_item['currency']

            prices = trading_source.get_last_month_prices(target_currency)
            current_buy_price = prices[-1].buy_price
            try:
                _, converted_target_amount = trading_source.convert(source_cryptocurrency,
                                                                    source_fragment_amount,
                                                                    target_currency)
            except Exception as e:
                capture_exception(e)
                log(str(e))
                continue

            package = Package(
                currency_symbol=target_currency.symbol,
                currency_amount=converted_target_amount,
                bought_at_price=current_buy_price,
                operation_datetime=pytz.utc.localize(datetime.utcnow()),
            )
            storage.save_package(package)
            add_system_log(f'BUY', f'BUY {target_currency.symbol} {converted_target_amount}')
    finally:
        trading_source.finish_conversions()

    log(f'--- FINISH PURCHASE ---')


def sell_packages(package_ids: List[int]):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    packages = []
    different_currencies = set()
    amount = 0.0
    for package_id in package_ids:
        package = storage.get_package_by_id(package_id)
        if package is not None:
            packages.append(package)
            different_currencies.add(package.currency_symbol)
            amount += package.currency_amount
    if len(different_currencies) > 1:
        print(f'Cannot mix packages from different currencies')
        return
    elif len(different_currencies) == 0:
        print(f'No valid packages selected. Doing nothing.')
        return

    currency = trading_source.get_trading_cryptocurrency(packages[0].currency_symbol)

    trading_source.start_conversions()
    target = trading_source.get_stable_cryptocurrency()
    log(f'Currency {currency} convirtiendo {currency} {amount} en {target}')

    try:
        real_source_amount, _ = trading_source.convert(currency, amount, target)
    except Exception as e:
        capture_exception(e)
        log(e)
        return
    finally:
        trading_source.finish_conversions()

    mean_bought_at_price = statistics.mean([package.bought_at_price for package in packages])
    remaining = amount - real_source_amount
    operation_datetime = pytz.utc.localize(datetime.utcnow()) if len(packages) == 0 else \
        packages[0].operation_datetime

    package = Package(
        currency_symbol=currency.symbol,
        currency_amount=remaining,
        bought_at_price=mean_bought_at_price,
        operation_datetime=operation_datetime,
    )
    storage.save_package(package)
    for package in packages:
        storage.delete_package(package)
    add_system_log(f'SELL', f'SELL {currency.symbol} {amount}')


def get_last_inflexion_point_price(currency):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    prices = trading_source.get_last_month_prices(currency)

    x = np.array([price.instant.timestamp() for price in prices])
    y = np.array([price.buy_price for price in prices])

    different_days = 0
    days = []
    for price in prices:
        if price.instant.date() not in days:
            days.append(price.instant.date())
            different_days += 1

    number_of_knots = round(different_days / 1.5)

    f, _ = cubic_splines_function(x=x, y=y, number_of_knots=number_of_knots)

    for idx in range(len(prices) - 1, -1, -1):
        price = prices[idx]
        timestamp = price.instant.timestamp()
        minutes_ahead = timestamp + 600
        minutes_backwards = timestamp - 600

        ahead = derivative(f, minutes_ahead)
        backwards = derivative(f, minutes_backwards)

        if ahead < 0 < backwards or ahead > 0 > backwards:
            return price, ahead

    return None, None


"""
Specific commands
"""


def reset_trading():
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    now = pytz.utc.localize(datetime.utcnow())
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()

    trading_source.start_conversions()
    target = trading_source.get_stable_cryptocurrency()

    for currency in trading_cryptocurrencies:
        if currency.symbol == target.symbol:
            continue
        native_amount = trading_source.get_native_amount_owned(currency)
        if round(native_amount) == 0.0:
            continue
        prices = trading_source.get_last_month_prices(currency)
        qs = PricesQueryset(prices)
        if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
            continue
        amount = trading_source.get_amount_owned(currency)
        packages = storage.get_cryptocurrency_packages(currency)
        trading_source.convert(currency, amount, target)
        for package in packages:
            storage.delete_package(package)

    trading_source.finish_conversions()


def reset_currency(symbol: str):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    now = pytz.utc.localize(datetime.utcnow())

    source = trading_source.get_trading_cryptocurrency(symbol)
    target = trading_source.get_stable_cryptocurrency()

    if source.symbol == target.symbol:
        return
    native_amount = trading_source.get_native_amount_owned(source)
    if round(native_amount) == 0.0:
        return
    amount = trading_source.get_amount_owned(source)
    prices = trading_source.get_last_month_prices(source)
    qs = PricesQueryset(prices)
    if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
        return

    packages = storage.get_cryptocurrency_packages(source)
    trading_source.start_conversions()
    trading_source.convert(source, amount, target)
    trading_source.finish_conversions()
    for package in packages:
        storage.delete_package(package)


"""
Profits
"""


def list_package_profits(symbol=None):
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()

    trading_cryptocurrencies.sort(key=lambda curr: curr.symbol)

    for currency in trading_cryptocurrencies:
        if symbol is not None and currency.symbol != symbol:
            continue
        packages = storage.get_cryptocurrency_packages(currency)
        if len(packages) == 0:
            continue
        current_price = trading_source.get_current_sell_price(currency)
        total_spent = 0.0
        total_current_value = 0.0
        total_currency_amount = 0.0
        total_profits = []
        print(f'\nFor {currency} (current price: {current_price}):')
        for package in packages:
            spent = package.currency_amount * package.bought_at_price
            current_value = package.currency_amount * current_price
            profit = profit_difference_percentage(spent, current_value)
            total_spent += spent
            total_current_value += current_value
            total_profits.append(profit)
            total_currency_amount += package.currency_amount
            print(f'    > [{package.id}] Spent EUR {round(spent, 2)} - Value EUR {round(current_value, 2)} - Bought at {package.bought_at_price} - Profit: {round(profit, 2)}%')
        if len(total_profits) == 0:
            total_profits = [0.0]
        print('    ' + ('-' * 75))
        print(f'    > Total spent EUR {round(total_spent, 2)} - Total value EUR {round(total_current_value, 2)} - Profit: {round(statistics.mean(total_profits), 2)} - Total {currency.symbol} {total_currency_amount}')


def show_global_profit_stats():
    fig, axs = plt.subplots(2)
    fig.suptitle('Global profit stats')
    global_profits_data = server_get('global_profits', default_data={'records': []}).data

    x = []
    y_total = []
    y_profit = []

    for record in global_profits_data.get('records', list()):
        # {'datetime': str(now), 'total': total, 'profit': 0.0}
        x.append(datetime.strptime(record.get('datetime'), '%Y-%m-%d'))
        y_total.append(record.get('total'))
        y_profit.append(record.get('profit'))

    axs[0].plot(x, y_total)
    axs[0].set_xlabel('Amount')
    axs[0].xaxis.set_label_coords(0.5, 0.5)
    axs[0].xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))

    axs[1].plot(x, y_profit)
    axs[1].set_xlabel('Profit')
    axs[1].xaxis.set_label_coords(0.5, 0.5)
    axs[1].xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))

    plt.tight_layout()
    plt.show()


@periodic_task(run_every=crontab(hour='0', minute='0'), name="compute_global_profit", ignore_result=False)
def compute_global_profit():
    global_profits_data = server_get('global_profits', default_data={'records': []}).data
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    now = pytz.utc.localize(datetime.utcnow())
    total = 0.0
    for currency in trading_source.get_trading_cryptocurrencies():
        total += trading_source.get_native_amount_owned(currency)

    current = {'datetime': now.strftime('%Y-%m-%d'), 'total': total, 'profit': 0.0}
    if len(global_profits_data['records']) == 0:
        last = None
    else:
        last = global_profits_data['records'][-1]

    if last is not None:
        current['profit'] = profit_difference_percentage(last['total'], current['total'])

    global_profits_data['records'].append(current)
    server_set('global_profits', global_profits_data)


"""
Obsolete
"""


# def _sample():
#     now = pytz.utc.localize(datetime.utcnow())
#     current = now - timedelta(hours=36)
#     while current < now:
#         _discriminate_by_sell_and_purchase_2(current)
#         current += timedelta(minutes=5)
#
#
# def _discriminate_by_sell_and_purchase_2(now=None):
#     trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
#     storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
#
#     for_sell = []
#     purchase_currency_data = []
#
#     now = now or pytz.utc.localize(datetime.utcnow())
#     trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
#
#     for currency in trading_cryptocurrencies:
#         print('=' * 80)
#         print(f'[{now}] Checking currency {currency}')
#         prices = trading_source.get_last_month_prices(currency)
#         qs = PricesQueryset(prices)
#         if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
#             continue
#         packages = storage.get_cryptocurrency_packages(currency)
#         current_sell_price = prices[-1].sell_price
#
#         """
#         1.- Para vender, rentabilidad últimas 4h tendría que ser < -5 y tener paquetes que cumplan:
#                 + Que alguno ofrezca una rentabilidad de > 20%
#                 + Que alguno tenga 2 semanas o más con rentabilidad entre 5% y 20%
#                 + Que tengan más de n meses de antiguedad. Que sea configurable.
#         """
#         profit_4d = qs.profit_percentage(timedelta(days=4), now=now)
#         if profit_4d < -5:
#             for package in packages:
#                 package_profit = profit_difference_percentage(package.bought_at_price, current_sell_price)
#                 sell_it = False
#                 if package_profit > 20:
#                     sell_it = True
#                 elif 5 <= package_profit <= 20 and now - timedelta(days=7) >= package.operation_datetime:
#                     sell_it = True
#                 # TODO add auto_sell
#
#                 if sell_it:
#                     for_sell.append(currency)
#
#         """
#         2.- Para comprar:
#                 + La que menos pasta tenga invertida?
#                 + La que más haya caido?
#                 + Ambas, rentabilidad / dinero en ella, filtra por < 0, ordena por ello
#         """
#         # evaluate purchase
#         native_total = 0
#         for package in packages:
#             native_total += package.currency_amount * current_sell_price
#         if native_total == 0:
#             native_total = 1
#         profitability = qs.profit_percentage(timedelta(days=7), now=now)
#         if profitability / native_total < 0:
#             score = profitability / native_total
#             if score < 0:
#                 purchase_currency_data.append({
#                     'score': score,
#                     'currency': currency
#                 })
#
#     purchase_currency_data.sort(key=lambda item: item['score'])
#     for_purchase = [item['currency'] for item in purchase_currency_data[0: 10]]
#
#     _plot_prices(for_sell, f'For sell {now}', now)
#     _plot_prices(for_purchase, f'For purchase {now}', now)
#
#     return for_sell, for_purchase
#
#
# def _discriminate_by_sell_and_purchase(now=None):
#     # consume un máximo de 89 peticiones al API
#
#     # get_trading_cryptocurrencies
#     trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
#
#     for_sell = []
#     for_purchase = []
#
#     now = now or pytz.utc.localize(datetime.utcnow())
#     trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
#     for currency in trading_cryptocurrencies:
#         prices = trading_source.get_last_month_prices(currency)
#         qs = PricesQueryset(prices)
#         if len(qs.filter_by_last(timedelta(days=30), now=now)) == 0:
#             continue
#
#         last_24h_prices = qs.filter_by_last(timedelta(hours=24), now=now)
#         last_1h_prices = qs.filter_by_last(timedelta(hours=1), now=now)
#
#         current_sell_price = prices[-1].sell_price
#         if current_sell_price is None:
#             continue
#
#         # Si el precio actual está por encima del precio mediano + stdev último mes,
#         # y la rentabilidad 6h es < 0, vender!
#         last_24h_profit = profit_difference_percentage(last_24h_prices[0].sell_price, last_24h_prices[-1].sell_price)
#         last_1h_profit = profit_difference_percentage(last_1h_prices[0].sell_price, last_1h_prices[-1].sell_price)
#         if last_24h_profit > 5 and last_1h_profit < 5:
#             for_sell.append(currency)
#             continue
#
#         # Si el precio actual está por debajo del precio mediano - stdev último mes,
#         # y la rentabilidad 6h es > 0, comprar!
#         current_buy_price = prices[-1].buy_price
#         if current_buy_price is None:
#             continue
#
#         buy_prices_month = [price.buy_price for price in prices]
#         buy_prices_median = statistics.median(buy_prices_month)
#         buy_prices_stdev = statistics.stdev(buy_prices_month)
#         last_1h_profit = profit_difference_percentage(last_1h_prices[0].buy_price, last_1h_prices[-1].buy_price)
#         if current_buy_price < buy_prices_median - (buy_prices_stdev / 2.0) and last_1h_profit > 5:
#             for_purchase.append(currency)
#             continue
#
#     _plot_prices(for_sell, f'For sell {now}', now)
#     _plot_prices(for_purchase, f'For purchase {now}', now)
#
#     return for_sell, for_purchase
#
#
# def _plot_prices(currencies, title, now):
#     trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
#     if len(currencies) > 0:
#         fig, axs = plt.subplots(len(currencies))
#         fig.suptitle(title)
#         for n, currency in enumerate(currencies):
#             prices = trading_source.get_last_month_prices(currency)
#             prices = [price for price in prices if now - timedelta(days=30) <= price.instant <= now]
#             if len(prices) == 0:
#                 continue
#
#             x = [p.instant for p in prices]
#             y = [p.sell_price for p in prices]
#             try:
#                 axs[n].plot(x, y)
#                 axs[n].set_xlabel(currency.symbol)
#                 axs[n].xaxis.set_label_coords(0.5, 0.5)
#                 axs[n].xaxis.set_major_formatter(DateFormatter('%H:%M'))
#             except TypeError:
#                 axs.plot(x, y)
#                 axs.set_xlabel(currency.symbol)
#                 axs.xaxis.set_label_coords(0.5, 0.5)
#                 axs.xaxis.set_major_formatter(DateFormatter('%H:%M'))
#         plt.tight_layout()
#         plt.show()
#
#
# def _get_global_market_profit(time_delta=None):
#     trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
#     time_delta = time_delta or timedelta(hours=24)
#     now = pytz.utc.localize(datetime.utcnow())
#     trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
#     profits = []
#     for currency in trading_cryptocurrencies:
#         prices = trading_source.get_last_month_prices(currency)
#         prices = [price for price in prices if now - time_delta <= price.instant]
#         if len(prices) == 0:
#             continue
#         profit = profit_difference_percentage(prices[0].buy_price, prices[-1].buy_price)
#         profits.append(profit)
#     if len(profits) == 0:
#         return 0.0
#     return statistics.mean(profits)
#
#
# def _check_sell(candidate_currency: Cryptocurrency):
#     storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
#     trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
#
#     now = pytz.utc.localize(datetime.utcnow())
#
#     packages = storage.get_cryptocurrency_packages(candidate_currency)
#     delete_packages = []
#     profits = []
#     if len(packages) == 0:
#         amount = trading_source.get_amount_owned(candidate_currency)
#     else:
#         amount = 0.0
#         current_sell_price = trading_source.get_current_sell_price(candidate_currency)
#         for package in packages:
#             profit_difference = profit_difference_percentage(package.bought_at_price, current_sell_price)
#             if profit_difference > 20:
#                 profits.append(profit_difference)
#                 delete_packages.append(package)
#                 amount += package.currency_amount
#             elif 5 <= profit_difference <= 20 and now - timedelta(days=7) >= package.operation_datetime:
#                 profits.append(profit_difference)
#                 delete_packages.append(package)
#                 amount += package.currency_amount
#
#     if len(profits) == 0:
#         profits = [0.0]
#
#     if round(amount) > 0.0:
#         amount = two_decimals_floor(amount)
#         target = trading_source.get_stable_cryptocurrency()
#         trading_source.convert(candidate_currency, amount, target)
#         for package in delete_packages:
#             storage.delete_package(package)
#
#         add_system_log(f'SELL', f'SELL {candidate_currency.symbol} {amount} profit: {statistics.mean(profits)}%')
#
#
# def _check_buy(candidate_currencies: List[Cryptocurrency]):
#     storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
#     trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
#
#     # stable currency
#     source_cryptocurrency = trading_source.get_stable_cryptocurrency()
#     source_amount = trading_source.get_amount_owned(source_cryptocurrency)
#     if round(source_amount) <= 1:
#         return
#
#     parts = len(candidate_currencies)
#     # queremos diversificación, no jugárnosla convirtiendo all a una única moneda
#     if parts < 3:
#         parts = 3
#     source_fragment_amount = math.floor((source_amount / parts) * 100.0) / 100.0
#
#     for target_currency in candidate_currencies:
#         real_source_fragment_amount = trading_source.convert(source_cryptocurrency, source_fragment_amount, target_currency)
#         target_currency_buy_price = trading_source.get_current_buy_price(target_currency)
#         package = Package(
#             currency_symbol=target_currency.symbol,
#             currency_amount=real_source_fragment_amount,
#             bought_at_price=target_currency_buy_price,
#             operation_datetime=pytz.utc.localize(datetime.utcnow()),
#         )
#         storage.save_package(package)
#         add_system_log(f'BUY', f'BUY {target_currency.symbol} {real_source_fragment_amount}')
