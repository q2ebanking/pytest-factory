from configparser import ConfigParser
from pytest_factory.framework.parse_configs import prep_stores_update_local

from pytest_factory.framework.stores import STORES

# DIR_NAME must match config.ini section
DIR_NAME = __name__
config = ConfigParser()

# TODO this does not work with pycharm visual debugger which moves the CWD around so that this relative path breaks
#  need to reimplement using pathlib.glob?
config.read("tests/config.ini")

# Add to STORES for this test dir
conf_dict = prep_stores_update_local(dir_name="default", conf=config)
STORES.load(conf=conf_dict, key=DIR_NAME)
