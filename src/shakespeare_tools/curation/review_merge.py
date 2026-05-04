"""Apply human review to drafts and build approved instance rows."""

from __future__ import annotations

import hashlib

from shakespeare_tools.curation.models import (
    ApprovedDramaticEvent,
    CurationDraftBundle,
    HumanDecision,
    HumanDecisionStatus,
)


def _mention_resolver(bundle: CurationDraftBundle) -> dict[str, str]:
    """Lowercased mention -> resolved curie/IRI."""
    out: dict[str, str] = {}
    for a in bundle.aligned_entities:
        if a.resolved_id:
            out[a.mention.strip().lower()] = a.resolved_id
    for o in bundle.review.entity_overrides:
        out[o.mention.strip().lower()] = o.resolved_id
    return out


def mint_event_id(work_slug: str, candidate_id: str) -> str:
    h = hashlib.sha256(f"{work_slug}:{candidate_id}".encode()).hexdigest()[:10]
    return f"sc:evt-{work_slug}-{h}"


def apply_review(bundle: CurationDraftBundle) -> CurationDraftBundle:
    """Return a copy of bundle with approved_events populated from approved human decisions."""
    data = bundle.model_dump(mode="json")
    out = CurationDraftBundle.model_validate(data)
    resolve = _mention_resolver(out)
    approved: list[ApprovedDramaticEvent] = []
    decisions = {d.candidate_id: d for d in out.review.human_decisions}
    for e in out.extraction.events:
        dec = decisions.get(e.candidate_id)
        if not dec or dec.status != HumanDecisionStatus.APPROVE:
            continue
        parts: list[str] = []
        for m in e.participant_mentions:
            rid = resolve.get(m.strip().lower())
            if rid:
                parts.append(rid)
        eid = mint_event_id(out.task_pack.work_slug, e.candidate_id)
        approved.append(
            ApprovedDramaticEvent(
                id=eid,
                label=e.label,
                motif_type=e.motif_type,
                in_work=out.task_pack.work_id,
                p11_had_participant=parts,
                evidence_span_id=e.evidence_span_id,
                candidate_id=e.candidate_id,
            )
        )
    out.approved_events = approved
    return out


def auto_approve_all(bundle: CurationDraftBundle) -> CurationDraftBundle:
    """Mark every candidate as approved (developer convenience; not for production HIL)."""
    b = bundle.model_copy(deep=True)
    b.review.human_decisions = [
        HumanDecision(candidate_id=e.candidate_id, status=HumanDecisionStatus.APPROVE, comment="auto")
        for e in b.extraction.events
    ]
    return apply_review(b)
