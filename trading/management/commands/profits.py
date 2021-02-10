from django.core.management.base import BaseCommand
from trading.domain.services import list_package_profits


class Command(BaseCommand):
    help = 'List all profits'

    def add_arguments(self, parser):
        parser.add_argument('symbol', nargs='?', type=str)

    def handle(self, *args, **options):
        symbol = options.get('symbol', None)
        list_package_profits(symbol=symbol)
