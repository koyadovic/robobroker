from django.core.management.base import BaseCommand
from trading.domain.services import reset_currency


class Command(BaseCommand):
    help = 'Reset single currency'

    def add_arguments(self, parser):
        parser.add_argument('symbol', type=str)

    def handle(self, *args, **options):
        symbol = options['symbol'].upper()
        reset_currency(symbol)
