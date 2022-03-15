import configparser
from typing import Tuple, Dict, Callable
from importlib import import_module
import pytest_factory.framework.default_configs as defaults

conf_dict = {}
CONFIG_MAP = {
    'tuples': lambda x: x.split(","),
    'paths': lambda x: x.split('.'),
    'bools': lambda x: bool(x)
}


def clean_whitespace(input: list) -> list:
    return [x.strip() for x in input]


def parse_type(section: str, _type: str, parse_func: Callable, conf: configparser.ConfigParser) -> dict:
    str_to_split = conf.get(section, _type, fallback=None)
    if not str_to_split:
        return {}
    split_str = str_to_split.split(",") if str_to_split else []
    sub_dict = {}
    for k in clean_whitespace(split_str):
        default_value = getattr(defaults, k) if hasattr(defaults, k) else None
        sub_dict[k] = parse_func(conf.get(section=section, option=k, fallback=default_value))

    return sub_dict


def prep_defaults(conf: configparser.ConfigParser) -> Dict:
    conf_dict = {}
    for _type, parse_func in CONFIG_MAP.items():
        conf_dict.update(parse_type(section="default", _type=_type, parse_func=parse_func, conf=conf))

    return conf_dict


def prep_stores_update_local(
        dir_name: str,
        conf: configparser.ConfigParser,
        defaults: dict = None,
) -> Tuple[Callable, Dict]:
    """Prep config values"""
    defaults = prep_defaults(conf=conf) if defaults is None else defaults
    conf_dict.update(defaults)

    # In each config.ini block, there are keys: paths, tuples
    # these are to note what handling the values in the matching keys need

    # For example, keys listed in the paths value need to cast to Path()
    # Because the paths values from config.ini is a tuple, it needs to be split

    for _type, parse_func in CONFIG_MAP.items():
        sub_dict = parse_type(section="default", _type=_type, parse_func=parse_func, conf=conf)
        conf_dict.update(sub_dict)

    # The request_handler is a path, so we know it will be
    # in the conf_dict, but we don't actually want it to
    # be there. It gets added to STORES separately.
    request_handler_path_list: list = conf_dict.get("request_handler_class")

    conf_dict.pop("request_handler_class")

    # Check if any other string-only values need to be added
    keys = set(conf[dir_name].keys()).difference(set(conf_dict.keys()))
    # Keys we don't want to add
    no_add = ["request_handler_class", *list(CONFIG_MAP.keys())]
    # If we try to remove a key that isn't in the set, it will error
    no_add_present = [x for x in no_add if x in keys]
    # Remove those from the set
    [keys.remove(item) for item in no_add_present]

    additions = {k: conf.get(dir_name, k) for k in keys}
    conf_dict.update(additions)
    request_handler_path = '.'.join(request_handler_path_list[:-1])
    request_handler_class_name = request_handler_path_list[-1]
    # TODO maybe a try block here
    request_handler_module = import_module(request_handler_path)
    # TODO maybe a try block here
    request_handler_class = getattr(request_handler_module, request_handler_class_name)
    return request_handler_class, conf_dict


CONFIGS = conf_dict
