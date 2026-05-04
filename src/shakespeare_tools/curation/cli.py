"""CLI for STRUCTSENSE-aligned curation pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shakespeare_tools.curation.emit import emit_trig, emit_turtle_flat
from shakespeare_tools.curation.graph_constants import INSTANCE_GRAPH_IRI as DEFAULT_GRAPH
from shakespeare_tools.curation.ontology_index import OntologyIndex
from shakespeare_tools.curation.pipeline import run_pipeline
from shakespeare_tools.curation.prep import passages_from_json_list, passages_to_json, prepare_path
from shakespeare_tools.curation.review_merge import auto_approve_all, apply_review
from shakespeare_tools.curation.task_pack import load_task_pack
from shakespeare_tools.curation.validation import load_draft_json, validate_for_export, write_draft_json


def cmd_prepare(args: argparse.Namespace) -> int:
    passages = prepare_path(Path(args.input), prefer_spacy=args.spacy)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(passages_to_json(passages), encoding="utf-8")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    raw = json.loads(Path(args.spans).read_text(encoding="utf-8"))
    passages = passages_from_json_list(raw)
    pack = load_task_pack(args.task_pack)
    index = None
    if args.ontology_ttl:
        index = OntologyIndex.from_path_auto(args.ontology_ttl)
    draft = run_pipeline(
        passages,
        pack,
        ontology_index=index,
        use_mock_llm=args.mock,
        llm_model=args.model,
    )
    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    write_draft_json(draft, outp)
    return 0


def cmd_apply_review(args: argparse.Namespace) -> int:
    bundle = load_draft_json(Path(args.draft))
    if args.auto_approve:
        merged = auto_approve_all(bundle)
    else:
        merged = apply_review(bundle)
    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    write_draft_json(merged, outp)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    bundle = load_draft_json(Path(args.draft))
    errs = validate_for_export(bundle)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    return 0


def cmd_export_turtle(args: argparse.Namespace) -> int:
    bundle = load_draft_json(Path(args.draft))
    if args.auto_approve:
        bundle = auto_approve_all(bundle)
    errs = validate_for_export(bundle)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    graph_iri = args.graph_instances
    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "trig":
        outp.write_text(emit_trig(bundle, graph_iri), encoding="utf-8")
    else:
        outp.write_text(emit_turtle_flat(bundle), encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shakespeare-curate")
    sub = p.add_subparsers(dest="command", required=True)

    pp = sub.add_parser("prepare", help="Segment TEI or text into passages + span JSON")
    pp.add_argument("input", type=str)
    pp.add_argument("-o", "--output", required=True)
    pp.add_argument("--spacy", action="store_true", help="Use spaCy (requires: uv sync --group curation-nlp)")
    pp.set_defaults(func=cmd_prepare)

    pr = sub.add_parser("run", help="Run extractor → alignment → judge")
    pr.add_argument("spans", type=str, help="JSON from prepare")
    pr.add_argument("--task-pack", required=True)
    pr.add_argument("-o", "--output", required=True)
    pr.add_argument("--mock", action="store_true", help="Stub LLM outputs (CI / offline)")
    pr.add_argument("--model", default=None, help="Override CURATION_LLM_MODEL")
    pr.add_argument("--ontology-ttl", default=None, help="Path to ontology/shakespeare_crm.ttl for label alignment")
    pr.set_defaults(func=cmd_run)

    pa = sub.add_parser("apply-review", help="Apply HIL decisions → approved_events")
    pa.add_argument("draft", type=str)
    pa.add_argument("-o", "--output", required=True)
    pa.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve all candidates (developer / CI only; not for production HIL)",
    )
    pa.set_defaults(func=cmd_apply_review)

    pv = sub.add_parser("validate", help="Validate draft is ready for export")
    pv.add_argument("draft", type=str)
    pv.set_defaults(func=cmd_validate)

    pe = sub.add_parser("export-turtle", help="Emit Turtle or TriG for approved_events")
    pe.add_argument("draft", type=str)
    pe.add_argument("-o", "--output", required=True)
    pe.add_argument(
        "--graph-instances",
        default=DEFAULT_GRAPH,
        help="Named graph IRI for TriG output",
    )
    pe.add_argument("--format", choices=("turtle", "trig"), default="turtle")
    pe.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve all candidates before export (developer / CI only)",
    )
    pe.set_defaults(func=cmd_export_turtle)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
