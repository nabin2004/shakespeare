"""MIT play HTML: per-scene files and full.html."""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag

from shakespeare_tools.mit_html.clean import clean_text
from shakespeare_tools.mit_html.encoding import read_html_text
from shakespeare_tools.mit_html.errors import ParseIssue
from shakespeare_tools.mit_html.models import ParsedPlay, Scene, Speech, StageDirection, TextLine

_SPEECH_RE = re.compile(r"^speech(\d+)$", re.IGNORECASE)
_LINE_COMPOUND = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_LINE_NUMERIC = re.compile(r"^(\d+)$")
_SCENE_FILE_RE = re.compile(r"^(.+)\.(\d+)\.(\d+)\.html$")
_ACT_HEAD = re.compile(r"^ACT\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
_SCENE_HEAD = re.compile(r"^SCENE\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)

_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _roman_to_int(s: str) -> int | None:
    s = s.upper().strip()
    if not s:
        return None
    if set(s) - set(_ROMAN_VALUES):
        return None
    total = 0
    i = 0
    while i < len(s):
        if i + 1 < len(s) and _ROMAN_VALUES[s[i]] < _ROMAN_VALUES[s[i + 1]]:
            total -= _ROMAN_VALUES[s[i]]
        else:
            total += _ROMAN_VALUES[s[i]]
        i += 1
    return total if total > 0 else None


def _act_scene_token(tok: str) -> int | None:
    tok = tok.strip()
    if tok.isdigit():
        return int(tok)
    return _roman_to_int(tok)


def _strip_header_tables(soup: BeautifulSoup) -> None:
    body = soup.body
    if not body:
        return
    for table in body.find_all("table", recursive=False):
        bg = (table.get("bgcolor") or table.get("BGCOLOR") or "").upper()
        cls = (table.get("class") or []) if isinstance(table.get("class"), list) else []
        if "CCF6F6" in bg.replace("#", "") or "play" in cls or table.find("td", class_="play"):
            table.decompose()
            return


def _is_speech_anchor(tag: Tag) -> bool:
    if tag.name not in ("a", "A"):
        return False
    n = tag.get("name")
    if not n:
        return False
    return bool(_SPEECH_RE.match(str(n)))


def _speech_index(tag: Tag) -> int:
    n = str(tag.get("name"))
    m = _SPEECH_RE.match(n)
    assert m
    return int(m.group(1))


def _parse_line_anchor(
    raw: str,
    *,
    fallback_act: int | None,
    fallback_scene: int | None,
    compound: bool,
) -> tuple[str | None, int | None, int | None, int | None]:
    name = raw.strip()
    if compound:
        m = _LINE_COMPOUND.match(name)
        if m:
            return name, int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = _LINE_NUMERIC.match(name)
        if m:
            num = int(m.group(1))
            return name, fallback_act, fallback_scene, num
    return name, None, None, None  # caller may warn


def _speaker_from_anchor(tag: Tag) -> tuple[str, list[ParseIssue]]:
    issues: list[ParseIssue] = []
    b = tag.find(["b", "B"])
    if not b:
        issues.append(
            ParseIssue("warning", "", "speech anchor missing <b> speaker", str(tag.get("name")))
        )
        return "", issues
    return clean_text(b.get_text()), issues


def _is_opening_blockquote(bq: Tag) -> bool:
    if bq.find(_line_anchor_predicate):
        return False
    return bool(bq.find(["i", "I"]))


def _line_anchor_predicate(tag: Tag) -> bool:
    if tag.name not in ("a", "A"):
        return False
    n = tag.get("name")
    if not n or _SPEECH_RE.match(str(n)):
        return False
    return bool(_LINE_NUMERIC.match(str(n).strip()) or _LINE_COMPOUND.match(str(n).strip()))


def _flatten_blockquote_items(
    bq: Tag,
    *,
    path: str,
    issues: list[ParseIssue],
    fallback_act: int | None,
    fallback_scene: int | None,
    compound_lines: bool,
) -> list[TextLine | StageDirection]:
    out: list[TextLine | StageDirection] = []

    def handle_a(a: Tag) -> None:
        nm = str(a.get("name", "")).strip()
        if _SPEECH_RE.match(nm):
            issues.append(ParseIssue("warning", path, "nested speech anchor inside blockquote", nm))
            return
        anchor, act, scene, line_no = _parse_line_anchor(
            nm,
            fallback_act=fallback_act,
            fallback_scene=fallback_scene,
            compound=compound_lines,
        )
        if act is None and scene is None and line_no is None and anchor:
            issues.append(ParseIssue("warning", path, "unrecognized line anchor", nm))
        text = clean_text(a.get_text())
        if text:
            out.append(
                TextLine(
                    anchor=anchor,
                    text=text,
                    act=act,
                    scene=scene,
                    line_num=line_no,
                )
            )

    def walk(node: Tag) -> None:
        for child in node.children:
            if isinstance(child, NavigableString):
                continue
            if not isinstance(child, Tag):
                continue
            name = child.name.lower() if child.name else ""
            if name == "a":
                handle_a(child)
            elif name == "i":
                t = clean_text(child.get_text())
                if t:
                    out.append(StageDirection(text=t))
            elif name == "p":
                walk(child)
            elif name == "blockquote":
                walk(child)
            elif name == "table":
                bg = str(child.get("bgcolor") or "").upper()
                if "CCF6F6" in bg.replace("#", ""):
                    continue
                walk(child)
            elif name == "br":
                continue
            elif name in ("font", "span", "em", "strong"):
                walk(child)
            else:
                if child.get_text(strip=True):
                    issues.append(
                        ParseIssue(
                            "warning",
                            path,
                            f"unexpected tag in blockquote: {name}",
                            None,
                        )
                    )

    walk(bq)
    return out


def _following_blockquote(speech_tag: Tag) -> Tag | None:
    sib = speech_tag.next_sibling
    while sib is not None:
        if isinstance(sib, NavigableString):
            if str(sib).strip():
                pass
            sib = sib.next_sibling
            continue
        if isinstance(sib, Tag):
            if sib.name and sib.name.lower() == "blockquote":
                return sib
            return None
        sib = getattr(sib, "next_sibling", None)
    return None


def _blockquote_for_speech(speech_tag: Tag) -> Tag | None:
    """Return the blockquote for this speech, including shared replies (several <a name=speechN> before one blockquote)."""
    bq = _following_blockquote(speech_tag)
    if bq is not None:
        return bq
    sib = speech_tag.next_sibling
    while sib is not None:
        if isinstance(sib, NavigableString):
            sib = sib.next_sibling
            continue
        if not isinstance(sib, Tag):
            sib = getattr(sib, "next_sibling", None)
            continue
        name = (sib.name or "").lower()
        if name == "blockquote":
            return sib
        if name == "a" and _is_speech_anchor(sib):
            sib = sib.next_sibling
            continue
        if name in ("p", "span", "font") and not sib.get_text(strip=True):
            sib = sib.next_sibling
            continue
        return None
    return None


def _parse_speech(
    speech_tag: Tag,
    *,
    path: str,
    issues: list[ParseIssue],
    act: int | None,
    scene: int | None,
    compound_lines: bool,
) -> Speech | None:
    idx = _speech_index(speech_tag)
    speaker, sp_issues = _speaker_from_anchor(speech_tag)
    issues.extend([ParseIssue(i.severity, path, i.message, i.snippet) for i in sp_issues])
    bq = _blockquote_for_speech(speech_tag)
    if not bq:
        issues.append(
            ParseIssue(
                "warning",
                path,
                "speech missing following blockquote",
                f"speech{idx}",
            )
        )
        return Speech(speech_index=idx, speaker=speaker, items=[])
    items = _flatten_blockquote_items(
        bq,
        path=path,
        issues=issues,
        fallback_act=act,
        fallback_scene=scene,
        compound_lines=compound_lines,
    )
    if not items:
        issues.append(ParseIssue("warning", path, "empty speech blockquote", f"speech{idx}"))
    return Speech(speech_index=idx, speaker=speaker, items=items)


def parse_scene_file_path(path: Path) -> tuple[str, int, int] | None:
    m = _SCENE_FILE_RE.match(path.name)
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3))


