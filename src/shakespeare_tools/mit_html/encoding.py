"""Decode legacy MIT HTML bytes with charset from meta or ISO-8859-1 fallback."""

from __future__ import annotations

import re
from pathlib import Path

_CHARSET_RE = re.compile(r"charset\s*=\s*([a-zA-Z0-9._-]+)", re.IGNORECASE)
_META_CT_RE = re.compile(
    r'<meta\s+http-equiv\s*=\s*["\']Content-Type["\']\s+content\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_CT_RE_ALT = re.compile(
    r'<meta\s+content\s*=\s*["\']([^"\']+)["\'][^>]*http-equiv\s*=\s*["\']Content-Type["\']',
    re.IGNORECASE,
)


def _detect_charset(snippet: str) -> str | None:
    m = _META_CT_RE.search(snippet)
    if not m:
        m = _META_CT_RE_ALT.search(snippet)
    if not m:
        return None
    cm = _CHARSET_RE.search(m.group(1))
    if not cm:
        return None
    return cm.group(1).lower()


def read_html_text(path: Path) -> str:
    data = path.read_bytes()
    head = data[:16384].decode("ascii", errors="ignore")
    charset = _detect_charset(head) or "iso-8859-1"
    try:
        return data.decode(charset, errors="replace")
    except LookupError:
        return data.decode("iso-8859-1", errors="replace")
