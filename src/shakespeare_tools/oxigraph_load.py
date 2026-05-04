"""Load ontology + instance Turtle into Oxigraph via SPARQL Update and Graph Store HTTP API."""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path
from urllib.parse import quote

import httpx

from shakespeare_tools.curation.graph_constants import INSTANCE_GRAPH_IRI, ONTOLOGY_GRAPH_IRI
from shakespeare_tools.hamlet_seed import build_hamlet_seed_file


def resolve_repo_root() -> Path:
    """Resolve checkout root (works when CWD is inside the repo; falls back to editable layout)."""
    cwd = Path.cwd()
    for d in (cwd, *cwd.parents):
        pp = d / "pyproject.toml"
        if not pp.is_file():
            continue
        try:
            meta = tomllib.loads(pp.read_text(encoding="utf-8"))
            if meta.get("project", {}).get("name") == "shakespeare-tools":
                return d
        except OSError:
            continue
    here = Path(__file__).resolve()
    return here.parents[2]


class OxigraphLoader:
    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def clear_graph(self, client: httpx.Client, graph_iri: str) -> None:
        body = f"CLEAR GRAPH <{graph_iri}>"
        r = client.post(
            f"{self.base_url}/update",
            content=body.encode("utf-8"),
            headers={"Content-Type": "application/sparql-update"},
            timeout=self.timeout,
        )
        r.raise_for_status()

    def post_turtle(self, client: httpx.Client, graph_iri: str, turtle: bytes) -> None:
        if not turtle.strip():
            return
        url = f"{self.base_url}/store?graph={quote(graph_iri, safe='')}"
        r = client.post(
            url,
            content=turtle,
            headers={"Content-Type": "text/turtle"},
            timeout=self.timeout,
        )
        r.raise_for_status()

    def load_graph_file(
        self,
        client: httpx.Client,
        graph_iri: str,
        path: Path,
        *,
        clear: bool = True,
    ) -> None:
        raw = path.read_bytes()
        if clear:
            self.clear_graph(client, graph_iri)
        self.post_turtle(client, graph_iri, raw)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shakespeare-oxigraph-load",
        description="Load ShakespeareCRM ontology and Hamlet seed instances into Oxigraph.",
    )
    p.add_argument(
        "--base-url",
        default=os.environ.get("OXIGRAPH_URL", "http://localhost:7878"),
        help="Oxigraph base URL (default: env OXIGRAPH_URL or http://localhost:7878)",
    )
    p.add_argument(
        "--skip-clear",
        action="store_true",
        help="Do not CLEAR GRAPH before POST (additive; may duplicate on re-run).",
    )
    p.add_argument(
        "--ontology",
        type=Path,
        default=None,
        help="Path to TBox Turtle",
    )
    p.add_argument(
        "--instances",
        type=Path,
        default=None,
        help="Path to ABox Turtle (written when seed is built)",
    )
    p.add_argument(
        "--no-build-seed",
        action="store_true",
        help="Skip LinkML merge step; --instances file must already exist.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = resolve_repo_root()
    ontology_path: Path = args.ontology or (root / "ontology" / "shakespeare_crm.ttl")
    instances_path: Path = args.instances or (root / "data" / "triples" / "hamlet_seed.ttl")
    loader = OxigraphLoader(args.base_url)

    if not args.no_build_seed:
        instances_path.parent.mkdir(parents=True, exist_ok=True)
        build_hamlet_seed_file(root, instances_path)

    if not ontology_path.is_file():
        print(
            f"Ontology not found: {ontology_path}\nRun: uv run generate-ontology",
            file=sys.stderr,
        )
        return 1
    if not instances_path.is_file():
        print(f"Instances not found: {instances_path}", file=sys.stderr)
        return 1

    clear = not args.skip_clear
    try:
        with httpx.Client() as client:
            loader.load_graph_file(client, ONTOLOGY_GRAPH_IRI, ontology_path, clear=clear)
            loader.load_graph_file(client, INSTANCE_GRAPH_IRI, instances_path, clear=clear)
    except httpx.HTTPError as e:
        print(f"HTTP error talking to Oxigraph: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
