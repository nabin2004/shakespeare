"""Pydantic models for curation drafts, review, and agent I/O."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

# --- Preparation (spaCy or fallback) ---


class SentenceSpan(BaseModel):
    span_id: str
    text: str
    char_start: int
    char_end: int
    act: int | None = None
    scene: int | None = None
    line_anchor: str | None = None
    item_kind: Literal["line", "stage_direction", "opening_stage_direction"] | None = None
    speaker: str | None = None


class PreparedPassage(BaseModel):
    passage_id: str
    source_path: str
    tei_xpath: str | None = None
    text: str
    char_start: int = 0
    char_end: int
    sentences: list[SentenceSpan] = Field(default_factory=list)


# --- Task pack (YAML) ---


class KnownEntity(BaseModel):
    id: str
    label: str
    type: str


class TaskPack(BaseModel):
    work_id: str
    work_slug: str
    instructions: str = ""
    known_entities: list[KnownEntity] = Field(default_factory=list)


# --- Extraction / alignment / judge ---


class ExtractedEvent(BaseModel):
    candidate_id: str
    label: str
    motif_type: str | None = None
    evidence_span_id: str
    participant_mentions: list[str] = Field(default_factory=list)


class ExtractorOutput(BaseModel):
    events: list[ExtractedEvent] = Field(default_factory=list)


class AlignedEntity(BaseModel):
    mention: str
    resolved_id: str | None = None
    resolution_confidence: float = 0.0
    source: Literal["known_entity", "ontology_index", "unresolved"] = "unresolved"


class JudgeRow(BaseModel):
    candidate_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class JudgeBundle(BaseModel):
    rows: list[JudgeRow] = Field(default_factory=list)


class HumanDecisionStatus(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    NEEDS_EDIT = "needs_edit"


class HumanDecision(BaseModel):
    candidate_id: str
    status: HumanDecisionStatus
    comment: str = ""


class EntityOverride(BaseModel):
    mention: str
    resolved_id: str
    note: str = ""


class ReviewBlock(BaseModel):
    reviewer: str | None = None
    human_decisions: list[HumanDecision] = Field(default_factory=list)
    entity_overrides: list[EntityOverride] = Field(default_factory=list)


# --- Approved instance-shaped rows (LinkML-aligned uriorcurie ids) ---


class ApprovedDramaticEvent(BaseModel):
    """Instance data compatible with DramaticEvent slot shape."""

    id: str
    label: str
    motif_type: str | None = None
    in_work: str
    p11_had_participant: list[str] = Field(default_factory=list)
    evidence_span_id: str
    candidate_id: str
    dramatic_act: int | None = None
    dramatic_scene: int | None = None
    line_anchor: str | None = None
    speaker_label: str | None = None
    evidence_text: str | None = None


class CurationDraftBundle(BaseModel):
    version: Literal[1] = 1
    task_pack: TaskPack
    passages: list[PreparedPassage]
    extraction: ExtractorOutput
    aligned_entities: list[AlignedEntity] = Field(default_factory=list)
    judge: JudgeBundle = Field(default_factory=JudgeBundle)
    review: ReviewBlock = Field(default_factory=ReviewBlock)
    approved_events: list[ApprovedDramaticEvent] = Field(default_factory=list)


def draft_from_json(data: dict[str, object]) -> CurationDraftBundle:
    return CurationDraftBundle.model_validate(data)
