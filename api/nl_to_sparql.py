"""
Natural language → SPARQL (Phase 2).

Schema-aware translation with few-shot examples from this repository's LinkML output.
Validate generated SPARQL before execution; never invent bindings not returned by Oxigraph.
See AGENTS.md and docs/VISION.md.
"""

from __future__ import annotations


def nl_to_sparql(_question: str) -> str:
    raise NotImplementedError("Phase 2: implement LLM-backed translation with validation.")


def narrate_results(_sparql_results: object, _question: str) -> str:
    raise NotImplementedError("Phase 2: narrate only SPARQL result rows.")
