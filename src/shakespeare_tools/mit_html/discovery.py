"""Discover play folders and genre metadata from works.html."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from shakespeare_tools.mit_html.clean import clean_text
from shakespeare_tools.mit_html.encoding import read_html_text


@dataclass(frozen=True)
class WorkRef:
    """Entry from the main works table (plays + poetry TOC pages)."""

    slug: str
    title: str
    genre: str
    href: str


def iter_play_directories(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name == "Poetry":
            continue
        if (child / "index.html").is_file():
            yield child


def load_works_catalog(works_path: Path) -> tuple[list[WorkRef], dict[str, str]]:
    """Return all table rows and a ``slug -> genre`` map for top-level play directories."""
    html = read_html_text(works_path)
    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")
    header_row_idx: int | None = None
    genre_labels: list[str] = []
    for i, row in enumerate(rows):
        h2s = row.find_all("h2")
        if len(h2s) < 4:
            continue
        genre_labels = [clean_text(h.get_text()).lower() for h in h2s[:4]]
        if "poetry" in genre_labels or ("comedy" in genre_labels and "history" in genre_labels):
            header_row_idx = i
            break
    refs: list[WorkRef] = []
    by_slug: dict[str, str] = {}
    if header_row_idx is None or header_row_idx + 1 >= len(rows):
        return refs, by_slug
    data_row = rows[header_row_idx + 1]
    cells = data_row.find_all("td", recursive=False)
    for genre, cell in zip(genre_labels, cells[:4]):
        for a in cell.find_all("a", href=True):
            href = str(a["href"]).strip()
            title = clean_text(a.get_text())
            parts = [p for p in href.split("/") if p]
            if not parts:
                continue
            if parts[0] == "Poetry":
                slug = parts[-1].replace(".html", "")
            else:
                slug = parts[0]
            refs.append(WorkRef(slug=slug, title=title, genre=genre, href=href))
            if parts[0] != "Poetry" and slug not in by_slug:
                by_slug[slug] = genre
    return refs, by_slug
