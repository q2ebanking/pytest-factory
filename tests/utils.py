import re
from typing import List, Union, Optional, Callable, Tuple

UUID_PATTERN = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
ISO_PATTERN_COMPLETE = r'\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+([+-][0-2]\d:[0-5]\d|)'
ISO_PATTERN_SECONDS = r'\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|)'
ISO_PATTERN_MINUTES = r'\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z)'
ISO_PATTERN_DATE = r'\d{4}-([0]\d|1[0-2])-([0-2]\d|3[01])'

DEFAULT_PATTERNS = {
    UUID_PATTERN: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
    ISO_PATTERN_COMPLETE: '1999-12-31T11:59:59.999',
    ISO_PATTERN_SECONDS: '1999-12-31T11:59:59',
    ISO_PATTERN_MINUTES: '1999-12-31T11:59',
    ISO_PATTERN_DATE: '1999-12-31'
}

Pattern = Union[str, re.Pattern]
PatternOrPatterns = Union[Pattern, List[Pattern]]
Repl = Union[str, Callable]


def mask(patterns: PatternOrPatterns, string: str, repl: Optional[Repl] = None) -> str:
    if not patterns:
        patterns = DEFAULT_PATTERNS
    if not isinstance(patterns, list):
        patterns = [patterns]
    s_masked = string
    for pattern in patterns:
        repl = repl or DEFAULT_PATTERNS.get(pattern, 'MASKED')
        _repl = repl if isinstance(repl, str) else repl(pattern)
        s_masked = re.sub(pattern=pattern, string=s_masked, repl=repl)
    return s_masked


def get_masked_pair(patterns: PatternOrPatterns, a: str, b: str,
                    repl: Optional[Repl] = None) -> Tuple[str, str]:
    _a = mask(string=a, patterns=patterns, repl=repl)
    _b = mask(string=b, patterns=patterns, repl=repl)
    return _a, _b


def get_logs(caplog, levelname: str = 'WARNING') -> List[str]:
    actual = [rec.message for rec in caplog.records if rec.levelname == levelname]
    return actual
