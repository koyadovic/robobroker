from django.core.management.base import BaseCommand
from trading.domain.services import sell_packages


class Command(BaseCommand):
    help = 'Reset investments'

    def add_arguments(self, parser):
        parser.add_argument('package_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        package_ids = options.get('package_ids')
        sell_packages(package_ids)
