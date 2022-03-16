import configparser
from pytest_factory.framework.parse_configs import prep_stores_update_local

from pytest_factory.framework.mall import STORES

# DIR_NAME must match config.ini section
DIR_NAME = __name__.split('.')[1]

config = configparser.ConfigParser()
config.read("tests/config.ini")

# Add to STORES for this test dir
request_handler, conf_dict = prep_stores_update_local(dir_name=DIR_NAME, conf=config)
STORES.default_handler_class = request_handler
STORES.load(conf=conf_dict, key=DIR_NAME)