def parse_scene_html(path: Path, issues: list[ParseIssue] | None = None) -> Scene | None:
    iss = issues if issues is not None else []
    path_str = str(path)
    meta = parse_scene_file_path(path)
    if not meta:
        iss.append(ParseIssue("warning", path_str, "filename does not match play.act.scene.html", None))
        return None
    _prefix, act, scene = meta
    html = read_html_text(path)
    soup = BeautifulSoup(html, "lxml")
    _strip_header_tables(soup)
    body = soup.body
    if not body:
        iss.append(ParseIssue("error", path_str, "no body element", None))
        return Scene(
            act=act,
            scene=scene,
            title=None,
            source_file=path.name,
            opening_stage_direction=None,
            speeches=[],
        )

    h3 = body.find(["h3", "H3"])
    title = clean_text(h3.get_text()) if h3 else None

    opening = None
    first_speech = body.find(_is_speech_anchor)
    if first_speech is not None:
        cand = first_speech.find_previous("blockquote")
        if cand is not None and _is_opening_blockquote(cand):
            opening = clean_text(cand.get_text())

    speeches: list[Speech] = []
    for tag in body.find_all(_is_speech_anchor):
        if tag.find_parent("blockquote") is not None:
            continue
        sp = _parse_speech(
            tag, path=path_str, issues=iss, act=act, scene=scene, compound_lines=False
        )
        if sp:
            speeches.append(sp)

    return Scene(
        act=act,
        scene=scene,
        title=title,
        source_file=path.name,
        opening_stage_direction=opening,
        speeches=speeches,
    )


def _h3_heading_kind(text: str) -> tuple[str, int | None, str] | None:
    t = clean_text(text)
    if not t:
        return None
    m = _ACT_HEAD.match(t)
    if m:
        num = _act_scene_token(m.group(1))
        return ("act", num, t)
    m = _SCENE_HEAD.match(t)
    if m:
        num = _act_scene_token(m.group(1))
        return ("scene", num, t)
    return None


