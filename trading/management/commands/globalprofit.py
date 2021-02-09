from django.core.management.base import BaseCommand
from trading.domain.services import show_global_profit_stats


class Command(BaseCommand):
    help = 'Global profit stats'

    def handle(self, *args, **options):
        show_global_profit_stats()
