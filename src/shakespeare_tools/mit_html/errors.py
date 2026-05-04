"""Non-fatal parse diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["warning", "error"]


@dataclass(frozen=True)
class ParseIssue:
    severity: Severity
    path: str
    message: str
    snippet: str | None = None
