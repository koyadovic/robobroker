from django.conf import settings
from shared.domain.interfaces.environment import AbstractEnvironment


class DjangoEnvironment(AbstractEnvironment):

    def is_debug(self):
        return settings.DEBUG

    def get_secret_key(self) -> str:
        return settings.SECRET_KEY

    def is_in_test(self):
        return settings.TESTING
