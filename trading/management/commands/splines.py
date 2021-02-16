from django.core.management.base import BaseCommand
from matplotlib.dates import DateFormatter

from shared.domain.dependencies import dependency_dispatcher
from trading.domain.interfaces import ICryptoCurrencySource
from trading.domain.services import get_last_inflexion_point_price
import matplotlib.pyplot as plt

from trading.domain.tools.stats import profit_difference_percentage


class Command(BaseCommand):
    help = 'Splines test'

    def add_arguments(self, parser):
        parser.add_argument('symbol', nargs='?', type=str)

    def handle(self, *args, **options):
        trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
        symbol = options.get('symbol', None)

        for currency in trading_source.get_trading_cryptocurrencies():
            if symbol is not None and currency.symbol != symbol:
                continue

            price, ahead_derivative = get_last_inflexion_point_price(currency)
            if price is None:
                continue
            prices = trading_source.get_month_prices(currency)

            current_sell_price = prices[-1].sell_price
            profit_from_last_inflexion_point = profit_difference_percentage(price.sell_price, current_sell_price)

            status = 'estable'
            if ahead_derivative > 0.0:
                status = 'subiendo'
            elif ahead_derivative < 0.0:
                status = 'bajando'

            fig, axs = plt.subplots(1)
            fig.suptitle(f'{currency} {round(profit_from_last_inflexion_point, 1)}% - {status}')
            if len(prices) == 0:
                continue

            x = [p.instant for p in prices]
            y = [p.sell_price for p in prices]
            axs.plot(x, y)
            axs.axvline(price.instant)
            axs.set_xlabel(currency.symbol)
            axs.xaxis.set_label_coords(0.5, 0.5)
            axs.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            plt.tight_layout()
            plt.show()
