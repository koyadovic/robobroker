from datetime import datetime

import pytz

from trading.domain.tools.stats import profit_difference_percentage


class PricesQueryset:
    def __init__(self, prices):
        self.prices = prices

    def filter_by_last(self, td, now=None):
        now = now or pytz.utc.localize(datetime.utcnow())
        filtered_prices = [price for price in self.prices if now - td <= price.instant <= now]
        return filtered_prices

    def profit_percentage(self, td, now=None):
        prices = self.filter_by_last(td, now=now)
        if len(prices) == 0:
            return 0
        return profit_difference_percentage(prices[0].sell_price, prices[-1].sell_price)
