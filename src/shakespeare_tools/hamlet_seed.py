"""Build minimal Hamlet instance Turtle from LinkML example YAMLs."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from rdflib import Graph


def build_hamlet_seed_turtle(repo_root: Path) -> str:
    """Merge sample Work + FictionalCharacter LinkML instances into one Turtle document."""
    schema = repo_root / "schemas" / "shakespeare_crm.yaml"
    work_yaml = repo_root / "schemas" / "examples" / "sample_work.yaml"
    char_yaml = repo_root / "schemas" / "examples" / "sample_character.yaml"
    for p in (schema, work_yaml, char_yaml):
        if not p.is_file():
            raise FileNotFoundError(p)

    linkml_convert = shutil.which("linkml-convert")
    if linkml_convert is None:
        raise RuntimeError("linkml-convert not on PATH (use: uv run shakespeare-oxigraph-load)")

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        work_ttl = td_path / "work.ttl"
        char_ttl = td_path / "char.ttl"
        subprocess.run(
            [
                linkml_convert,
                "-s",
                str(schema),
                "-C",
                "Work",
                "-t",
                "ttl",
                str(work_yaml),
                "-o",
                str(work_ttl),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                linkml_convert,
                "-s",
                str(schema),
                "-C",
                "FictionalCharacter",
                "-t",
                "ttl",
                str(char_yaml),
                "-o",
                str(char_ttl),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        merged = Graph()
        merged.parse(work_ttl, format="turtle")
        merged.parse(char_ttl, format="turtle")
        return merged.serialize(format="turtle")


def build_hamlet_seed_file(repo_root: Path, out: Path) -> None:
    out.write_text(build_hamlet_seed_turtle(repo_root), encoding="utf-8")
