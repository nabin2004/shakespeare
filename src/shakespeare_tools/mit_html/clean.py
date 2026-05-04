"""Normalize extracted text."""

from __future__ import annotations

import html
import re

_ZW_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")

_CURLY = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": "--",
        "\u2013": "-",
    }
)


def clean_text(s: str, *, normalize_quotes: bool = False) -> str:
    s = html.unescape(s)
    s = _ZW_RE.sub("", s)
    t = re.sub(r"\s+", " ", s).strip()
    if normalize_quotes:
        t = t.translate(_CURLY)
    return t


def speaker_normalized(speaker: str) -> str:
    """Uppercase fold for deduplication hints (optional downstream use)."""
    return re.sub(r"\s+", " ", speaker.strip()).upper()
