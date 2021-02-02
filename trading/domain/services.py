import math
from typing import List

from shared.domain.dependencies import dependency_dispatcher
from trading.domain.entities import Cryptocurrency, Package
from trading.domain.interfaces import ILocalStorage, ICryptoCurrencySource


COMMON_CURRENCY = 'EUR'


def trade():
    """
    El proceso es:
    1.- El Discriminator cataloga candidates_for_purchase y candidates_for_sell
    2.- Primero se ejecuta una a una check_sell(single_candidate_for_sell)
    3.- Se finaliza llamando check_purchase(candidates_for_purchase)
    """
    for_sell, for_purchase = _discriminate_by_sell_and_purchase()
    pass


def _discriminate_by_sell_and_purchase():
    # get_trading_cryptocurrencies
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    for_sell = []
    for_purchase = []

    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    for currency in trading_cryptocurrencies:
        data = trading_source.get_last_month_prices(currency, COMMON_CURRENCY)

    return for_sell, for_purchase


def _check_sell(candidate_currency: Cryptocurrency):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    packages = storage.get_cryptocurrency_packages(candidate_currency)
    amount = 0.0

    for package in packages:
        if package.sell_profit_percentage > 5.0:
            amount += package.amount

    if amount > 0.0:
        target = trading_source.get_stable_cryptocurrency()
        trading_source.convert(candidate_currency, amount, target)


def _check_buy(candidate_currencies: List[Cryptocurrency]):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    source_cryptocurrency = trading_source.get_stable_cryptocurrency()
    source_amount = trading_source.get_amount_owned(source_cryptocurrency)
    parts = len(candidate_currencies)
    for target_currency in candidate_currencies:
        source_fragment_amount = math.floor(source_amount / parts)
        trading_source.convert(source_cryptocurrency, source_fragment_amount, target_currency)
        storage.save_package(Package())
        # TODO crear el package
