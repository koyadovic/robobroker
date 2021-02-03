from typing import List

from trading.application.django_models import DPackage
from trading.domain.entities import Cryptocurrency, Package
from trading.domain.interfaces import ILocalStorage


class DjangoLocalStorage(ILocalStorage):
    def save_package(self, package: Package):
        if package.id is None:
            dinstance = DPackage.objects.create(
                currency_symbol=package.currency_symbol,
                currency_amount=package.currency_amount,
                bought_at_price=package.bought_at_price,
                operation_datetime=package.operation_datetime,
            )
            package.id = dinstance.pk
        else:
            dinstance = DPackage.objects.get(pk=package.id)
            dinstance.currency_symbol = package.currency_symbol
            dinstance.currency_amount = package.currency_amount
            dinstance.bought_at_price = package.bought_at_price
            dinstance.operation_datetime = package.operation_datetime
            dinstance.save()

    def delete_package(self, package: Package):
        if package.id is None:
            return
        p = DPackage.objects.filter(pk=package.id).first()
        if p is not None:
            p.delete()

    def get_cryptocurrency_packages(self, cryptocurrency: Cryptocurrency) -> List[Package]:
        return [p.core_entity for p in DPackage.objects.filter(currency_symbol=cryptocurrency.symbol)]
