"""Golden tests for curation prep, mock pipeline, and Turtle emit (no live LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from shakespeare_tools.curation.emit import expand_curie, emit_turtle_flat
from shakespeare_tools.curation.pipeline import run_pipeline
from shakespeare_tools.curation.prep import prepare_path
from shakespeare_tools.curation.review_merge import auto_approve_all
from shakespeare_tools.curation.task_pack import load_task_pack
from shakespeare_tools.curation.validation import validate_for_export

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_PACK = REPO_ROOT / "src/shakespeare_tools/curation/examples/hamlet_task_pack.yaml"


def test_expand_curie_sc() -> None:
    assert expand_curie("sc:hamlet") == "https://w3id.org/shakespeare-crm/hamlet"


def test_prepare_fallback_sentences(tmp_path: Path) -> None:
    p = tmp_path / "lines.txt"
    p.write_text("Hamlet sees the ghost. The ramparts are cold.", encoding="utf-8")
    passages = prepare_path(p, prefer_spacy=False)
    assert len(passages) == 1
    assert passages[0].sentences, "expected at least one sentence span"
    assert passages[0].sentences[0].span_id


def test_mock_pipeline_mock_emit(tmp_path: Path) -> None:
    p = tmp_path / "ghost.txt"
    p.write_text("Hamlet sees the ghost of his father.", encoding="utf-8")
    passages = prepare_path(p, prefer_spacy=False)
    pack = load_task_pack(TASK_PACK)
    draft = run_pipeline(passages, pack, use_mock_llm=True)
    assert draft.extraction.events, "mock extractor should emit ≥1 event for ghost motif"
    approved_bundle = auto_approve_all(draft)
    errs = validate_for_export(approved_bundle)
    assert not errs, errs
    ttl = emit_turtle_flat(approved_bundle)
    g = Graph()
    g.parse(data=ttl, format="turtle")
    dramatic = URIRef("https://w3id.org/shakespeare-crm/DramaticEvent")
    types = set(g.objects(None, RDF.type))
    assert dramatic in types


@pytest.mark.skipif(
    not (REPO_ROOT / "ontology" / "shakespeare_crm.ttl").is_file(),
    reason="ontology/shakespeare_crm.ttl not generated locally",
)
def test_ontology_index_labels() -> None:
    from shakespeare_tools.curation.ontology_index import OntologyIndex

    idx = OntologyIndex.from_path_auto(REPO_ROOT / "ontology" / "shakespeare_crm.ttl")
    uri, score = idx.best_class_match("DramaticEvent")
    assert uri and score >= 0.75
