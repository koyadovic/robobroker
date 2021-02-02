from shared.domain.tools.properties import property_cached


class Cryptocurrency:
    buy_price: float = None
    sell_price: float = None
    symbol: str = None

    # TODO constructors

    @property_cached
    def total_amount(self):
        # (the sum of all packages) cached_property
        return 0.0


class Package:
    id: int = None
    cryptocurrency_symbol: str = None
    amount: float = None
    bought_at_price: float = None

    # TODO constructors

    def sell_profit_percentage(self, sell_price):
        return ((sell_price - self.bought_at_price) / self.bought_at_price) * 100
