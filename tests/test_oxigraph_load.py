"""Tests for Oxigraph HTTP loader (mocked, no Docker)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from shakespeare_tools.curation.graph_constants import INSTANCE_GRAPH_IRI, ONTOLOGY_GRAPH_IRI
from shakespeare_tools.oxigraph_load import OxigraphLoader


def test_loader_clear_then_store_order(tmp_path: Path) -> None:
    calls: list[tuple[str, str]] = []

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResp:
            ctype = ""
            h = kwargs.get("headers")
            if isinstance(h, dict):
                ctype = str(h.get("Content-Type", ""))
            calls.append((url, ctype))
            return FakeResp()

    ont = tmp_path / "tbox.ttl"
    ont.write_bytes(b"<http://example.org/s> <http://example.org/p> <http://example.org/o> .")
    abox = tmp_path / "abox.ttl"
    abox.write_bytes(b"<http://example.org/a> <http://example.org/b> <http://example.org/c> .")

    loader = OxigraphLoader("http://oxi.test")
    client = FakeClient()
    loader.load_graph_file(client, ONTOLOGY_GRAPH_IRI, ont, clear=True)
    loader.load_graph_file(client, INSTANCE_GRAPH_IRI, abox, clear=True)

    assert len(calls) == 4
    assert "/update" in calls[0][0]
    assert calls[0][1] == "application/sparql-update"
    assert "/store?graph=" in calls[1][0]
    assert calls[1][1] == "text/turtle"
    assert "/update" in calls[2][0]
    assert "/store?graph=" in calls[3][0]


def test_loader_skip_clear_no_update(tmp_path: Path) -> None:
    urls: list[str] = []

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResp:
            urls.append(url)
            return FakeResp()

    ont = tmp_path / "tbox.ttl"
    ont.write_bytes(b"<http://x/s> <http://x/p> <http://x/o> .")

    loader = OxigraphLoader("http://oxi.test")
    client = FakeClient()
    loader.load_graph_file(client, ONTOLOGY_GRAPH_IRI, ont, clear=False)

    assert len(urls) == 1
    assert "/store?" in urls[0]
    assert "/update" not in urls[0]


def test_post_turtle_skips_empty_body() -> None:
    class FakeResp:
        def raise_for_status(self) -> None:
            return None

    mock_client = MagicMock()
    mock_client.post.return_value = FakeResp()

    loader = OxigraphLoader("http://oxi.test")
    loader.post_turtle(mock_client, INSTANCE_GRAPH_IRI, b"  \n  ")
    mock_client.post.assert_not_called()


def test_build_hamlet_seed_contains_hamlet() -> None:
    from shakespeare_tools.hamlet_seed import build_hamlet_seed_turtle
    from shakespeare_tools.oxigraph_load import resolve_repo_root

    ttl = build_hamlet_seed_turtle(resolve_repo_root())
    low = ttl.lower()
    assert "hamlet" in low
    assert "work" in low or "information" in low
