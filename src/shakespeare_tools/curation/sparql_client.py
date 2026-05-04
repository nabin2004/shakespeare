"""Minimal read-only SPARQL client (HTTP JSON results)."""

from __future__ import annotations

import os
from typing import Any

import httpx


class SparqlClient:
    def __init__(self, endpoint: str, *, timeout_s: float = 30.0) -> None:
        self.endpoint = endpoint
        self.timeout_s = timeout_s

    @classmethod
    def from_env(cls) -> "SparqlClient | None":
        url = os.environ.get("SPARQL_ENDPOINT", "http://localhost:7878/query")
        if not url:
            return None
        return cls(url)

    def select(self, query: str) -> list[dict[str, Any]]:
        r = httpx.post(
            self.endpoint,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        bindings = data.get("results", {}).get("bindings", [])
        rows: list[dict[str, Any]] = []
        for b in bindings:
            row = {k: v.get("value") for k, v in b.items()}
            rows.append(row)
        return rows

    def ask(self, query: str) -> bool:
        r = httpx.post(
            self.endpoint,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        return r.json().get("boolean", False)
