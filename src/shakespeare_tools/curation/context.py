"""Execution context and dependencies for curation agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from shakespeare_tools.curation.models import PreparedPassage, TaskPack
from shakespeare_tools.curation.ontology_index import OntologyIndex
from shakespeare_tools.curation.sparql_client import SparqlClient


@dataclass
class CurationContext:
    """Cross-stage memory: stable anchors for provenance and prompts."""

    run_id: str
    passages: list[PreparedPassage]
    notes: list[str] = field(default_factory=list)


@dataclass
class CurationDeps:
    """Injected into Pydantic AI agents and tools."""

    context: CurationContext
    task_pack: TaskPack
    ontology_index: OntologyIndex | None
    sparql: SparqlClient | None
    use_mock_llm: bool
    llm_model: str | None = None
