from pytest_factory.framework.parse_configs import prep_stores_update_local, get_config_parser

from pytest_factory.framework.mall import MALL

# DIR_NAME must match config.ini section
DIR_NAME = __name__.split('.')[1]

config = get_config_parser()

# Add to MALL for this test dir
conf_dict = prep_stores_update_local(dir_name=DIR_NAME, conf=config)
MALL.load(conf=conf_dict, key=DIR_NAME)