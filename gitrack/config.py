import configparser
import pathlib
import pickle
import typing
from collections import namedtuple

import git
import appdirs

from . import exceptions, APP_NAME, LOCAL_CONFIG_NAME


IniEntry = namedtuple('IniEntry', ['section', 'type'])


class IniConfig:
    """
    Class mixin for implementing __getattribute__ which have a source of a data in config file that is implemented
    using ConfigParser.

    INI_MAPPING defines mapping of config (ini) file structure (eq. sections -> options) into just attribute's names.
    It also defines the types of the values for correct type casting.

    Only attributes that have entry in INI_MAPPING will be considered during the lookup, if the attribute does not have
    entry the look continues with propagating the lookup to next in line, with super().
    """

    def __init__(self, stores, **kwargs):  # type: (typing.Sequence[configparser.ConfigParser], **typing.Any) -> None
        self._stores = stores
        super().__init__(**kwargs)

    def _resolve_type(self, store, entry, item):  # type: (configparser.ConfigParser, IniEntry, str) -> typing.Any
        """
        Method returns value in config file defined by entry.section and item (eq. option).
        The value is type-casted into proper type defined in the entry.type.
        """
        if entry is None:
            return None

        if entry.type == bool:
            return store.getboolean(entry.section, item, fallback=None)
        elif entry.type == int:
            return store.getint(entry.section, item, fallback=None)
        elif entry.type == float:
            return store.getfloat(entry.section, item, fallback=None)
        else:
            return store.get(entry.section, item, fallback=None)

    def __getattribute__(self, item):  # type: (str) -> typing.Any
        """
        Attr lookup method which implements the main logic.
        """
        mapping_dict = object.__getattribute__(self, 'INI_MAPPING')
        if item in mapping_dict:
            for store in self._stores:
                value = self._resolve_type(store, mapping_dict[item], item)
                if value is not None:
                    return value

        return super().__getattribute__(item)

    @property
    def is_loaded(self):  # type: () -> bool
        """
        Method states if the config file associated with this config's instance was loaded. Eq. if the file exists,
        is readable and was loaded into memory.
        """
        return bool(self._loaded)


class Config(IniConfig):
    """
    Configuration class which implements hierarchy lookup to enable overloading configurations
    based on several aspects.

    Supported hierarchy in order of priority:
         1) config instance's dict if value is defined
         2) repo's config file
         3) global's config file
         4) class's dict for default fallback
    """

    # Default values

    datetime_format = 'LTS L'

    INI_MAPPING = {
        'api_token': IniEntry('auth', str),
    }

    def __init__(self, repo, **kwargs):  # type: (git.Repo, **typing.Any) -> None
        stores = (
            self._load_store(pathlib.Path(appdirs.user_config_dir(APP_NAME)) / 'default.config'),
            self._load_store(pathlib.Path(repo.git_dir).parent / LOCAL_CONFIG_NAME),
        )

        super().__init__(stores)

        self._store = Store(repo)
        self._store.load()

        # Validate that only proper attributes are set
        for key, value in kwargs.items():
            if key.isupper() or key[0] == '_':
                raise AttributeError('You can not overload constants (eq. uppercase attributes) and private attributes'
                                     '(eq. variables starting with \'_\')!')

            setattr(self, key, value)

    @property
    def store(self):
        return self._store

    @staticmethod
    def _load_store(path):  # type: (pathlib.Path) -> configparser.ConfigParser
        store = configparser.ConfigParser()

        if path.exists():
            store.read((str(path),))

        return store

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

        print('{}: {}'.format(item, type(retrieved_value)))

        # We are not interested in special attributes (private attributes or constants, methods)
        # for the hierarchy lookup
        if item.isupper() or item[0] == '_' or (item_exists and callable(retrieved_value)):
            return retrieved_value

        # Retrieved value differs from the class attribute ==> it is instance's value, which has highest priority
        if item_exists and self._get_class_attribute(item) != retrieved_value:
            return retrieved_value

        return super().__getattribute__(item)

    def _get_class_attribute(self, attr):  # type: (str) -> typing.Any
        return self.__class__.__dict__.get(attr)


class Store:

    def __init__(self, repo):  # type: (git.Repo) -> None
        try:
            name = repo.git_dir
        except AttributeError:
            name = str(repo)

        path = pathlib.Path(appdirs.user_data_dir(APP_NAME)) / 'repos'
        path.mkdir(parents=True, exist_ok=True)
        self._path = path / name + '.pickle'  # type: pathlib.Path

        if not self._path.exists():
            raise exceptions.UninitializedRepoException('Repo \'{}\' has not been initialized!'.format(name))

        self.data = {}

    def load(self):
        with self._path.open('r') as file:
            self.data = pickle.load(file)

    def save(self):
        with self._path.open('w') as file:
            pickle.dump(self.data, file)

    @classmethod
    def init_repo(cls, repo):
        name = repo.git_dir
        path = pathlib.Path(appdirs.user_data_dir(APP_NAME)) / 'repos'
        path.mkdir(parents=True, exist_ok=True)
        repo_file = path / name + '.pickle'  # type: pathlib.Path

        with repo_file.open('w') as file:
            pickle.dump({}, file)
