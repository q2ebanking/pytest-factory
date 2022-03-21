from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Callable
from importlib import import_module
import pytest_factory.framework.default_configs as defaults


def get_config_parser(filename: str = 'config.ini') -> ConfigParser:
    config = ConfigParser()
    p = Path()
    p_list = list(p.glob(f"../**/{filename}"))
    if len(p_list) != 1:
        raise Exception(f'{filename} is missing from project!')
    config.read(p_list[0])
    return config


def import_from_str_path(path: str) -> Callable:
    path_parts = path.split('.')
    import_path = '.'.join(path_parts[:-1])
    import_callable = path_parts[-1]
    module = import_module(import_path)
    kallable = getattr(module, import_callable)
    return kallable


CONFIG_MAP = {
    'tuples': lambda x: x.split(","),
    'imports': import_from_str_path,
    'bools': lambda x: x.lower() == 'true'
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
        default_value = getattr(defaults, k) if hasattr(defaults, k) else None
        sub_dict[k] = parse_func(conf.get(section=section, option=k, fallback=default_value))

    return sub_dict


def prep_defaults(conf: ConfigParser) -> Dict:
    conf_dict = {}
    for _type, parse_func in CONFIG_MAP.items():
        conf_dict.update(parse_type(section="default", _type=_type, parse_func=parse_func, conf=conf))

    return conf_dict


def prep_stores_update_local(
        dir_name: str,
        conf: ConfigParser,
        defaults: dict = None,
) -> Dict:
    """Prep config values"""
    conf_dict = prep_defaults(conf=conf) if defaults is None else defaults

    # In each config.ini block, there are keys: paths, tuples
    # these are to note what handling the values in the matching keys need

    # For example, keys listed in the paths value need to cast to Path()
    # Because the paths values from config.ini is a tuple, it needs to be split

    for _type, parse_func in CONFIG_MAP.items():
        sub_dict = parse_type(section=dir_name, _type=_type, parse_func=parse_func, conf=conf)
        conf_dict.update(sub_dict)

    # Check if any other string-only values need to be added
    keys = set(conf[dir_name].keys()).difference(set(conf_dict.keys()))

    # If we try to remove a key that isn't in the set, it will error
    no_add_present = [x for x in CONFIG_MAP.keys() if x in keys]
    # Remove those from the set
    [keys.remove(item) for item in no_add_present]

    additions = {k: conf.get(dir_name, k) for k in keys}
    conf_dict.update(additions)

    return conf_dict
