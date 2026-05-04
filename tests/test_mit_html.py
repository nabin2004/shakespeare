"""Golden tests for MIT/Moby HTML parsing (local clone under data/raw/shakespeare)."""

from __future__ import annotations

from pathlib import Path

import pytest

from shakespeare_tools.mit_html.models import TextLine
from shakespeare_tools.mit_html.plays import parse_full_play, parse_scene_html
from shakespeare_tools.mit_html.poetry import parse_poem_html

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "data" / "raw" / "shakespeare"


@pytest.mark.skipif(not (CORPUS / "hamlet").is_dir(), reason="MIT corpus not present")
def test_hamlet_scene_1_1_opening_and_lines() -> None:
    path = CORPUS / "hamlet" / "hamlet.1.1.html"
    sc = parse_scene_html(path)
    assert sc is not None
    assert sc.act == 1 and sc.scene == 1
    assert sc.opening_stage_direction is not None
    assert "BERNARDO" in sc.opening_stage_direction
    assert sc.speeches[0].speaker == "BERNARDO"
    first_line = sc.speeches[0].items[0]
    assert first_line.anchor == "1"
    assert first_line.text == "Who's there?"
    assert sc.speeches[1].speaker == "FRANCISCO"
    assert sc.speeches[1].items[0].text == "Nay, answer me: stand, and unfold yourself."


@pytest.mark.skipif(not (CORPUS / "hamlet" / "full.html").is_file(), reason="full.html missing")
def test_hamlet_full_compound_line_anchor() -> None:
    path = CORPUS / "hamlet" / "full.html"
    play = parse_full_play(path)
    assert play.scenes, "expected scenes from full.html"
    first = play.scenes[0]
    assert first.act == 1 and first.scene == 1
    line0 = first.speeches[0].items[0]
    assert line0.anchor == "1.1.1"
    assert line0.act == 1 and line0.scene == 1 and line0.line_num == 1
    assert line0.text == "Who's there?"


@pytest.mark.skipif(not (CORPUS / "hamlet" / "hamlet.1.2.html").is_file(), reason="scene missing")
def test_hamlet_shared_blockquote_two_speakers() -> None:
    path = CORPUS / "hamlet" / "hamlet.1.2.html"
    sc = parse_scene_html(path)
    assert sc is not None
    duty = "In that and all things will we show our duty."
    s2 = next(s for s in sc.speeches if s.speech_index == 2)
    s3 = next(s for s in sc.speeches if s.speech_index == 3)
    assert s2.speaker == "CORNELIUS" and s3.speaker == "VOLTIMAND"
    assert any(isinstance(i, TextLine) and i.text == duty for i in s2.items)
    assert any(isinstance(i, TextLine) and i.text == duty for i in s3.items)


@pytest.mark.skipif(not (CORPUS / "Poetry" / "sonnet.I.html").is_file(), reason="sonnet.I.html missing")
def test_sonnet_I_first_line() -> None:
    path = CORPUS / "Poetry" / "sonnet.I.html"
    poem = parse_poem_html(path)
    assert poem.lines
    assert poem.lines[0] == "FROM fairest creatures we desire increase,"
