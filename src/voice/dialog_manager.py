"""Hindi-aware command parsing.

Extends the parser with Hindi phrases and numbers.
"""
import re
from typing import Optional, Tuple


def _normalize(text: str) -> str:
    return (text or '').strip().lower()


_confirm_phrases = [
    r'^(confirm|yes|proceed|place order|place it|ok|okay)$',
    r'^(पुष्टि|पुष्टि करें|ठीक है|हाँ|करें)$',
    r'^(confirm kare|confirm karen|confirm kijiye)$'
]

_cancel_phrases = [
    r'^(cancel|abort|stop|do not place|don\'t place)$',
    r'^(रद्द|रद्द करें|रद्द करो|निरस्त|निरस्त करो|नहीं|नही|बंद)$',
    r'^(cancel karo|cancel kijiye|cancel karen)$'
]

_use_suggested = [
    r'^(use suggested|use recommended|use suggested allocation|use recommended allocation)$',
    r'^(सुझाव अनुसार|सुझाए अनुसार|जैसा सुझाया गया|सुझाव के अनुसार)$'
]


def parse_confirm(text: str) -> Optional[str]:
    t = _normalize(text)
    if not t:
        return None
    for pattern in _confirm_phrases:
        if re.fullmatch(pattern, t):
            return 'confirm'
    for pattern in _cancel_phrases:
        if re.fullmatch(pattern, t):
            return 'cancel'
    for pattern in _use_suggested:
        if re.fullmatch(pattern, t):
            return 'use_suggested'
    return None


_hindi_numbers = {
    'शून्य': 0, 'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पाँच': 5, 'पांच': 5,
    'छः': 6, 'छह': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
    'बीस': 20, 'तेईस': 23, 'पच्चीस': 25, 'साठ': 60, 'सौ': 100
}


def parse_allocation(text: str) -> Tuple[Optional[float], Optional[str]]:
    if not text:
        return None, None
    t = _normalize(text)
    for pat in _use_suggested:
        if re.fullmatch(pat, t):
            return None, 'use_suggested'

    # standard percent patterns
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%', t)
    if m:
        return float(m.group(1)), 'pct'
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(percent|प्रतिशत|प्रति शत)', t)
    if m:
        return float(m.group(1)), 'pct'

    # Hindi number + percent patterns like 'दो प्रतिशत' or 'एक प्रतिशत'
    for word, value in _hindi_numbers.items():
        if re.search(rf'{word}\s*(प्रतिशत|percent)', t):
            return float(value), 'pct'

    # dollar forms
    m = re.search(r'\$\s*([0-9]+(?:\.[0-9]+)?)', t)
    if m:
        return float(m.group(1)), 'usd'
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(dollars|usd|डॉलर|dollar)', t)
    if m:
        return float(m.group(1)), 'usd'
    for word, value in _hindi_numbers.items():
        if re.search(rf'{word}\s*(डॉलर|dollar)', t):
            return float(value), 'usd'

    return None, None
