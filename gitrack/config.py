import atexit
import configparser
import pathlib
import pickle
import typing
import abc
from collections import namedtuple
from enum import Enum

import git
import appdirs

from . import exceptions, APP_NAME, LOCAL_CONFIG_NAME, PROVIDERS

IniEntry = namedtuple('IniEntry', ['section', 'type'])


class ConfigSource(abc.ABC):
    @abc.abstractmethod
    def persist(self):
        pass

    @abc.abstractmethod
    def get_providers_config(self, provider_name):  # type: (str) -> typing.Dict
        pass

    @abc.abstractmethod
    def set_providers_config(self, provider_name, items):  # type: (str, typing.Dict) -> None
        pass

    @abc.abstractmethod
    def __getattr__(self, item):
        pass

    @abc.abstractmethod
    def __setattr__(self, key, value):
        super().__setattr__(key, value)


class IniConfigSource(ConfigSource):
    def __init__(self, path, mapping):  # type: (pathlib.Path, typing.Dict[str, IniEntry]) -> None
        self._path = path
        self._mapping = mapping
        self._store = configparser.ConfigParser(interpolation=None)

        if path.exists():
            self._store.read((str(path),))

    def __getattr__(self, item):  # type: (str) -> typing.Any
        try:
            if item in self._mapping:
                return self._resolve_type(self._mapping[item], item)
        except configparser.Error:
            pass

        raise AttributeError('\'{}\' attribute not found at: {}'.format(item, self._path))

    def __setattr__(self, key, value):
        # Private fields are stored directly on instance
        if key[0] == '_':
            super().__setattr__(key, value)
            return

        if key not in self._mapping:
            raise exceptions.ConfigException('You are trying to set \'{}\' attribute '
                                             'which does not have defined mapping!'.format(key))

        section = self._mapping[key].section

        if not self._store.has_section(section):
            self._store.add_section(section)

        if value is None:
            self._store.remove_option(section, key)
        else:
            self._store.set(section, key, str(value))

    def _resolve_type(self, entry, item):  # type: (IniEntry, str) -> typing.Any
        """
        Method returns value in config file defined by entry.section and item (eq. option).
        The value is type-casted into proper type defined in the entry.type.
        """
        if entry is None:
            return None

        if entry.type == bool:
            return self._store.getboolean(entry.section, item)
        elif entry.type == int:
            return self._store.getint(entry.section, item)
        elif entry.type == float:
            return self._store.getfloat(entry.section, item)
        else:
            return self._store.get(entry.section, item)

    def get_providers_config(self, provider_name):  # type: (str) -> typing.Dict
        try:
            return dict(self._store.items(provider_name))
        except configparser.NoSectionError:
            return {}

    def set_providers_config(self, provider_name, items):  # type: (str, typing.Dict) -> None
        self._store.read_dict({provider_name: items})

    def persist(self):
        with self._path.open('w') as config_file:
            self._store.write(config_file)


class StoreConfigSource(ConfigSource):

    def get_providers_config(self, provider_name):
        try:
            return getattr(self, provider_name)
        except AttributeError:
            return {}

    def set_providers_config(self, provider_name, items):
        setattr(self, provider_name, items)

    def __init__(self, store):  # type: (Store) -> None
        self._store = store

    def __setattr__(self, key, value):
        # Private fields are stored directly on instance
        if key[0] == '_':
            super().__setattr__(key, value)
            return

        self._store.data[key] = value

    def __getattr__(self, item):
        try:
            return self._store.data[item]
        except KeyError:
            raise AttributeError('\'{}\' attribute not found at Store!'.format(item))

    def persist(self):
        self._store.save()


class ConfigDestination(Enum):
    GLOBAL_CONFIG = 'global'
    LOCAL_CONFIG = 'local'
    STORE = 'store'


