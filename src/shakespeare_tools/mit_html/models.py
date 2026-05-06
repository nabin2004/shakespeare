"""Structured parse results (JSON-serializable)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from shakespeare_tools.mit_html.errors import ParseIssue


@dataclass
class TextLine:
    anchor: str | None
    text: str
    act: int | None = None
    scene: int | None = None
    line_num: int | None = None


@dataclass
class StageDirection:
    text: str


@dataclass
class Speech:
    speech_index: int
    speaker: str
    items: list[TextLine | StageDirection] = field(default_factory=list)


@dataclass
class Scene:
    act: int
    scene: int
    title: str | None
    source_file: str | None
    opening_stage_direction: str | None
    speeches: list[Speech] = field(default_factory=list)


@dataclass
class ParsedPlay:
    kind: Literal["play"] = "play"
    slug: str = ""
    title: str = ""
    genre: str | None = None
    scenes: list[Scene] = field(default_factory=list)
    issues: list[ParseIssue] = field(default_factory=list)


@dataclass
class PoemPage:
    kind: Literal["poem"] = "poem"
    slug: str = ""
    title: str = ""
    lines: list[str] = field(default_factory=list)
    source_file: str | None = None
    issues: list[ParseIssue] = field(default_factory=list)


def _issue_dict(i: ParseIssue) -> dict[str, Any]:
    return {
        "severity": i.severity,
        "path": i.path,
        "message": i.message,
        "snippet": i.snippet,
    }


def _line_dict(x: TextLine) -> dict[str, Any]:
    d: dict[str, Any] = {
        "kind": "line",
        "anchor": x.anchor,
        "text": x.text,
    }
    if x.act is not None:
        d["act"] = x.act
    if x.scene is not None:
        d["scene"] = x.scene
    if x.line_num is not None:
        d["line_num"] = x.line_num
    return d


def _block_item_dict(x: TextLine | StageDirection) -> dict[str, Any]:
    if isinstance(x, TextLine):
        return _line_dict(x)
    return {"kind": "stage_direction", "text": x.text}


def _speech_dict(s: Speech) -> dict[str, Any]:
    return {
        "speech_index": s.speech_index,
        "speaker": s.speaker,
        "items": [_block_item_dict(i) for i in s.items],
    }


def _scene_dict(s: Scene) -> dict[str, Any]:
    return {
        "act": s.act,
        "scene": s.scene,
        "title": s.title,
        "source_file": s.source_file,
        "opening_stage_direction": s.opening_stage_direction,
        "speeches": [_speech_dict(sp) for sp in s.speeches],
    }


def play_to_dict(p: ParsedPlay) -> dict[str, Any]:
    return {
        "kind": p.kind,
        "slug": p.slug,
        "title": p.title,
        "genre": p.genre,
        "scenes": [_scene_dict(s) for s in p.scenes],
        "issues": [_issue_dict(i) for i in p.issues],
    }


def _parse_scene(data: dict[str, Any]) -> Scene:
    speeches_raw = data.get("speeches") or []
    speeches: list[Speech] = []
    for sp in speeches_raw:
        items_raw = sp.get("items") or []
        items: list[TextLine | StageDirection] = []
        for it in items_raw:
            kind = it.get("kind") or "line"
            if kind == "stage_direction":
                items.append(StageDirection(text=str(it.get("text") or "")))
            else:
                items.append(
                    TextLine(
                        anchor=it.get("anchor"),
                        text=str(it.get("text") or ""),
                        act=it.get("act"),
                        scene=it.get("scene"),
                        line_num=it.get("line_num"),
                    )
                )
        speeches.append(
            Speech(
                speech_index=int(sp.get("speech_index", 0)),
                speaker=str(sp.get("speaker") or ""),
                items=items,
            )
        )
    return Scene(
        act=int(data["act"]),
        scene=int(data["scene"]),
        title=data.get("title"),
        source_file=data.get("source_file"),
        opening_stage_direction=data.get("opening_stage_direction"),
        speeches=speeches,
    )


def play_from_dict(data: dict[str, Any]) -> ParsedPlay:
    """Rehydrate a :func:`play_to_dict` / pipeline JSON payload into a ParsedPlay."""
    issues: list[ParseIssue] = []
    for raw in data.get("issues") or []:
        rsev = raw.get("severity", "warning")
        sev = rsev if rsev in ("warning", "error") else "warning"
        issues.append(
            ParseIssue(
                severity=sev,
                path=str(raw.get("path", "")),
                message=str(raw.get("message", "")),
                snippet=raw.get("snippet"),
            )
        )
    scenes = [_parse_scene(s) for s in data.get("scenes") or []]
    return ParsedPlay(
        kind="play",
        slug=str(data.get("slug") or ""),
        title=str(data.get("title") or ""),
        genre=data.get("genre"),
        scenes=scenes,
        issues=issues,
    )


def is_play_json_dict(data: dict[str, Any]) -> bool:
    return data.get("kind") == "play" and isinstance(data.get("scenes"), list)


def poem_to_dict(p: PoemPage) -> dict[str, Any]:
    return {
        "kind": p.kind,
        "slug": p.slug,
        "title": p.title,
        "lines": p.lines,
        "source_file": p.source_file,
        "issues": [_issue_dict(i) for i in p.issues],
    }


def dump_json(obj: ParsedPlay | PoemPage, *, indent: int = 2) -> str:
    if isinstance(obj, ParsedPlay):
        payload = play_to_dict(obj)
    else:
        payload = poem_to_dict(obj)
    return json.dumps(payload, indent=indent, sort_keys=True, ensure_ascii=False)
