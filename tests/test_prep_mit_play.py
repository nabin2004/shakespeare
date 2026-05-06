"""Tests for MIT Folger-style play JSON → curation passages."""

from __future__ import annotations

import json
from pathlib import Path

from shakespeare_tools.curation.emit import emit_turtle_flat
from shakespeare_tools.curation.models import (
    ApprovedDramaticEvent,
    CurationDraftBundle,
    ExtractorOutput,
    HumanDecision,
    HumanDecisionStatus,
    PreparedPassage,
    ReviewBlock,
    SentenceSpan,
    TaskPack,
)
from shakespeare_tools.curation.prep import prepare_path, prepared_passage_from_mit_play
from shakespeare_tools.curation.validation import validate_for_export, validate_task_pack_vs_passages
from shakespeare_tools.mit_html.models import play_from_dict

MINI_PLAY = {
    "kind": "play",
    "slug": "mini-play",
    "title": "Mini",
    "genre": "history",
    "scenes": [
        {
            "act": 1,
            "scene": 1,
            "title": None,
            "source_file": "mini.1.1.html",
            "opening_stage_direction": "Enter KING.",
            "speeches": [
                {
                    "speech_index": 1,
                    "speaker": "KING",
                    "items": [
                        {
                            "kind": "line",
                            "anchor": "1",
                            "act": 1,
                            "scene": 1,
                            "line_num": 1,
                            "text": "Now is the winter of our discontent.",
                        }
                    ],
                }
            ],
        }
    ],
    "issues": [],
}


def test_prepare_path_mit_play_json(tmp_path: Path) -> None:
    path = tmp_path / "play.json"
    path.write_text(json.dumps(MINI_PLAY), encoding="utf-8")
    passages = prepare_path(path)
    assert len(passages) == 1
    sents = passages[0].sentences
    assert sents[0].text == "Enter KING."
    assert sents[0].item_kind == "opening_stage_direction"
    line_spans = [s for s in sents if s.item_kind == "line"]
    assert line_spans[0].text == "Now is the winter of our discontent."
    assert line_spans[0].speaker == "KING"
    assert line_spans[0].line_anchor == "1"
    assert not line_spans[0].text.strip().startswith("{")


def test_play_from_dict_roundtrip() -> None:
    play = play_from_dict(MINI_PLAY)
    assert play.scenes[0].speeches[0].items[0].text.startswith("Now is")


def test_validate_task_pack_mismatch_henry_vs_hamlet() -> None:
    from shakespeare_tools.curation.models import TaskPack as TP

    bundle = CurationDraftBundle(
        task_pack=TP(work_id="sc:hamlet", work_slug="hamlet"),
        passages=[
            PreparedPassage(
                passage_id="passage-1henryiv-deadbeef",
                source_path="/data/1henryiv.json",
                text="x",
                char_end=1,
                sentences=[
                    SentenceSpan(span_id="passage-1henryiv-deadbeef:s0", text="Hi", char_start=0, char_end=2)
                ],
            )
        ],
        extraction=ExtractorOutput(),
    )
    assert validate_task_pack_vs_passages(bundle)


def test_emit_includes_locator_triples() -> None:
    bundle = CurationDraftBundle(
        task_pack=TaskPack(work_id="sc:hamlet", work_slug="hamlet"),
        passages=[
            PreparedPassage(
                passage_id="p1",
                source_path="/x",
                text="line",
                char_end=4,
                sentences=[
                    SentenceSpan(
                        span_id="p1:s0",
                        text="A line",
                        char_start=0,
                        char_end=6,
                        act=2,
                        scene=1,
                        line_anchor="5",
                        speaker="GHOST",
                    )
                ],
            )
        ],
        extraction=ExtractorOutput(),
        review=ReviewBlock(
            human_decisions=[
                HumanDecision(candidate_id="evt-1", status=HumanDecisionStatus.APPROVE),
            ],
        ),
        approved_events=[
            ApprovedDramaticEvent(
                id="sc:evt-hamlet-aaaaaaaaaa",
                label="Ghost speaks",
                in_work="sc:hamlet",
                evidence_span_id="p1:s0",
                candidate_id="evt-1",
                dramatic_act=2,
                dramatic_scene=1,
                line_anchor="5",
                speaker_label="GHOST",
                evidence_text="A line of the ghost.",
            )
        ],
    )
    assert validate_for_export(bundle) == []
    ttl = emit_turtle_flat(bundle)
    assert "dramatic_act" in ttl
    assert "dramatic_scene" in ttl
    assert "line_anchor" in ttl
    assert "speaker_label" in ttl
    assert "dcterms:description" in ttl


def test_prepared_passage_stable_ids(tmp_path: Path) -> None:
    play = play_from_dict(MINI_PLAY)
    pid = "passage-mini-play-abc12345"
    pp = prepared_passage_from_mit_play(play, passage_id=pid, source_path=str(tmp_path / "x.json"))
    assert any(s.span_id.endswith(":sp1i0") for s in pp.sentences)