class Config:

    # Default values

    provider = None

    INI_MAPPING = {
        'provider': IniEntry('gitrack', str),
    }

    def __init__(self, repo, primary_source=ConfigDestination.LOCAL_CONFIG,
                 **kwargs):  # type: (git.Repo, ConfigDestination, **typing.Any) -> None

        self._bootstrap_sources(repo, primary_source)

        # Validate that only proper attributes are set
        for key, value in kwargs.items():
            if key.isupper() or key[0] == '_':
                raise AttributeError('You can not overload constants (eq. uppercase attributes) and private attributes'
                                     '(eq. variables starting with \'_\')!')

            setattr(self, key, value)

    def _bootstrap_sources(self, repo, primary_source):
        self._store = Store(repo)
        self._store.load()

        self._sources = (
            IniConfigSource(pathlib.Path(repo.git_dir).parent / LOCAL_CONFIG_NAME, self.INI_MAPPING),
            StoreConfigSource(self._store),
            IniConfigSource(pathlib.Path(appdirs.user_config_dir(APP_NAME)) / 'default.config', self.INI_MAPPING),
        )

        if primary_source == ConfigDestination.STORE:
            self._primary_source = self._sources[0]
        elif primary_source == ConfigDestination.LOCAL_CONFIG:
            self._primary_source = self._sources[1]
        elif primary_source == ConfigDestination.GLOBAL_CONFIG:
            self._primary_source = self._sources[2]

    @property
    def store(self):
        return self._store

    @property
    def provider_class(self):
        return PROVIDERS(self.provider).klass()

    def get_providers_config(self, provider_name):
        provider_config = {}

        for source in reversed(self._sources):
            provider_config.update(source.get_providers_config(provider_name))

        return provider_config

    def set_providers_config(self, provider_name, items):
        self._primary_source.set_providers_config(provider_name, items)

    def persist(self):  # type: () -> None
        self._primary_source.persist()

    def __getattribute__(self, item):  # type: (str) -> typing.Any
        """
        Implements hierarchy lookup as described in the class docstring.
        """
        item_exists = True
        retrieved_value = None
        try:
            retrieved_value = object.__getattribute__(self, item)
        except AttributeError:
            item_exists = False

        # We are not interested in special attributes (private attributes or constants, methods)
        # for the hierarchy lookup
        if item.isupper() or item[0] == '_' or (item_exists and callable(retrieved_value)):
            return retrieved_value

        # Retrieved value differs from the class attribute ==> it is instance's value, which has highest priority
        if item_exists and self._get_class_attribute(item) != retrieved_value:
            return retrieved_value

        for source in self._sources:
            try:
                return getattr(source, item)
            except AttributeError:
                pass

        if not item_exists:
            raise AttributeError

        return retrieved_value

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if self._primary_source is not None:
            setattr(self._primary_source, key, value)

    def _get_class_attribute(self, attr):  # type: (str) -> typing.Any
        return self.__class__.__dict__.get(attr)


# TODO: [Q] Should I use CachedFactoryMeta for this? (eq. Singleton with parameter)
class Store:

    def __init__(self, repo):  # type: (git.Repo) -> None
        name = self.repo_name(repo)
        path = pathlib.Path(appdirs.user_data_dir(APP_NAME)) / 'repos'
        path.mkdir(parents=True, exist_ok=True)
        self._path = path / (name + '.pickle')  # type: pathlib.Path

        if not self._path.exists():
            raise exceptions.UninitializedRepoException('Repo \'{}\' has not been initialized!'.format(name))

        self.data = {}

        atexit.register(self.save)

    def load(self):
        with self._path.open('rb') as file:
            self.data = pickle.load(file)

    def save(self):
        with self._path.open('wb') as file:
            pickle.dump(self.data, file)

    @staticmethod
    def repo_name(repo):
        # TODO: Proper escaping of the path
        # TODO: Check for too long strings
        return repo.git_dir[1:].replace('/', '_').replace('_.git', '')

    @classmethod
    def is_repo_initialized(cls, repo):  # type: (git.Repo) -> bool
        name = cls.repo_name(repo)
        path = pathlib.Path(appdirs.user_data_dir(APP_NAME)) / 'repos' / (name + '.pickle')
        return path.exists()

    # TODO: Refactor usage of appdirs into separate fnc and use GITRACK_DEV envvar
    @classmethod
    def init_repo(cls, repo):
        name = cls.repo_name(repo)
        path = pathlib.Path(appdirs.user_data_dir(APP_NAME)) / 'repos'
        path.mkdir(parents=True, exist_ok=True)
        repo_file = path / (name + '.pickle')  # type: pathlib.Path

        with repo_file.open('wb') as file:
            pickle.dump({}, file)
