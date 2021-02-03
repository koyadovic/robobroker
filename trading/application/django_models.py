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
