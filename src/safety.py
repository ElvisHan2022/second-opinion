"""Safety filter: never show dosing for non-FDA-approved peptides (AGENTS.md hard rule).

`redact_dosing` replaces every sentence that holds a dose (number + unit) within
120 characters of a non-approved peptide name. Doses for approved drugs such as
semaglutide pass through unchanged. Stdlib only.
"""
from __future__ import annotations

import re

NON_APPROVED_PEPTIDES: list[str] = ["BPC-157", "BPC 157", "TB-500", "ipamorelin", "CJC-1295"]

# Number (with optional decimal: "2.4", "7·2", "0,5") followed by a dose unit.
DOSE_PATTERN: re.Pattern = re.compile(
    r"\d+(?:[.,·]\d+)?\s*(?:mg|mcg|µg|μg|ug|units?|iu)\b", re.IGNORECASE)

REDACTION = "[removed: dosing for a non-approved peptide]"
WINDOW = 120


def _name_pattern(name: str) -> str:
    # "BPC-157" also matches "BPC 157" and "BPC157"; same for the other hyphenated names.
    return r"[-\s]?".join(re.escape(part) for part in re.split(r"[-\s]", name))


PEPTIDE_PATTERN: re.Pattern = re.compile(
    "|".join(_name_pattern(n) for n in NON_APPROVED_PEPTIDES), re.IGNORECASE)

# A sentence runs to ., ! or ? followed by whitespace or end of text, so the
# decimal point in "2.4 mg" does not end a sentence.
_SENTENCE = re.compile(r"\S.*?(?:[.!?](?=\s|$)|$)", re.DOTALL)


def _dose_near_peptide(text: str, start: int, end: int) -> bool:
    for m in DOSE_PATTERN.finditer(text, start, end):
        lo, hi = max(0, m.start() - WINDOW), min(len(text), m.end() + WINDOW)
        if PEPTIDE_PATTERN.search(text, lo, hi):
            return True
    return False


def redact_dosing(text: str) -> tuple[str, bool]:
    """Return (text with dosing sentences replaced, whether anything was replaced)."""
    spans = [m.span() for m in _SENTENCE.finditer(text) if _dose_near_peptide(text, *m.span())]
    for start, end in reversed(spans):
        text = text[:start] + REDACTION + text[end:]
    return text, bool(spans)
