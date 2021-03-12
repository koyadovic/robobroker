from django.core.management.base import BaseCommand
from trading.domain.services import show_global_profit_stats, get_current_global_profit


class Command(BaseCommand):
    help = 'Global profit stats'

    def handle(self, *args, **options):
        current = get_current_global_profit()
        print(f'Current amount: {current["total"]}, Today profit: {current["profit"]}')
        show_global_profit_stats()
