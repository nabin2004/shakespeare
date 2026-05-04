"""Gradio UI: run SPARQL SELECT against Oxigraph (HTTP from this process only)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import gradio as gr
import httpx
import pandas as pd

_INSTANCE_GRAPH = "https://w3id.org/shakespeare-crm/graph/instances"

_STARTER_QUERIES: dict[str, str] = {
    "Works in instance graph": f"""PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?work ?label WHERE {{
  GRAPH <{_INSTANCE_GRAPH}> {{
    ?work a sc:Work .
    OPTIONAL {{ ?work rdfs:label ?label . }}
  }}
}}""",
    "Characters and labels": f"""PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?char ?label WHERE {{
  GRAPH <{_INSTANCE_GRAPH}> {{
    ?char a sc:FictionalCharacter .
    OPTIONAL {{ ?char rdfs:label ?label . }}
  }}
}}""",
    "Characters appearing in a work": """PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?char ?name ?work ?workLabel WHERE {
  GRAPH <https://w3id.org/shakespeare-crm/graph/instances> {
    ?char a sc:FictionalCharacter ;
          sc:appears_in_work ?work .
    ?work a sc:Work .
    OPTIONAL { ?char rdfs:label ?name . }
    OPTIONAL { ?work rdfs:label ?workLabel . }
  }
}""",
}


def _query_url_from_env() -> str:
    explicit = os.environ.get("SPARQL_ENDPOINT")
    if explicit:
        return explicit
    base = os.environ.get("OXIGRAPH_URL", "http://localhost:7878").rstrip("/")
    return f"{base}/query"


def run_select(query: str, endpoint: str) -> tuple[pd.DataFrame | None, str]:
    q = (query or "").strip()
    if not q:
        return None, "Enter a SPARQL query."
    ep = (endpoint or "").strip() or _query_url_from_env()
    try:
        r = httpx.post(
            ep,
            content=q.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=60.0,
        )
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPError as e:
        return None, f"HTTP error: {e}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON response: {e}"

    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return pd.DataFrame(), json.dumps(data, indent=2)

    vars_ = data.get("head", {}).get("vars", [])
    rows: list[dict[str, Any]] = []
    for b in bindings:
        row = {v: b.get(v, {}).get("value") for v in vars_}
        rows.append(row)
    return pd.DataFrame(rows), json.dumps(data, indent=2)


def build_blocks() -> gr.Blocks:
    default_ep = _query_url_from_env()
    default_q = _STARTER_QUERIES["Works in instance graph"]

    with gr.Blocks(title="ShakespeareCRM SPARQL") as demo:
        gr.Markdown("# ShakespeareCRM — SPARQL (read-only)\nQueries run **server-side** via HTTP; the browser does not talk to `/update`.")

        with gr.Row():
            starter = gr.Dropdown(
                choices=list(_STARTER_QUERIES.keys()),
                value="Works in instance graph",
                label="Example query",
            )
        endpoint = gr.Textbox(label="Query endpoint URL", value=default_ep)
        query_in = gr.Textbox(
            label="SPARQL",
            value=default_q,
            lines=16,
            max_lines=30,
        )
        run_btn = gr.Button("Run SELECT")
        err = gr.Markdown()
        table = gr.Dataframe(label="Bindings", interactive=False)
        raw = gr.Code(label="Raw JSON", language="json")

        def on_run(q: str, ep: str) -> tuple[pd.DataFrame, str, str]:
            df, detail = run_select(q, ep)
            if df is None:
                return pd.DataFrame(), f"**{detail}**", ""
            return df, "", detail

        run_btn.click(on_run, inputs=[query_in, endpoint], outputs=[table, err, raw])

        def load_starter(name: str) -> str:
            return _STARTER_QUERIES.get(name, default_q)

        starter.change(load_starter, inputs=[starter], outputs=[query_in])

    return demo


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    import argparse

    p = argparse.ArgumentParser(prog="shakespeare-sparql-ui")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--share", action="store_true", help="Enable Gradio share link (public tunnel).")
    args = p.parse_args(argv)

    demo = build_blocks()
    demo.launch(server_name=args.host, server_port=args.port, share=args.share)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
