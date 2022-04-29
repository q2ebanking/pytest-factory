from typing import List


def get_logs(caplog, levelname: str = 'WARNING') -> List[str]:
    actual = [rec.message for rec in caplog.records if rec.levelname == levelname]
    return actual
