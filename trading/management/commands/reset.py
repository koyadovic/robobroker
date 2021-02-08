from django.core.management.base import BaseCommand
from trading.domain.services import reset_trading


class Command(BaseCommand):
    help = 'Reset investments'

    def handle(self, *args, **options):
        reset_trading()
