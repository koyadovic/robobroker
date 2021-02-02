class AbstractEnvironment:
    def is_debug(self):
        raise NotImplementedError

    def get_secret_key(self) -> str:
        raise NotImplementedError

    def is_in_test(self):
        raise NotImplementedError

    def get_default_absolute_logo_path(self):
        raise NotImplementedError
