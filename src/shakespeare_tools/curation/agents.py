"""Pydantic AI agents: extractor and judge (STRUCTSENSE-style roles)."""

from __future__ import annotations

import os
import uuid
from textwrap import dedent

from pydantic_ai import Agent

from shakespeare_tools.curation.context import CurationDeps
from shakespeare_tools.curation.models import (
    ExtractorOutput,
    ExtractedEvent,
    JudgeBundle,
    JudgeRow,
)


def _build_prompt_payload(deps: CurationDeps) -> str:
    ke_lines = []
    for ke in deps.task_pack.known_entities:
        ke_lines.append(f"- {ke.label} -> {ke.id} ({ke.type})")
    known = "\n".join(ke_lines) if ke_lines else "(none)"
    lines: list[str] = [f"Known entities (from task pack):\n{known}\n"]
    for p in deps.context.passages:
        lines.append(f"## passage_id={p.passage_id}\n{p.text}\n")
        for s in p.sentences:
            lines.append(f"- span_id={s.span_id!r}: {s.text}\n")
    return "".join(lines)


def mock_extract(deps: CurationDeps) -> ExtractorOutput:
    """Deterministic stub for CI / offline runs."""
    events: list[ExtractedEvent] = []
    for passage in deps.context.passages:
        for sent in passage.sentences:
            low = sent.text.lower()
            motif = None
            if "ghost" in low:
                motif = "supernatural"
            elif "murder" in low or "kill" in low or "death" in low:
                motif = "violence"
            elif "love" in low:
                motif = "love"
            if motif:
                mentions: list[str] = []
                if "hamlet" in low:
                    mentions.append("Hamlet")
                events.append(
                    ExtractedEvent(
                        candidate_id=f"evt-{uuid.uuid4().hex[:10]}",
                        label=sent.text[:120],
                        motif_type=motif,
                        evidence_span_id=sent.span_id,
                        participant_mentions=mentions,
                    )
                )
    if not events and deps.context.passages:
        s0 = deps.context.passages[0].sentences[0] if deps.context.passages[0].sentences else None
        text = s0.text if s0 else deps.context.passages[0].text[:200]
        sid = s0.span_id if s0 else f"{deps.context.passages[0].passage_id}:s0"
        events.append(
            ExtractedEvent(
                candidate_id=f"evt-{uuid.uuid4().hex[:10]}",
                label=text,
                motif_type="scene",
                evidence_span_id=sid,
                participant_mentions=(["Hamlet"] if "hamlet" in text.lower() else []),
            )
        )
    return ExtractorOutput(events=events)


def mock_judge(extraction: ExtractorOutput) -> JudgeBundle:
    return JudgeBundle(
        rows=[
            JudgeRow(candidate_id=e.candidate_id, confidence=0.85, rationale="mock judge")
            for e in extraction.events
        ]
    )


def build_extractor_agent(model: str | None) -> Agent[CurationDeps, ExtractorOutput]:
    sys = dedent(
        """
        You extract DramaticEvent candidates for ShakespeareCRM.
        Output JSON matching the schema: list of events with candidate_id, label, motif_type,
        evidence_span_id (must match an input span_id exactly), participant_mentions (strings).
        Only use span_ids present in the user message. Invent stable candidate_id strings prefixed with 'evt-'.
        """
    ).strip()
    m = model or os.environ.get("CURATION_LLM_MODEL", "openai:gpt-4o-mini")
    return Agent(
        model=m,
        deps_type=CurationDeps,
        output_type=ExtractorOutput,
        system_prompt=sys,
        tools=[],
    )


def build_judge_agent(model: str | None) -> Agent[CurationDeps, JudgeBundle]:
    sys = dedent(
        """
        You judge extraction candidates. For each candidate_id, output confidence 0.0-1.0
        and a short rationale. Penalize motifs that do not fit the evidence sentence.
        """
    ).strip()
    m = model or os.environ.get("CURATION_LLM_MODEL", "openai:gpt-4o-mini")
    return Agent(
        model=m,
        deps_type=CurationDeps,
        output_type=JudgeBundle,
        system_prompt=sys,
        tools=[],
    )


def run_extractor(deps: CurationDeps) -> ExtractorOutput:
    if deps.use_mock_llm:
        return mock_extract(deps)
    agent = build_extractor_agent(deps.llm_model)
    user = _build_prompt_payload(deps)
    result = agent.run_sync(user, deps=deps)
    return result.output


def run_judge(deps: CurationDeps, extraction: ExtractorOutput) -> JudgeBundle:
    if deps.use_mock_llm:
        return mock_judge(extraction)
    agent = build_judge_agent(deps.llm_model)
    lines = [e.model_dump_json() for e in extraction.events]
    user = "Candidates:\n" + "\n".join(lines)
    result = agent.run_sync(user, deps=deps)
    return result.output
