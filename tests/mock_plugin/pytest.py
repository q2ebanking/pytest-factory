"""
pytest integration hooks

import path to this file must be in pytest_plugins in conftest.py

"""

from pytest_factory import logger

logger = logger.get_logger(__name__)
# TODO monkey patch overrides?

logger.info('mock_plugin loaded!')
