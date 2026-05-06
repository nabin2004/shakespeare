"""Draft validation before Turtle export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from shakespeare_tools.curation.models import (
    CurationDraftBundle,
    HumanDecisionStatus,
)

try:
    import jsonschema  # type: ignore[import-untyped]
except ImportError:
    jsonschema = None


def _looks_like_json_shred(text: str) -> bool:
    """True if text looks like JSON or Folger/MIT structure leaked into a string field."""
    t = text.strip()
    if not t:
        return False
    if t.startswith("{"):
        return True
    if '"act":' in t:
        return True
    if '"anchor"' in t and '"scene":' in t:
        return True
    return False


def validate_task_pack_vs_passages(bundle: CurationDraftBundle) -> list[str]:
    """Catch common mistakes (e.g. Hamlet task pack with Henry IV passages)."""
    errs: list[str] = []
    slug = bundle.task_pack.work_slug.lower()
    wid = bundle.task_pack.work_id.lower()
    for p in bundle.passages:
        blob = f"{p.passage_id} {p.source_path}".lower()
        henry = "1henryiv" in blob or "henryiv" in blob or "henry_iv" in blob
        if henry and (slug == "hamlet" or "hamlet" in wid):
            errs.append(
                "Task pack points at Hamlet, but passages reference Henry IV (1henryiv); "
                "fix work_id/work_slug (see curation/examples/1henryiv_task_pack.yaml)."
            )
            return errs
    return errs


def collect_span_ids(bundle: CurationDraftBundle) -> set[str]:
    return {s.span_id for p in bundle.passages for s in p.sentences}


def validate_for_export(bundle: CurationDraftBundle) -> list[str]:
    """Return errors; empty means OK to export."""
    errs: list[str] = []
    errs.extend(validate_task_pack_vs_passages(bundle))
    if not bundle.approved_events:
        return errs or [
            "No approved_events to export — run apply-review with approve decisions.",
        ]
    spans = collect_span_ids(bundle)
    decisions = {d.candidate_id: d.status for d in bundle.review.human_decisions}
    for ev in bundle.approved_events:
        if ev.evidence_span_id not in spans:
            errs.append(f"Unknown evidence_span_id on approved event: {ev.evidence_span_id!r}")
        if decisions.get(ev.candidate_id) != HumanDecisionStatus.APPROVE:
            errs.append(f"Candidate {ev.candidate_id!r} is not approved in review.human_decisions.")
        if _looks_like_json_shred(ev.label):
            errs.append(
                f"Approved event {ev.candidate_id!r} has a corrupt label (JSON-like); "
                "rebuild passages with MIT play JSON prep or re-run extraction."
            )
        if ev.evidence_text and _looks_like_json_shred(ev.evidence_text):
            errs.append(
                f"Approved event {ev.candidate_id!r} has corrupt evidence_text; rebuild draft from clean spans."
            )
    return errs


def validate_instance_against_json_schema(
    instance: dict[str, Any],
    schema_path: Path,
    *,
    root_def: str = "DramaticEvent",
) -> None:
    """Validate one object against $defs[root_def] in a LinkML gen-json-schema file."""
    if jsonschema is None:
        raise RuntimeError("jsonschema is required for schema file validation")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    defs = schema.get("$defs", {})
    if root_def not in defs:
        raise KeyError(f"JSON Schema missing $defs.{root_def} in {schema_path}")
    jsonschema.validate(instance, defs[root_def])


def load_draft_json(path: Path) -> CurationDraftBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    return CurationDraftBundle.model_validate(cast(dict[str, Any], data))


def write_draft_json(bundle: CurationDraftBundle, path: Path) -> None:
    path.write_text(
        json.dumps(bundle.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
