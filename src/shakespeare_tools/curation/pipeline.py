"""Orchestrate extract → align → judge into a curation draft bundle."""

from __future__ import annotations

import uuid
from collections.abc import Iterable

from shakespeare_tools.curation.agents import run_extractor, run_judge
from shakespeare_tools.curation.context import CurationContext, CurationDeps
from shakespeare_tools.curation.models import (
    AlignedEntity,
    CurationDraftBundle,
    ExtractedEvent,
    HumanDecision,
    HumanDecisionStatus,
    ReviewBlock,
    TaskPack,
)
from shakespeare_tools.curation.ontology_index import OntologyIndex
from shakespeare_tools.curation.prep import PreparedPassage
from shakespeare_tools.curation.sparql_client import SparqlClient


def _known_map(task_pack: TaskPack) -> dict[str, str]:
    return {ke.label.strip().lower(): ke.id for ke in task_pack.known_entities}


def align_mentions(
    mentions: Iterable[str],
    task_pack: TaskPack,
    index: OntologyIndex | None,
) -> list[AlignedEntity]:
    known = _known_map(task_pack)
    out: list[AlignedEntity] = []
    for raw in mentions:
        m = raw.strip()
        key = m.lower()
        if key in known:
            out.append(
                AlignedEntity(
                    mention=m,
                    resolved_id=known[key],
                    resolution_confidence=1.0,
                    source="known_entity",
                )
            )
            continue
        if index is not None:
            uri, score = index.best_class_match(m)
            if uri and score >= 0.75:
                out.append(
                    AlignedEntity(
                        mention=m,
                        resolved_id=uri,
                        resolution_confidence=score,
                        source="ontology_index",
                    )
                )
                continue
        out.append(AlignedEntity(mention=m))
    return out


def align_events(
    events: list[ExtractedEvent],
    task_pack: TaskPack,
    index: OntologyIndex | None,
) -> list[AlignedEntity]:
    seen: dict[str, AlignedEntity] = {}
    for e in events:
        for row in align_mentions(e.participant_mentions, task_pack, index):
            seen[row.mention] = row
    return list(seen.values())


def run_pipeline(
    passages: list[PreparedPassage],
    task_pack: TaskPack,
    *,
    ontology_index: OntologyIndex | None = None,
    sparql: SparqlClient | None = None,
    use_mock_llm: bool = False,
    llm_model: str | None = None,
    run_id: str | None = None,
) -> CurationDraftBundle:
    rid = run_id or f"run-{uuid.uuid4().hex[:12]}"
    ctx = CurationContext(run_id=rid, passages=passages)
    deps = CurationDeps(
        context=ctx,
        task_pack=task_pack,
        ontology_index=ontology_index,
        sparql=sparql,
        use_mock_llm=use_mock_llm,
        llm_model=llm_model,
    )
    extraction = run_extractor(deps)
    aligned = align_events(extraction.events, task_pack, ontology_index)
    judge = run_judge(deps, extraction)
    review = ReviewBlock(
        human_decisions=[
            HumanDecision(
                candidate_id=e.candidate_id,
                status=HumanDecisionStatus.NEEDS_EDIT,
                comment="pending review",
            )
            for e in extraction.events
        ]
    )
    return CurationDraftBundle(
        task_pack=task_pack,
        passages=passages,
        extraction=extraction,
        aligned_entities=aligned,
        judge=judge,
        review=review,
    )

