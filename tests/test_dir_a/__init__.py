from configparser import ConfigParser
from pytest_factory.framework.parse_configs import prep_stores_update_local

from pytest_factory.framework.stores import STORES
from pytest_factory.framework.default_configs import default_config_parser as config

# DIR_NAME must match config.ini section
DIR_NAME = __name__.split('.')[1]

# TODO could use pathlib to find the config.ini for the user
config.read("tests/config.ini")

# Add to STORES for this test dir
request_handler, conf_dict = prep_stores_update_local(dir_name=DIR_NAME, conf=config)
STORES.default_handler_class = request_handler
STORES.load(conf=conf_dict, key=DIR_NAME)
