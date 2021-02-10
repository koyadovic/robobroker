from django.core.management.base import BaseCommand
from matplotlib.dates import DateFormatter

from shared.domain.dependencies import dependency_dispatcher
from trading.domain.interfaces import ICryptoCurrencySource
from trading.domain.services import get_last_inflexion_point_price
import matplotlib.pyplot as plt


class Command(BaseCommand):
    help = 'Splines test'

    def handle(self, *args, **options):
        trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
        for currency in trading_source.get_trading_cryptocurrencies():
            price = get_last_inflexion_point_price(currency)
            if price is None:
                continue
            prices = trading_source.get_last_month_prices(currency)

            fig, axs = plt.subplots(1)
            fig.suptitle(f'{currency}')
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
