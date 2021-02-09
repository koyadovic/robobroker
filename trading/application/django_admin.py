from django.contrib import admin

from trading.application.django_models import DPackage


class DPackageAdmin(admin.ModelAdmin):
    list_display = ['operation_datetime', 'currency_symbol', 'currency_amount', 'bought_at_price']
    list_filter = ['operation_datetime', 'currency_symbol']


admin.site.register(DPackage, DPackageAdmin)
