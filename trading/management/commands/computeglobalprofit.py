from django.core.management.base import BaseCommand
from trading.domain.services import compute_global_profit


class Command(BaseCommand):
    help = 'Global profit stats'

    def handle(self, *args, **options):
        compute_global_profit()
