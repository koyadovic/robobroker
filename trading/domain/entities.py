from shared.domain.tools.properties import property_cached


class Cryptocurrency:
    buy_price: float = None
    sell_price: float = None
    symbol: str = None

    @property_cached
    def total_amount(self):
        # (the sum of all packages) cached_property
        return 0.0


class Package:
    cryptocurrency: Cryptocurrency = None
    amount: float = None
    bought_at_price: float = None

    @property
    def sell_profit_percentage(self):
        return ((self.cryptocurrency.sell_price - self.bought_at_price) / self.bought_at_price) * 100
