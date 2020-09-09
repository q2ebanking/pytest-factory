"""
pytest integration hooks

the  following functions are predefined hooks in pytest
"""

from _pytest.config import Config

from settings import Settings


def pytest_configure(config: Config) -> None:
    # load settings
    # initialize mock store
    pass
