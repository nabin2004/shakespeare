"""Plain-text / TEI preparation: passages and sentence-like spans."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET

from shakespeare_tools.curation.models import PreparedPassage, SentenceSpan


def _fallback_sentences(text: str, passage_id: str) -> list[SentenceSpan]:
    """Heuristic sentence boundaries when spaCy is not installed."""
    sentences: list[SentenceSpan] = []
    # Split on . ! ? followed by space or end, keep indices roughly stable.
    pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])|(?<=[.!?])\s*$")
    start = 0
    part_idx = 0
    for m in pattern.finditer(text):
        end = m.start()
        chunk = text[start:end].strip()
        if chunk:
            sid = f"{passage_id}:s{part_idx}"
            sentences.append(
                SentenceSpan(span_id=sid, text=chunk, char_start=start, char_end=start + len(chunk))
            )
            part_idx += 1
        start = m.end()
    tail = text[start:].strip()
    if tail:
        sid = f"{passage_id}:s{part_idx}"
        sentences.append(
            SentenceSpan(span_id=sid, text=tail, char_start=start, char_end=start + len(tail))
        )
    if not sentences and text.strip():
        sentences.append(
            SentenceSpan(span_id=f"{passage_id}:s0", text=text.strip(), char_start=0, char_end=len(text.strip()))
        )
    return sentences


def _spacy_sentences(text: str, passage_id: str) -> list[SentenceSpan]:
    try:
        import spacy  # type: ignore import-not-found
    except ImportError as e:
        raise RuntimeError(
            "spaCy is not installed. Use: uv sync --group curation-nlp && uv run python -m spacy download en_core_web_sm"
        ) from e
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    out: list[SentenceSpan] = []
    for i, sent in enumerate(doc.sents):
        sid = f"{passage_id}:s{i}"
        out.append(
            SentenceSpan(
                span_id=sid,
                text=sent.text.strip(),
                char_start=sent.start_char,
                char_end=sent.end_char,
            )
        )
    return out if out else _fallback_sentences(text, passage_id)


def segment_text_to_sentences(text: str, passage_id: str, prefer_spacy: bool) -> list[SentenceSpan]:
    if prefer_spacy:
        try:
            import spacy  # noqa: F401
        except ImportError:
            return _fallback_sentences(text, passage_id)
        return _spacy_sentences(text, passage_id)
    return _fallback_sentences(text, passage_id)


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _collect_text_from_tei(elem: ET.Element) -> str:
    parts: list[str] = []

    def walk(e: ET.Element) -> None:
        if _strip_namespace(e.tag) in {"sp", "p", "l", "head"}:
            t = "".join(e.itertext()).strip()
            if t:
                parts.append(t)
            return
        for c in e:
            walk(c)

    walk(elem)
    return "\n".join(parts)


def prepare_path(path: Path | str, *, prefer_spacy: bool = False) -> list[PreparedPassage]:
    p = Path(path)
    passage_id = f"passage-{p.stem}-{uuid.uuid4().hex[:8]}"
    if p.suffix.lower() in {".xml", ".tei"}:
        tree = ET.parse(p)
        root = tree.getroot()
        passages: list[PreparedPassage] = []
        # Prefer div-level chunks; otherwise one root passage.
        divs = [e for e in root.iter() if _strip_namespace(e.tag) == "div"]
        if not divs:
            divs = [root]
        for i, div in enumerate(divs):
            pid = f"{passage_id}-div{i}"
            text = _collect_text_from_tei(div).strip()
            if not text:
                continue
            sents = segment_text_to_sentences(text, pid, prefer_spacy)
            passages.append(
                PreparedPassage(
                    passage_id=pid,
                    source_path=str(p.resolve()),
                    text=text,
                    char_end=len(text),
                    sentences=sents,
                )
            )
        return passages if passages else []

    raw = p.read_text(encoding="utf-8")
    sents = segment_text_to_sentences(raw, passage_id, prefer_spacy)
    return [
        PreparedPassage(
            passage_id=passage_id,
            source_path=str(p.resolve()),
            text=raw,
            char_end=len(raw),
            sentences=sents,
        )
    ]


def passages_to_json(passages: list[PreparedPassage]) -> str:
    return json.dumps([m.model_dump(mode="json") for m in passages], indent=2, ensure_ascii=False)


def passages_from_json_list(data: list[dict]) -> list[PreparedPassage]:
    return [PreparedPassage.model_validate(x) for x in data]
