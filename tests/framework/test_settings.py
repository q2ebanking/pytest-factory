""""
TODO test inheritance and all that here - also add stuff for loading settings from files

"""

import pytest


@pytest.mark.asyncio
class TestAsync:
    """
    integration tests
    """
    async def test_settings_default_store(self, store):
        """
        settings/store integration test

        expect store to have fixtures defined in local settings.py and mock_plugin/settings.py
        :return:
        """
        assert False

    async def test_settings_handler_override(self, store):
        """
        settings/handler integration test

        expect handler to have overridden properties defined in local settings.py and mock_plugin/settings.py
        :return:
        """
        assert False


def test_settings_load():
    assert False


def test_settings_inherit():
    assert False
