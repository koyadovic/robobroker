from datetime import datetime


class Cryptocurrency:
    buy_price: float = None
    sell_price: float = None
    symbol: str = None

    def __init__(self, buy_price=None, sell_price=None, symbol=None):
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.symbol = symbol


class Package:
    id: int = None
    currency_symbol: str = None
    currency_amount: float = None
    bought_at_price: float = None
    operation_datetime: datetime = None

    def __init__(self, id=None, currency_symbol=None, currency_amount=None, bought_at_price=None,
                 operation_datetime=None):
        self.id = id
        self.currency_symbol = currency_symbol
        self.currency_amount = currency_amount
        self.bought_at_price = bought_at_price
        self.operation_datetime = operation_datetime
