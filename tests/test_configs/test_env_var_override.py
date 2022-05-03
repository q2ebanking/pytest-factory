import os

def test_env_var(store):
    result = os.environ.get('TEST')
    assert result == '404'