from typing import List

from pytest_factory.parameterization.cause_failures import cause_failures
from pytest_factory.framework.stores import Store, STORES

# from parse_logs import parse_logs
# from diff_recordings import diff_recordings

PARAMETRIZATION_SEQUENCE = [
    cause_failures,
    # live_connections,
    # parse_logs,
    # diff_recordings
]


def pytest_generate_tests(metafunc: "Metafunc") -> None:
    """
    takes metafunc and passes the contained Item to the parametrizer
    which returns a dictionary of new tests and generated Store fixtures.
    metafunc.parametrize is called to add new test cases
    :param metafunc: contains metadata for test function and references
        to test config and definition
    """
    item = metafunc.definition
    store = STORES.get_store(test_name=item.name)
    parametrized_stores: List[Store] = [store]  # seeding stores with original
    for parametrizer in PARAMETRIZATION_SEQUENCE:
        if item.get_closest_marker(parametrizer.__name__):
            parametrizer(test_name=item.name, stores=parametrized_stores)
    argnames = 'store'
    if len(parametrized_stores) > 1:
        # remove original store so we don't duplicate
        parameterized_stores = parametrized_stores[1:]
        metafunc.parametrize(argnames=argnames, argvalues=parameterized_stores)
