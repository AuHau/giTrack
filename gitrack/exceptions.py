
class GitrackException(Exception):
    pass


class ConfigException(GitrackException):
    pass


class InitializedRepoException(GitrackException):
    """
    Raised when user tries to initialized repo that has been already initialized before.
    """
    pass


class UninitializedRepoException(GitrackException):
    pass


class UnkownShell(GitrackException):
    pass


class ProviderException(GitrackException):
    def __init__(self, provider_name, message, *args, **kwargs):
        self.message = message
        self.provider_name = provider_name

        super().__init__(*args, **kwargs)

    def __str__(self):
        return 'Provider \'{}\': {}'.format(self.provider_name, self.message)
