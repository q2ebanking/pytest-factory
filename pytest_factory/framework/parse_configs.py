import json
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Callable, Optional, Any
from importlib import import_module

from pytest_factory.logger import get_logger
from pytest_factory.framework.exceptions import ConfigException
from pytest_factory.framework.mall import MALL

logger = get_logger(__name__)


def get_config_parser(path: str = '../**/config.ini') -> ConfigParser:
    config = ConfigParser()
    p = Path()
    p_list = list(p.glob(path))
    if len(p_list) != 1:
        raise ConfigException(log_msg=f'{path} is missing from project!')
    config.read(p_list[0])
    return config


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


CONFIG_MAP = {
    'tuples': lambda x: x.split(","),
    'imports': import_from_str_path,
    'bools': lambda x: x.lower() == 'true',
    'dicts': lambda x: json.loads(x)
}


def clean_whitespace(input: list) -> list:
    return [x.strip() for x in input]


def parse_type(section: str, _type: str, parse_func: Callable, conf: ConfigParser) -> dict:
    str_to_split = conf.get(section, _type, fallback=None)
    if not str_to_split:
        return {}
    split_str = str_to_split.split(",") if str_to_split else []
    sub_dict = {}
    for k in clean_whitespace(split_str):
        sub_dict[k] = parse_func(conf.get(section=section, option=k))

    return sub_dict


def parse_section(conf: ConfigParser, section: str = 'tests') -> Dict:
    try:
        conf[section]
    except KeyError as ke:
        msg = f"test suite is missing config.ini OR config.ini is missing section \"{ke}\"!"
        raise ConfigException(log_msg=msg)

    conf_dict = {}

    for _type, parse_func in CONFIG_MAP.items():
        new_config = parse_type(section=section, _type=_type, parse_func=parse_func, conf=conf)
        conf_dict.update(new_config)

    keys = set(conf[section].keys()).difference(set(conf_dict.keys()))
    for key in keys:
        if key not in CONFIG_MAP.keys():
            conf_dict[key] = conf[section][key]

    return conf_dict


def prep_stores_update_local(dir_name: Optional[str] = 'tests', path: Optional[str] = '../**/config.ini') -> Dict[str, Any]:
    """Prep config values"""
    conf = get_config_parser(path=path)
    conf_dict = parse_section(conf=conf)

    sub_dict = parse_section(conf=conf, section=dir_name)
    conf_dict.update(sub_dict)

    MALL.load(conf=conf_dict, key=dir_name)
    return conf_dict
