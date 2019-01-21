import configparser
import logging
import os
import pathlib
import pickle
import typing
import abc
import pprint
from collections import namedtuple
from enum import Enum

import appdirs

from gitrack import exceptions, APP_NAME, LOCAL_CONFIG_NAME, Providers, TaskParsingModes

IniEntry = namedtuple('IniEntry', ['section', 'type'])
logger = logging.getLogger('gitrack.config')


def get_data_dir():  # type: () -> pathlib.Path
    if 'GITRACK_STORAGE' in os.environ:
        return pathlib.Path(os.environ.get('GITRACK_STORAGE')) / 'data'

    return pathlib.Path(appdirs.user_data_dir(APP_NAME))


def get_config_dir():  # type: () -> pathlib.Path
    if 'GITRACK_STORAGE' in os.environ:
        return pathlib.Path(os.environ.get('GITRACK_STORAGE')) / 'config'

    return pathlib.Path(appdirs.user_config_dir(APP_NAME))


def repo_name(repo_dir):  # type: (pathlib.Path) -> str
    name = str(repo_dir)[1:].replace('/', '_').replace('\\', '_')
    return name[-250:]  # Most of file-systems has restriction on length of filename around 250 chars


def is_repo_initialized(repo_dir):  # type: (pathlib.Path) -> bool
    name = repo_name(repo_dir)
    path = get_data_dir() / 'repos' / name
    return path.exists()


class ConfigSource(abc.ABC):
    """
    Interface definition of Config's source.
    """

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
    """
    Config source implementation that store the data in .ini file.

    As .ini files have sections (eq. 2 levels) and the config instance's attributes don't (eq. 1 level).
    This config source depends on mapping which maps the attribute's name to proper .ini's section.
    """

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
        elif entry.type == str:
            return self._store.get(entry.section, item)
        else:
            return entry.type(self._store.get(entry.section, item))

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
    """
    Config source implementation that stores the data into provided giTrack's store.
    """
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

    def get_providers_config(self, provider_name):
        try:
            return getattr(self, provider_name)
        except AttributeError:
            return {}

    def set_providers_config(self, provider_name, items):
        setattr(self, provider_name, items)


class ConfigDestination(Enum):
    GLOBAL_CONFIG = 'global'
    LOCAL_CONFIG = 'local'
    STORE = 'store'


class Config:
    """
    Main Config class, that handles hierarchical data sources.

    There are three sources:
     - Local config (eq. .gitrack file placed in root of the Git repo)
     - Store (see bellow)
     - Global config (eq. config file common for all Git repos)

    The lookup of attributes is done in order showed above.

    Regarding saving the configuration, there is set one source as primary and upon calling 'persist()' method
    changes are stored only into this source.
    """

    # Default values
    provider = None
    project_support = False
    tasks_support = False
    update_check = True

    INI_MAPPING = {
        'provider': IniEntry('gitrack', Providers),

        'update_check': IniEntry('gitrack', bool),

        'project_support': IniEntry('gitrack', bool),
        'project': IniEntry('gitrack', str),

        'tasks_support': IniEntry('gitrack', bool),
        'tasks_mode': IniEntry('gitrack', TaskParsingModes),
        'tasks_regex': IniEntry('gitrack', str),
        'tasks_value': IniEntry('gitrack', str),
    }

    def __init__(self, repo_dir, primary_source=ConfigDestination.LOCAL_CONFIG,
                 **kwargs):  # type: (pathlib.Path, ConfigDestination, **typing.Any) -> None
        self._repo_dir = repo_dir
        self._repo_name = repo_name(repo_dir)
        self._bootstrap_sources(repo_dir, primary_source)

        # Validate that only proper attributes are set
        for key, value in kwargs.items():
            if key.isupper() or key[0] == '_':
                raise AttributeError('You can not overload constants (eq. uppercase attributes) and private attributes'
                                     '(eq. variables starting with \'_\')!')

            setattr(self, key, value)

    def _bootstrap_sources(self, repo_dir, primary_source):
        self._store = Store(self.repo_data_dir / 'data.pickle')

        self._sources = (
            IniConfigSource(self.get_local_config_file(repo_dir), self.INI_MAPPING),
            StoreConfigSource(self._store),
            IniConfigSource(self.get_global_config_file(), self.INI_MAPPING),
        )

        if primary_source == ConfigDestination.STORE:
            self._primary_source = self._sources[1]
        elif primary_source == ConfigDestination.LOCAL_CONFIG:
            self._primary_source = self._sources[0]
        elif primary_source == ConfigDestination.GLOBAL_CONFIG:
            self._primary_source = self._sources[2]

    @property
    def store(self):
        return self._store

    @property
    def repo_data_dir(self):
        return get_data_dir() / 'repos' / self._repo_name

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

    @classmethod
    def get_global_config_file(cls):  # type: () -> pathlib.Path
        return get_config_dir() / 'default.config'

    @classmethod
    def get_local_config_file(cls, repo_dir):  # type: (pathlib.Path) -> pathlib.Path
        return repo_dir / LOCAL_CONFIG_NAME


# TODO: [Q] Should I use CachedFactoryMeta for this? (eq. Singleton with parameter)
class Store:
    """
    Internal data storage.

    It utilize pickle serialization. Serialized file is stored in passed path. The path is by convention bound
    to Git's repo path. (Eq. moving Git repo will brake things)
    """

    def __init__(self, path):  # type: (pathlib.Path) -> None
        self._path = path
        if not self._path.exists():
            raise exceptions.UninitializedRepoException('Repo has not been initialized!')

        self.data = {}
        self.load()

    def __getitem__(self, item):
        return self.data.get(item)  # TODO: [Q] Is this good idea? Return None instead of KeyError?

    def __setitem__(self, key, value):
        self.data[key] = value

    def load(self):
        with self._path.open('rb') as file:
            self.data = pickle.load(file)
            logger.debug("Store loading from this path: {}\nThis data:\n{}".format(self._path, pprint.pformat(self.data)))

    def save(self):
        with self._path.open('wb') as file:
            logger.debug("Store saving to this path: {}\nThis data:\n{}".format(self._path, pprint.pformat(self.data)))
            pickle.dump(self.data, file)

    @classmethod
    def init_repo(cls, repo_dir):
        name = repo_name(repo_dir)
        path = get_data_dir() / 'repos' / name
        path.mkdir(parents=True, exist_ok=True)
        repo_file = path / 'data.pickle'  # type: pathlib.Path

        with repo_file.open('wb') as file:
            pickle.dump({}, file)

    @classmethod
    def get_for_repo(cls, repo_dir):
        name = repo_name(repo_dir)
        path = get_data_dir() / 'repos' / name / 'data.pickle'
        return cls(path)

    def __str__(self):
        return 'Store({})'.format(self._path)
