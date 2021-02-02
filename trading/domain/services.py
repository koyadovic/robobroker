import math
from typing import List

from shared.domain.dependencies import dependency_dispatcher
from trading.domain.entities import Cryptocurrency, Package
from trading.domain.interfaces import ILocalStorage, ICryptoCurrencySource
from trading.domain.tools import profit_difference_percentage

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

    # TODO Lo que decide si comprar o vender debería poder cambiarse
    #  pensar en esto

    trading_cryptocurrencies = trading_source.get_trading_cryptocurrencies()
    for currency in trading_cryptocurrencies:
        # TODO analyze tendencies
        """
        Crecimiento 7 días      Crecimiento 1 día       qué hacer
        +                       +                       Si no tienes nada, comprar.
        +                       -                       Mirar si vender
        -                       +                       Mirar si comprar
        -                       -                       nada.
        """

        """
        si mean(to_profit(last_week)) > 0 y mean(to_profit(last_6_hours)) < 0, candidata a vender!
        si mean(to_profit(last_week)) < 0 y mean(to_profit(last_6_hours)) > 0, candidata a comprar!
        si mean(to_profit(last_week)) > 0 y mean(to_profit(last_6_hours)) > 0, y no tienes nada, candidata a comprar!
        """
        data = trading_source.get_last_month_prices(currency, COMMON_CURRENCY)

    # TODO si tenemos currencies por un determinado tiempo que no vendemos y que no sacamos rentabilidad
    #  tocaría vender sí o sí.

    return for_sell, for_purchase


def _check_sell(candidate_currency: Cryptocurrency):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    packages = storage.get_cryptocurrency_packages(candidate_currency)
    amount = 0.0

    for package in packages:
        profit_difference = profit_difference_percentage(package.bought_at_price, candidate_currency.sell_price)
        if profit_difference > 10.0:
            amount += package.currency_amount

    if amount > 0.0:
        amount = math.floor(amount * 100.0) / 100.0
        target = trading_source.get_stable_cryptocurrency()
        trading_source.convert(candidate_currency, amount, target)


def _check_buy(candidate_currencies: List[Cryptocurrency]):
    storage: ILocalStorage = dependency_dispatcher.request_implementation(ILocalStorage)
    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)

    source_cryptocurrency = trading_source.get_stable_cryptocurrency()
    source_amount = trading_source.get_amount_owned(source_cryptocurrency)
    parts = len(candidate_currencies)
    for target_currency in candidate_currencies:
        source_fragment_amount = math.floor((source_amount / parts) * 100.0) / 100.0
        trading_source.convert(source_cryptocurrency, source_fragment_amount, target_currency)
        storage.save_package(Package())
        # TODO crear el package