def parse_full_play(path: Path, issues: list[ParseIssue] | None = None) -> ParsedPlay:
    iss = issues if issues is not None else []
    path_str = str(path)
    slug = path.parent.name
    html = read_html_text(path)
    soup = BeautifulSoup(html, "lxml")
    title = ""
    t_play = soup.find("td", class_="play")
    if t_play:
        title = clean_text(t_play.get_text())
    _strip_header_tables(soup)
    body = soup.body

    scenes: list[Scene] = []
    current_act: int | None = None
    current_scene: int | None = None
    scene_title: str | None = None
    scene_speeches: list[Speech] = []
    opening_pending: str | None = None

    def flush_scene() -> None:
        nonlocal scene_speeches, scene_title, current_act, current_scene, opening_pending
        if current_act is None or current_scene is None:
            if scene_speeches:
                iss.append(
                    ParseIssue(
                        "warning",
                        path_str,
                        "dropping speeches with no act/scene context",
                        None,
                    )
                )
            scene_speeches = []
            opening_pending = None
            return
        scenes.append(
            Scene(
                act=current_act,
                scene=current_scene,
                title=scene_title,
                source_file=path.name,
                opening_stage_direction=opening_pending,
                speeches=list(scene_speeches),
            )
        )
        scene_speeches = []
        opening_pending = None

    if not body:
        iss.append(ParseIssue("error", path_str, "no body element", None))
        return ParsedPlay(slug=slug, title=title, scenes=[], issues=iss)

    for el in body.find_all(True, recursive=True):
        if not isinstance(el, Tag):
            continue
        if el.name and el.name.lower() == "h3":
            kind_info = _h3_heading_kind(el.get_text())
            if not kind_info:
                continue
            kind, num, full_t = kind_info
            if kind == "act" and num is not None:
                flush_scene()
                current_act = num
                current_scene = None
                scene_title = None
            elif kind == "scene" and num is not None:
                flush_scene()
                current_scene = num
                scene_title = full_t
        elif _is_speech_anchor(el) and el.find_parent("blockquote") is None:
            if current_act is None:
                iss.append(
                    ParseIssue(
                        "warning",
                        path_str,
                        "speech before first ACT heading; skipped",
                        str(el.get("name")),
                    )
                )
                continue
            if current_scene is None:
                iss.append(
                    ParseIssue(
                        "warning",
                        path_str,
                        "speech before SCENE heading in act; skipped",
                        str(el.get("name")),
                    )
                )
                continue
            if not scene_speeches and opening_pending is None:
                prev = el.find_previous("blockquote")
                if prev is not None and _is_opening_blockquote(prev):
                    opening_pending = clean_text(prev.get_text())
            sp = _parse_speech(
                el,
                path=path_str,
                issues=iss,
                act=current_act,
                scene=current_scene,
                compound_lines=True,
            )
            if sp:
                scene_speeches.append(sp)

    flush_scene()
    play = ParsedPlay(slug=slug, title=title, scenes=scenes, issues=iss)
    return play


def merge_scenes_to_play(
    slug: str,
    title: str,
    genre: str | None,
    scene_pages: list[Scene],
    issues: list[ParseIssue],
) -> ParsedPlay:
    scene_pages = sorted(scene_pages, key=lambda s: (s.act, s.scene))
    return ParsedPlay(slug=slug, title=title, genre=genre, scenes=scene_pages, issues=list(issues))


def parse_play_index_title(index_path: Path) -> str:
    html = read_html_text(index_path)
    soup = BeautifulSoup(html, "lxml")
    cell = soup.find("td", class_="play")
    if cell:
        return clean_text(cell.get_text())
    return ""


def collect_scene_files(play_dir: Path) -> list[Path]:
    out: list[Path] = []
    for p in play_dir.glob("*.html"):
        if p.name in ("index.html", "full.html"):
            continue
        if _SCENE_FILE_RE.match(p.name):
            out.append(p)
    return sorted(out, key=lambda x: parse_scene_file_path(x) or ("", 0, 0))


def parse_play_directory(
    play_dir: Path,
    *,
    genre: str | None = None,
    prefer_full: bool = False,
) -> ParsedPlay:
    slug = play_dir.name
    issues: list[ParseIssue] = []
    index_path = play_dir / "index.html"
    title = parse_play_index_title(index_path) if index_path.is_file() else slug

    if prefer_full:
        full = play_dir / "full.html"
        if not full.is_file():
            issues.append(
                ParseIssue("warning", str(full), "prefer_full set but full.html missing", None)
            )
            prefer_full = False

    if prefer_full:
        play = parse_full_play(full, issues=issues)
        play.genre = genre
        if not play.title and title:
            play.title = title
        return play

    scenes: list[Scene] = []
    for sf in collect_scene_files(play_dir):
        sc = parse_scene_html(sf, issues=issues)
        if sc:
            scenes.append(sc)
    return merge_scenes_to_play(slug, title, genre, scenes, issues)
