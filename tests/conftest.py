from pytest_factory.framework.parse_configs import prep_stores_update_local

prep_stores_update_local(dir_name=__name__.split('.')[0])

pytest_plugins = ["pytest_factory.framework.pytest"]
