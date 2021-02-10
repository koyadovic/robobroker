from django.core.management.base import BaseCommand
from trading.domain.services import purchase


class Command(BaseCommand):
    help = 'Reset investments'

    def handle(self, *args, **options):
        purchase()
