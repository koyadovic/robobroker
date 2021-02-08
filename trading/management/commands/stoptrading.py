from django.core.management.base import BaseCommand
from shared.domain.configurations import server_set


class Command(BaseCommand):
    help = 'Stop trading'

    def handle(self, *args, **options):
        server_set('enable_trading', {
            'activated': False
        })
