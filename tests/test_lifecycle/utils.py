from pathlib import Path

from pytest_factory.framework.mall import MALL


def get_file_path(join: str):
    p = Path(MALL._config_path).parent
    p = p.joinpath(join)
    return p
