"""Parsers for voice command phrases used in the trading dialog.

This module provides simple heuristics to extract numeric allocations (percent or dollars)
and confirmation/abort intents from free text. It is intentionally conservative and
falls back to safe behaviors when ambiguous.
"""
import re
from typing import Optional, Tuple


_confirm_phrases = [r'^(confirm|yes|proceed|place order|place it|ok|okay)$']
_cancel_phrases = [r'^(cancel|abort|stop|do not place|don\'t place)$']
_use_suggested = [r'^(use suggested|use recommended|use recommended allocation|use suggested allocation)$']


def _match_any(text: str, patterns):
    t = text.strip().lower()
    for p in patterns:
        if re.search(p, t):
            return True
    return False


def parse_confirm(text: str) -> Optional[str]:
    """Return 'confirm', 'cancel', 'use_suggested' or None if unknown."""
    if not text:
        return None
    t = text.strip().lower()
    if _match_any(t, _confirm_phrases):
        return 'confirm'
    if _match_any(t, _cancel_phrases):
        return 'cancel'
    if _match_any(t, _use_suggested):
        return 'use_suggested'
    # allow short tokens
    if t in ('yes', 'y', 'confirm'):
        return 'confirm'
    if t in ('no', 'n', 'cancel'):
        return 'cancel'
    return None


def parse_allocation(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Parse allocation from text. Returns (value, unit) where unit is 'pct' or 'usd'.

    Examples:
    - 'one percent' -> (1.0, 'pct')
    - '2%' -> (2.0, 'pct')
    - '100 dollars' -> (100.0, 'usd')
    - 'use suggested' -> (None, 'use_suggested')
    - None or ambiguous -> (None, None)
    """
    if not text:
        return None, None
    t = text.lower().strip()
    if _match_any(t, _use_suggested):
        return None, 'use_suggested'

    # percent like 2% or 2 percent
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", t)
    if m:
        return float(m.group(1)), 'pct'
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(percent|per cent|percent of portfolio)", t)
    if m:
        return float(m.group(1)), 'pct'

    # dollars like $100 or 100 dollars
    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)", t)
    if m:
        return float(m.group(1)), 'usd'
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(dollars|usd|bucks)", t)
    if m:
        return float(m.group(1)), 'usd'

    # natural language small numbers (one, two)
    words_to_num = {
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'ten': 10
    }
    for w, n in words_to_num.items():
        if re.search(rf'\b{w}\b', t):
            # assume percent if small number present
            return float(n), 'pct'

    return None, None
