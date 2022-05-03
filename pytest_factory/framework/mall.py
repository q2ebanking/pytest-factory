import os
from pytest import Item, Session
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Iterable, Union
from functools import cached_property
from importlib import import_module

from pytest_factory.framework.store import Store, is_plugin
from pytest_factory import logger
from pytest_factory.framework.exceptions import ConfigException
from pytest_factory.framework.parse_configs import prep_stores_update_local, DEFAULT_FOLDER_NAME
from pytest_factory.framework.default_configs import (assert_no_missing_calls as default_assert_no_missing_calls,
                                                      assert_no_extra_calls as default_assert_no_extra_calls)

logger = logger.get_logger(__name__)


def import_from_str_path(path: str) -> Callable:
    path_parts = path.split('.')
    import_path = '.'.join(path_parts[:-1])
    import_callable = path_parts[-1]
    module = import_module(import_path)
    try:
        kallable = getattr(module, import_callable)
    except AttributeError as _:
        kallable = import_module(path)
    return kallable


class Mall:
    """
    this class contains all the stores for all collected tests and defines
    convenience methods for looking up test doubles
    """

    def __init__(self):
        self._by_test: Dict[str, Store] = {}
        self._by_dir: Dict[str, Dict] = {}
        self._backup_env_vars: Dict[str, str] = {}
        self._current_test: Optional[str] = None
        self._current_test_dir: Optional[str] = None
        self._monkey_patch_configs: Dict[str, Dict[str, Union[Callable, Dict[str, Callable]]]] = {}

    def __getattr__(self, name):
        if name not in vars(self).keys():
            return self._get_prop(name)

    def get_constructor(self, handler_type: str) -> Callable:
        return self._monkey_patch_configs.get(handler_type, {}).get('constructor')

    def load_monkeypatch_configs(self, callable_obj: Any,
                                 patch_members: Dict[str, Any],
                                 constructor: Optional[Callable] = None):
        key = callable_obj.__name__
        patch_configs = self._monkey_patch_configs.get(key)
        if patch_configs:
            self._monkey_patch_configs[key].get('patch_methods').update(patch_members)
            if constructor:
                self._monkey_patch_configs[key]['constructor'] = constructor
        else:
            self._monkey_patch_configs[callable_obj.__name__] = {
                'callable': callable_obj,
                'patch_methods': patch_members,
                'constructor': constructor
            }

    def get_monkeypatch_configs(self) -> Iterable:
        return self._monkey_patch_configs.values()

    def _get_prop(self, key: str) -> Any:
        prop = self._by_dir.get(self._current_test_dir, {}).get(key)
        if self._current_test_dir == 'tests':
            return prop
        elif prop is None:
            prop = self._by_dir.get('tests', {}).get(key)
        return prop

    def get_full_path(self, new_file_name: Optional[str] = None):
        p = Path(self._config_path)
        p = p.parent
        if new_file_name:
            p = p.joinpath(new_file_name)
        return p

    @property
    def env_vars(self) -> Dict[str, Any]:
        return self._get_prop('env_vars') or {}

    @property
    def sut_callable(self) -> Callable:
        return self._get_prop('sut_callable')

    @property
    def assert_no_missing_calls(self) -> bool:
        return self._get_prop('assert_no_missing_calls') or default_assert_no_missing_calls

    @property
    def assert_no_extra_calls(self) -> bool:
        return self._get_prop('assert_no_extra_calls') or default_assert_no_extra_calls

    def open(self, test_dir: str):
        test_dir = test_dir if test_dir[:5] == 'test_' else DEFAULT_FOLDER_NAME
        if test_dir:
            self._current_test_dir = test_dir

        conf = prep_stores_update_local(dir_name=test_dir)
        self._by_dir = conf
        env_vars = self.env_vars or {}
        self._backup_env_vars.update({k: os.getenv(k) for k, v in env_vars.items()})
        for k, v in env_vars.items():
            os.environ[k] = v

        for _dir, configs in self._by_dir.items():
            import_str = configs.get('imports')
            if import_str:
                import_keys = import_str.replace(' ', '').split(',')
                for key in import_keys:
                    module_path = configs.get(key)
                    if not module_path:
                        msg = f"could not find module path for key: {key} in section: {_dir} of config.ini"
                        raise ConfigException(log_msg=msg)
                    kallable = import_from_str_path(module_path)

                    self._by_dir[_dir][key] = kallable

    def close(self):
        for k, v in self._backup_env_vars.items():
            if v:
                os.environ[k] = v

    @cached_property
    def plugins(self) -> Dict[str, Callable]:
        return_dict = {}
        for _, v in self._by_dir.get('tests').items():
            if is_plugin(v):
                return_dict[v.PLUGIN_URL] = v
        return return_dict

    def get_store(self, item: Optional[Item] = None, test_name: Optional[str] = None,
                  test_dir: Optional[str] = None) -> Store:
        """
        :param item: pytest.Item
        :return: the Store associated with the given Item; a new Store if
            a Store has not already been created for this test
        """
        self._current_test = item.name if item else test_name or self._current_test
        self._current_test_dir = item.path.parent.name if item else test_dir or self._current_test_dir
        key = '.'.join([self._current_test_dir, self._current_test])
        store = self._by_test.get(key)
        if not store:
            store = Store(test_path=key)
            self._by_test[key] = store
        return store


MALL = Mall()
