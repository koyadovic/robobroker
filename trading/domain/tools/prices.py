from datetime import datetime

import pytz

from trading.domain.tools.stats import profit_difference_percentage
import numpy as np
from sklearn.linear_model import LinearRegression


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
            return 0.0

        first_price = (prices[0].sell_price + prices[0].buy_price) / 2.0
        last_price = (prices[-1].sell_price + prices[-1].buy_price) / 2.0

        return profit_difference_percentage(first_price, last_price)

    def regression_profit_percentage(self, td, now=None):
        prices = self.filter_by_last(td, now=now)
        if len(prices) == 0:
            return 0.0

        y = [(price.sell_price + price.buy_price) / 2.0 for price in prices]
        x = [price.instant.timestamp() for price in prices]

        first_x = x[0]
        last_x = x[-1]

        x = np.array(x).reshape((-1, 1))
        y = np.array(y)

        model = LinearRegression()
        model.fit(x, y)

        first_y = model.predict([[first_x]])[0]
        last_y = model.predict([[last_x]])[0]

        return profit_difference_percentage(first_y, last_y)
