from pathlib import Path
from configparser import ConfigParser
from pytest_factory.framework.parse_configs import prep_stores_update_local

from pytest_factory.framework.mall import STORES

# DIR_NAME must match config.ini section
DIR_NAME = __name__
config = ConfigParser()

# TODO this does not work with pycharm visual debugger which moves the CWD around so that this relative path breaks
#  need to reimplement using pathlib.glob?
p = Path()
p_list = list(p.glob("**/config.ini"))
if len(p_list) != 1:
    raise Exception('config.ini is missing from project!')
config.read(p_list[0])

# Add to STORES for this test dir
conf_dict = prep_stores_update_local(dir_name="default", conf=config)
STORES.load(conf=conf_dict, key=DIR_NAME)
