"""
pytest integration hooks

the  following functions are predefined hooks in pytest that we need to
either cancel out or modify

"""
from _pytest.config import Config
from tornado_drill.framework.settings import SETTINGS, Settings
from tornado_drill.framework.stores import Stores


def pytest_configure(config: Config) -> None:
    if not SETTINGS:
        Settings()

    Stores(default_store=SETTINGS.default_store)
