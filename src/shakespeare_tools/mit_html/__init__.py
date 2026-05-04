"""Parse MIT/Moby Shakespeare static HTML into structured text."""

from shakespeare_tools.mit_html.discovery import WorkRef, iter_play_directories, load_works_catalog
from shakespeare_tools.mit_html.models import (
    ParsedPlay,
    PoemPage,
    Scene,
    Speech,
    StageDirection,
    TextLine,
    dump_json,
)
from shakespeare_tools.mit_html.plays import parse_full_play, parse_scene_html
from shakespeare_tools.mit_html.poetry import parse_poem_html

__all__ = [
    "iter_play_directories",
    "load_works_catalog",
    "parse_full_play",
    "parse_poem_html",
    "parse_scene_html",
    "ParsedPlay",
    "PoemPage",
    "Scene",
    "Speech",
    "StageDirection",
    "TextLine",
    "WorkRef",
    "dump_json",
]
