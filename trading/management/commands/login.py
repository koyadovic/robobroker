from django.core.management.base import BaseCommand

from trading.domain.tools.browser import get_current_browser_driver


class Command(BaseCommand):
    help = 'Login in coinbase'

    def handle(self, *args, **options):
        driver = get_current_browser_driver(headless=False, detach=True)
        driver.get('https://www.coinbase.com/')
