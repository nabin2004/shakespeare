"""Orchestrate standard LinkML CLIs against ``schemas/shakespeare_crm.yaml``.

This matches the upstream tutorial flow: edit the schema YAML first, then run generator
CLI tools (here we wrap ``gen-owl`` for repeatable outputs). Prefer ``uv run`` so the
venv provides ``gen-owl``, ``gen-json-schema``, ``linkml-validate``, etc.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SCHEMA = _REPO_ROOT / "schemas" / "shakespeare_crm.yaml"
_DEFAULT_OUT = _REPO_ROOT / "ontology"


def _venv_bin(tool: str) -> Path:
    exe = shutil.which(tool)
    if exe:
        return Path(exe).resolve()
    return Path(sys.executable).resolve().parent / tool


def generate(schema_path: Path, out_dir: Path) -> tuple[Path, Path]:
    """Write Turtle and RDF/XML using ``gen-owl`` with CIDOC-facing slot URIs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = schema_path.stem
    ttl_path = out_dir / f"{stem}.ttl"
    owl_path = out_dir / f"{stem}.owl"
    gen_owl = _venv_bin("gen-owl")

    # Emit declared ``slot_uri`` / ``class_uri`` IRIs (e.g. crm:P11…) instead of sc:-only names.
    base = [
        str(gen_owl),
        str(schema_path.resolve()),
        "--no-use-native-uris",
        "--mergeimports",
        "--stacktrace",
    ]
    # ``gen-owl`` emits OWL to stdout; ``-o`` may not persist output with current LinkML CLI.
    r_ttl = subprocess.run(
        [*base, "-f", "ttl"],
        check=True,
        capture_output=True,
        text=True,
    )
    ttl_path.write_text(r_ttl.stdout, encoding="utf-8")
    r_owl = subprocess.run(
        [*base, "-f", "xml"],
        check=True,
        capture_output=True,
        text=True,
    )
    owl_path.write_text(r_owl.stdout, encoding="utf-8")
    return ttl_path, owl_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate ontology/ from LinkML YAML using the official ``gen-owl`` CLI "
            "(Turtle + RDF/XML)."
        ),
        epilog=(
            "Workflow: edit ``schemas/shakespeare_crm.yaml`` first. For JSON Schema "
            "(``uv run gen-json-schema …``), instance validation "
            "(``uv run linkml-validate …``), and RDF data conversion "
            "(``uv run linkml-convert …``), see ontology/README.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=_DEFAULT_SCHEMA,
        help=f"Path to LinkML YAML (default: {_DEFAULT_SCHEMA})",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"Output directory (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args()
    schema_path = args.schema.resolve()
    if not schema_path.is_file():
        raise SystemExit(f"Schema not found: {schema_path}")
    print(f"Generating ontology from LinkML: {schema_path}")
    ttl, owl = generate(schema_path, args.out_dir.resolve())
    print(f"Wrote {ttl}")
    print(f"Wrote {owl}")


if __name__ == "__main__":
    main()
