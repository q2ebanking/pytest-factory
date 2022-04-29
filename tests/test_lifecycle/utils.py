from pathlib import Path
from pytest_factory.framework.parse_configs import DEFAULT_FOLDER_NAME


def get_file_path(join: str):
    p = Path.cwd()
    if p.parts[-1] != DEFAULT_FOLDER_NAME:
        p = p.joinpath(DEFAULT_FOLDER_NAME)
    p = p.joinpath(join)
    return p
