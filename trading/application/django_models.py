from django.db import models
from trading.domain.entities import Package


class DPackage(models.Model):
    currency_symbol = models.CharField(max_length=10)
    currency_amount = models.FloatField(default=0.0, blank=True, null=True)
    bought_at_price = models.FloatField(default=0.0, blank=True, null=True)
    operation_datetime = models.DateTimeField(blank=True, null=True)

    @property
    def core_entity(self):
        return Package(
            id=self.pk,
            currency_symbol=self.currency_symbol,
            currency_amount=self.currency_amount,
            bought_at_price=self.bought_at_price,
            operation_datetime=self.operation_datetime,
        )

    def __str__(self):
        return self.core_entity.__str__()

    def __repr__(self):
        return self.__repr__()

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'


class DCryptocurrencyPrice(models.Model):
    symbol = models.CharField(max_length=10)
    instant = models.DateTimeField(blank=True, null=True)
    sell_price = models.FloatField(blank=True, null=True)
    buy_price = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'{self.symbol} (sell_price: {self.sell_price}, buy_price: {self.buy_price})'

    def __repr__(self):
        return self.__repr__()

    class Meta:
        verbose_name = 'CryptocurrencyPrice'
        verbose_name_plural = 'CryptocurrencyPrices'
        ordering = ('-instant',)
