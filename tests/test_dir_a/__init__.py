import configparser
from pytest_factory.framework.stores import STORES

conf = configparser.ConfigParser()

conf.read('tests/config.ini')


# Add to STORES for this test dir

STORES.default_handler_class = conf.get('test_dir_a', 'default_handler_class')
