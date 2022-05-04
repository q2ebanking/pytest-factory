from pytest_factory.framework.parse_configs import prep_stores_update_local, DEFAULT_FOLDER_NAME
from pytest_factory.framework.mall import MALL


def test_configs():
    prep_stores_update_local(dir_name='test_configs')
    assert MALL._current_test == 'test_configs'
    assert MALL._by_dir['test_configs']['string_var'] == 'BAR'

    conf_dict = prep_stores_update_local(dir_name=DEFAULT_FOLDER_NAME)
    assert conf_dict[DEFAULT_FOLDER_NAME]['string_var'] == 'FOO'
    assert MALL._by_dir[DEFAULT_FOLDER_NAME]['string_var'] == 'FOO'
    assert MALL.string_var == 'BAR'
    MALL._current_test_dir = DEFAULT_FOLDER_NAME
    assert MALL.string_var == 'FOO'
