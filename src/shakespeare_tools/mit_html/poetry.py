"""Poetry pages (sonnets, narrative poems) — different template from plays."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from shakespeare_tools.mit_html.clean import clean_text
from shakespeare_tools.mit_html.encoding import read_html_text
from shakespeare_tools.mit_html.errors import ParseIssue
from shakespeare_tools.mit_html.models import PoemPage


def parse_poem_html(path: Path, issues: list[ParseIssue] | None = None) -> PoemPage:
    iss = issues if issues is not None else []
    path_str = str(path)
    html = read_html_text(path)
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find(["h1", "H1"])
    title = clean_text(h1.get_text()) if h1 else path.stem.replace("_", " ")
    bqs = soup.find_all("blockquote")
    lines: list[str] = []
    if not bqs:
        iss.append(ParseIssue("warning", path_str, "no blockquote in poem page", None))
        return PoemPage(
            slug=path.stem,
            title=title,
            lines=[],
            source_file=path.name,
            issues=iss,
        )
    for bq in bqs:
        for br in list(bq.find_all("br")):
            br.replace_with("\n")
        raw = bq.get_text()
        for part in raw.split("\n"):
            t = clean_text(part)
            if t:
                lines.append(t)
    if not lines:
        iss.append(ParseIssue("warning", path_str, "empty poem blockquote", None))
    return PoemPage(
        slug=path.stem,
        title=title,
        lines=lines,
        source_file=path.name,
        issues=iss,
    )


def iter_poem_files(poetry_dir: Path) -> list[Path]:
    if not poetry_dir.is_dir():
        return []
    paths = sorted(poetry_dir.glob("*.html"))
    toc_names = {"sonnets.html"}
    return [p for p in paths if p.name not in toc_names]
