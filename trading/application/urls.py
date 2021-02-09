from django.urls import path

from trading.application import api_views
# from trading.domain import services


urlpatterns = [
    path('api/month-prices/<str:currency>/', api_views.last_month_prices_view),
]
