"""Batch-export MIT Shakespeare HTML to JSON under ``data/processed/mit_html/``."""

from __future__ import annotations

import argparse
from pathlib import Path

from shakespeare_tools.mit_html.discovery import iter_play_directories, load_works_catalog
from shakespeare_tools.mit_html.models import PoemPage, dump_json
from shakespeare_tools.mit_html.plays import parse_play_directory
from shakespeare_tools.mit_html.poetry import iter_poem_files, parse_poem_html


def _repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").is_file():
            return p
    return start.resolve()


def main() -> None:
    root_default = Path(__file__).resolve().parents[3] / "data" / "raw" / "shakespeare"
    ap = argparse.ArgumentParser(description="Parse MIT Shakespeare HTML clone → JSON.")
    ap.add_argument("--root", type=Path, default=root_default, help="Corpus root (contains works.html)")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: <repo>/data/processed/mit_html)",
    )
    ap.add_argument("--play", type=str, default=None, help="Only this play directory name (e.g. hamlet)")
    ap.add_argument("--poetry", action="store_true", help="Also emit poem JSON files from Poetry/")
    ap.add_argument(
        "--prefer-full",
        action="store_true",
        help="Use full.html per play when available (compound line anchors)",
    )
    args = ap.parse_args()
    repo = _repo_root(Path.cwd())
    out_root = args.out if args.out is not None else repo / "data" / "processed" / "mit_html"
    out_root.mkdir(parents=True, exist_ok=True)

    corpus = args.root.resolve()
    works = corpus / "works.html"
    genres: dict[str, str] = {}
    if works.is_file():
        _, genres = load_works_catalog(works)

    play_dirs = list(iter_play_directories(corpus))
    if args.play:
        play_dirs = [p for p in play_dirs if p.name == args.play]
        if not play_dirs:
            raise SystemExit(f"No play directory named {args.play!r} under {corpus}")

    plays_out = out_root / "plays"
    plays_out.mkdir(parents=True, exist_ok=True)
    for pdir in play_dirs:
        genre = genres.get(pdir.name)
        play = parse_play_directory(pdir, genre=genre, prefer_full=args.prefer_full)
        out_path = plays_out / f"{pdir.name}.json"
        out_path.write_text(dump_json(play), encoding="utf-8")

    if args.poetry:
        poetry_dir = corpus / "Poetry"
        poems_out = out_root / "poetry"
        poems_out.mkdir(parents=True, exist_ok=True)
        for pf in iter_poem_files(poetry_dir):
            poem = parse_poem_html(pf)
            if not poem.lines:
                continue
            out_path = poems_out / f"{poem.slug}.json"
            out_path.write_text(dump_json(poem), encoding="utf-8")


if __name__ == "__main__":
    main()
