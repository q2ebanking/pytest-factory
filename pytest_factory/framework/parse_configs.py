# IMPORTANT do not put whitespace around commas in the config.ini
import configparser
from pathlib import Path



def clean_whitespace(input: list) -> list:

    return [x.strip() for x in input]


def parse_paths(section: str, conf: configparser.ConfigParser) -> list:
    paths_to_parse = conf.get(section, "paths", fallback=None)
    paths = paths_to_parse.split(",") if paths_to_parse else []
    paths = {k: Path(conf.get(section, k)) for k in clean_whitespace(paths)}

    return paths
    

def parse_tuples(section: str, conf: configparser.ConfigParser) -> list:
    tups_to_split = conf.get(section, "tuples", fallback=None)
    tups = tups_to_split.split(",") if tups_to_split else []
    tups = {k: conf.get(section, k).split(",") for k in clean_whitespace(tups)}

    return tups

def prep_defaults(conf: configparser.ConfigParser):
    
    paths = parse_paths(section='default', conf=conf)

    tups = parse_tuples(section="default", conf=conf)

    return {**paths, **tups}


def prep_stores_update_local(
    dir_name: str,
    conf: configparser.ConfigParser,
    defaults: dict = None,
):
    """Prep config values"""
    defaults = prep_defaults(conf=conf) if defaults is None else defaults
    conf_dict = {}
    conf_dict.update(defaults)

    # In each config.ini block, there are keys: paths, tuples
    # these are to note what handling the values in the matching keys need

    # For example, keys listed in the paths value need to cast to Path()
    # Because the paths values from config.ini is a tuple, it needs to be split
    paths = parse_paths(section=dir_name, conf=conf)
    if paths:
        conf_dict.update(paths)

    tuples = parse_tuples(section=dir_name, conf=conf)
    if tuples:
        conf_dict.update(tuples)

    # The request_handler is a path, so we know it will be
    # in the conf_dict, but we don't actually want it to
    # be there. It gets added to STORES separately.
    request_handler = conf_dict.get("request_handler_class")
    conf_dict.pop("request_handler_class")

    # Check if any other string-only values need to be added
    keys = set(conf[dir_name].keys()).difference(set(conf_dict.keys()))
    # Keys we don't want to add
    no_add = ['paths', 'tuples', 'request_handler_class']
    # If we try to remove a key that isn't in the set, it will error
    no_add_present = [x for x in no_add if x in keys]
    # Remove those from the set
    [keys.remove(item) for item in no_add_present]

    additions = {k: conf.get(dir_name, k) for k in keys}
    conf_dict.update(additions)
    return request_handler, conf_dict
