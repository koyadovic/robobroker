from django.contrib import admin

from trading.application.django_models import DPackage, DCryptocurrencyPrice


admin.site.register(DPackage)
admin.site.register(DCryptocurrencyPrice)
