from typing import Optional

from shared.domain.dependencies import dependency_dispatcher
from shared.domain.event_dispatcher import event_dispatcher


class ServerConfiguration:
    key: str
    data: dict

    def __init__(self, key, data):
        self.key = key
        self.data = data

    def request_pre_save_validations(self):
        event_dispatcher.emit('pre-save-validations-server-configuration', configuration=self, capture_exceptions=False)


class UserConfiguration:
    user_pk: int
    key: str
    data: dict

    def __init__(self, user_pk, key, data):
        self.user_pk = user_pk
        self.key = key
        self.data = data

    def request_pre_save_validations(self):
        event_dispatcher.emit('pre-save-validations-user-configuration', configuration=self, capture_exceptions=False)


class AbstractConfigurationStorage:
    def server_get(self, key: str) -> Optional[ServerConfiguration]:
        raise NotImplementedError

    def server_set(self, key: str, data: dict):
        raise NotImplementedError

    def user_set(self, user_pk, key: str, data: dict):
        raise NotImplementedError

    def user_get(self, user_pk, key: str) -> Optional[UserConfiguration]:
        raise NotImplementedError


def server_get(key: str, default_data=None) -> ServerConfiguration:
    storage: AbstractConfigurationStorage = dependency_dispatcher.request_implementation(AbstractConfigurationStorage)
    value = storage.server_get(key)
    if value is None and default_data is not None:
        storage.server_set(key, default_data)
        return storage.server_get(key)
    return value


def server_set(key: str, data: dict):
    if type(key) != str:
        raise ValueError(f'Invalid key provided. Must be str')
    if type(data) != dict:
        raise ValueError(f'Data must be a dict object')
    storage: AbstractConfigurationStorage = dependency_dispatcher.request_implementation(AbstractConfigurationStorage)
    storage.server_set(key, data)


def user_get(user_pk, key: str, default_data=None) -> UserConfiguration:
    storage: AbstractConfigurationStorage = dependency_dispatcher.request_implementation(AbstractConfigurationStorage)
    value = storage.user_get(user_pk, key)
    if value is None and default_data is not None:
        storage.user_set(user_pk, key, default_data)
        return storage.user_get(user_pk, key)
    return value


def user_set(user_pk, key: str, data: dict):
    if type(key) != str:
        raise ValueError(f'Invalid key provided. Must be str')
    if not bool(user_pk) or type(user_pk) != int:
        raise ValueError(f'Invalid user pk provided')
    if type(data) != dict:
        raise ValueError(f'Data must be a dict object')
    storage: AbstractConfigurationStorage = dependency_dispatcher.request_implementation(AbstractConfigurationStorage)
    storage.user_set(user_pk, key, data)
