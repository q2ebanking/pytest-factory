# IMPORTANT do not put whitespace around commas in the config.ini
import configparser
from pathlib import Path

from pytest_factory.framework.stores import STORES

config = configparser.ConfigParser()
config.read("tests/config.ini")


def prep_defaults(conf: configparser.ConfigParser = config):
    paths_to_parse = conf.get("default", "paths").split(",")
    paths = {k: Path(conf.get("default", k)) for k in paths_to_parse}

    tups_to_split = conf.get("default", "tuples").split(",")
    tups = {k: conf.get("default", k).split(",") for k in tups_to_split}

    return {**paths, **tups}


def prep_stores_update_local(
    dir_name: str = "test_dir_a",
    conf: configparser.ConfigParser = config,
    defaults: dict = prep_defaults(),
):
    """Prep config values"""
    conf_dict = {}
    conf_dict.update(defaults)

    # In each config.ini block, there are keys: paths, tuples
    # these are to note what handling the values in the matching keys need

    # For example, keys listed in the paths value need to cast to Path()
    # Because the paths values from config.ini is a tuple, it needs to be split
    paths_to_parse = conf.get(dir_name, "paths").split(",")
    paths = {k: Path(conf.get(dir_name, k)) for k in paths_to_parse}
    conf_dict.update(paths)

    request_handler = conf_dict.get("request_handler_class")
    # QUESTION Assuming that this shouldn't be in the conf dict
    conf_dict.pop("request_handler_class")
    return request_handler, conf_dict


# Add to STORES for this test dir
request_handler, conf_dict = prep_stores_update_local()
STORES.default_handler_class = request_handler
STORES.load(conf=conf_dict, key="test_dir_a")
