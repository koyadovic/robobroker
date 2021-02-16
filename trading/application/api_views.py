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

    days = int(request.GET.get('days', 30))
    prices = DCryptocurrencyPrice.objects.filter(symbol=currency, instant__gte=timezone.now() - timedelta(days=days)).order_by('instant').all()
    serialized_prices = [{
        'i': p.instant.timestamp(),
        's': p.sell_price,
        'b': p.buy_price,
    } for p in prices]
    return Response(serialized_prices)


@api_view(http_method_names=['GET'])
def all_last_month_prices_view(request):
    if not request.user.is_authenticated:
        return Response(status=401)

    trading_source: ICryptoCurrencySource = dependency_dispatcher.request_implementation(ICryptoCurrencySource)
    all_prices = {}
    days = int(request.GET.get('days', 30))
    for currency in trading_source.get_trading_cryptocurrencies():
        prices = DCryptocurrencyPrice.objects.filter(symbol=currency.symbol, instant__gte=timezone.now() - timedelta(days=days)).order_by('instant').all()
        all_prices[currency.symbol] = [{
            'i': p.instant.timestamp(),
            's': p.sell_price,
            'b': p.buy_price,
        } for p in prices]
    return Response(all_prices)
