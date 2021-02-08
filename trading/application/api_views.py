from rest_framework.decorators import api_view
from rest_framework.response import Response

from shared.domain.dependencies import dependency_dispatcher
from trading.domain.interfaces import ICryptoCurrencySource


@api_view(http_method_names=['GET'])
def last_month_prices_view(request, currency=None):
    if not request.user.is_authenticated:
        return Response(status=401)

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    curr = trading_source.get_trading_cryptocurrency(currency)
    prices = trading_source.get_last_month_prices(curr)
    serialized_prices = [{
        'symbol': p.symbol,
        'instant': p.instant.timestamp(),
        'sell_price': p.sell_price,
        'buy_price': p.buy_price,
    } for p in prices]
    return Response(serialized_prices)
