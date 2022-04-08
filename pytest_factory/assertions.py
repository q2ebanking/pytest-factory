import re
from typing import List


def compare_similar_strings(patterns: List[str, re.Pattern], a: str, b: str):
    _a = a
    _b = b
    repl = '*REDACTED BY pytest-factory*'
    for pattern in patterns:
        _a = re.sub(pattern=pattern, string=_a, repl=repl)
        _b = re.sub(pattern=pattern, string=_b, repl=repl)
    return _a == _b
