import os


def test_env_vars(update_env_vars):
    """Demo of a test function using the fixture
    to change values set on the environment temporarily.
    """
    fake_value = os.getenv("ENV")
    assert fake_value == "test"
