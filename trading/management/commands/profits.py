from django.core.management.base import BaseCommand
from trading.domain.services import list_package_profits


class Command(BaseCommand):
    help = 'List all profits'

    def handle(self, *args, **options):
        list_package_profits()
