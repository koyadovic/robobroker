from django.urls import path

from trading.application import api_views

urlpatterns = [
    path('api/all-month-prices/', api_views.all_last_month_prices_view),
    path('api/month-prices/<str:currency>/', api_views.last_month_prices_view),
]
