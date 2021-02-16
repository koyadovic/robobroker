from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from shared.domain.dependencies import dependency_dispatcher
from trading.application.django_models import DCryptocurrencyPrice
from trading.domain.interfaces import ICryptoCurrencySource


@api_view(http_method_names=['GET'])
def last_month_prices_view(request, currency=None):
    if not request.user.is_authenticated:
        return Response(status=401)
    prices = DCryptocurrencyPrice.objects.filter(symbol=currency, instant__gte=timezone.now() - timedelta(days=30)).all()
    serialized_prices = [{
        'symbol': p.symbol,
        'instant': p.instant.timestamp(),
        'sell_price': p.sell_price,
        'buy_price': p.buy_price,
    } for p in prices]
    return Response(serialized_prices)


@api_view(http_method_names=['GET'])
def all_last_month_prices_view(request):
    if not request.user.is_authenticated:
        return Response(status=401)

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    all_prices = {}
    for currency in trading_source.get_trading_cryptocurrencies():
        prices = DCryptocurrencyPrice.objects.filter(symbol=currency.symbol, instant__gte=timezone.now() - timedelta(days=30)).all()
        all_prices[currency.symbol] = [{
            'symbol': p.symbol,
            'instant': p.instant.timestamp(),
            'sell_price': p.sell_price,
            'buy_price': p.buy_price,
        } for p in prices]
    return Response(all_prices)
