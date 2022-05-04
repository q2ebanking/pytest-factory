import json
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Callable, Optional, Any

from pytest_factory.framework.exceptions import ConfigException


def get_config_parser(path: Optional[str] = None) -> ConfigParser:
    config = ConfigParser()
    p = Path()
    path = path or '**/config.ini'
    p_list = list(p.glob(path))
    if len(p_list) < 1:
        path = '../' + path
        p_list = list(p.glob(path))
    if len(p_list) < 1:
        raise ConfigException(log_msg=f'{path} is missing from project!')
    config_path = p_list[0]
    config.read(config_path)
    config_path = config_path.resolve()
    config.set(DEFAULT_FOLDER_NAME, '_config_path', str(config_path))
    return config


CONFIG_MAP = {
    'tuples': lambda x: x.split(","),
    'imports': lambda x: x,
    'bools': lambda x: x.lower() == 'true',
    'dicts': lambda x: json.loads(x)
}

DEFAULT_FOLDER_NAME = 'tests'


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


def parse_section(conf: ConfigParser, section: str = DEFAULT_FOLDER_NAME) -> Dict:
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
        if key not in CONFIG_MAP.keys() or key == 'imports':
            conf_dict[key] = conf[section][key]

    return conf_dict


def prep_stores_update_local(dir_name: Optional[str] = DEFAULT_FOLDER_NAME,
                             path: Optional[str] = None) -> Dict[str, Any]:
    """Prep config values"""
    conf_dict = {}
    conf = get_config_parser(path=path)
    conf_dict[DEFAULT_FOLDER_NAME] = parse_section(conf=conf)

    if dir_name in conf.sections():
        sub_dict = parse_section(conf=conf, section=dir_name)
        conf_dict[dir_name] = sub_dict

    return conf_dict
