import re
from typing import List


def assert_fuzzy_str_compare(patterns: List[str, re.Pattern], a: str, b: str):
    _a = a
    _b = b
    repl = '*REDACTED BY TORNADO DRILL*'
    for pattern in patterns:
        _a = re.sub(pattern=pattern, string=_a, repl=repl)
        _b = re.sub(pattern=pattern, string=_b, repl=repl)
    assert _a == _b