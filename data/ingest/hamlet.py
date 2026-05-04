"""
Hamlet sample ingest — Phase 0.

Builds instance Turtle from LinkML example YAMLs and loads ontology + instances
into Oxigraph (same defaults as ``shakespeare-oxigraph-load``).

Usage (repository root):

  uv run python data/ingest/hamlet.py

Options match ``shakespeare-oxigraph-load`` (e.g. ``--skip-clear``, ``--no-build-seed``).
"""

from __future__ import annotations

import sys

from shakespeare_tools.oxigraph_load import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
