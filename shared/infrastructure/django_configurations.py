from typing import Optional

from shared.domain.configurations import AbstractConfigurationStorage, UserConfiguration, ServerConfiguration


class DjangoConfigurationStorage(AbstractConfigurationStorage):
    def server_get(self, key: str) -> Optional[ServerConfiguration]:
        from shared.application.models import DServerConfiguration
        config = DServerConfiguration.objects.filter(key=key).first()
        if config is None:
            return None
        return config.core_entity

    def user_get(self, user_pk, key: str) -> Optional[UserConfiguration]:
        from shared.application.models import DUserConfiguration
        config = DUserConfiguration.objects.filter(user_pk=user_pk, key=key).first()
        if config is None:
            return None
        return config.core_entity

    def server_set(self, key: str, data: dict):
        from shared.application.models import DServerConfiguration
        config = DServerConfiguration.objects.filter(key=key).first()
        if config is None:
            DServerConfiguration.objects.create(key=key, data=data)
        else:
            config.data = data
            config.save()

    def user_set(self, user_pk, key: str, data: dict):
        from shared.application.models import DUserConfiguration
        config = DUserConfiguration.objects.filter(user_pk=user_pk, key=key).first()
        if config is None:
            DUserConfiguration.objects.create(user_pk=user_pk, key=key, data=data)
        else:
            config.data = data
            config.save()
