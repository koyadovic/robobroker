from datetime import datetime


class Cryptocurrency:
    symbol: str = None
    metadata: dict = {}

    def __init__(self, symbol=None, metadata=None):
        self.symbol = symbol
        self.metadata = metadata


class CryptocurrencyPrice:
    symbol: str = None
    instant: datetime = None
    sell_price: float = None
    buy_price: float = None

    def __init__(self, symbol=None, instant=None, sell_price=None, buy_price=None):
        self.symbol = symbol
        self.instant = instant
        self.sell_price = sell_price
        self.buy_price = buy_price


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
