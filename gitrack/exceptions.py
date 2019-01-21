
class GitrackException(Exception):
    """
    General giTrack's exception
    """
    pass


class ConfigException(GitrackException):
    """
    Exception related to Config functionality.
    """
    pass


class InitializedRepoException(GitrackException):
    """
    Raised when user tries to initialized repo that has been already initialized before.
    """
    pass


class UninitializedRepoException(GitrackException):
    """
    Raised when giTrack invoke in Git repository that has not been initialized.
    """
    pass


class UnknownShell(GitrackException):
    pass


class PromptException(GitrackException):
    pass


class ProviderException(GitrackException):
    def __init__(self, provider_name, message, *args, **kwargs):
        self.message = message
        self.provider_name = provider_name

        super().__init__(*args, **kwargs)

    def __str__(self):
        return 'Provider \'{}\': {}'.format(self.provider_name, self.message)


class RunningEntry(ProviderException):
    pass
