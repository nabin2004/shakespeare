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
    "Dramatic Events in a work": """PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?motif ?workLabel ?scene WHERE {
  GRAPH <https://w3id.org/shakespeare-crm/graph/instances> {
    ?event a sc:DramaticEvent ;
           sc:in_work ?work .
    OPTIONAL { ?event sc:motif_type ?motif . }
    OPTIONAL { ?event sc:dramatic_scene ?scene . }
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


def get_works() -> list[str]:
    df, _ = run_select(_STARTER_QUERIES["Works in instance graph"], "")
    if df is None or df.empty:
        return []
    return df["label"].dropna().unique().tolist()


def get_imdb_view(work_label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    query_chars = f"""PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?Character WHERE {{
  GRAPH <https://w3id.org/shakespeare-crm/graph/instances> {{
    ?char a sc:FictionalCharacter ;
          sc:appears_in_work ?work .
    ?work a sc:Work ;
          rdfs:label "{work_label}" .
    ?char rdfs:label ?Character .
  }}
}}"""
    df_chars, _ = run_select(query_chars, "")

    query_events = f"""PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?Motif ?Scene ?Speaker WHERE {{
  GRAPH <https://w3id.org/shakespeare-crm/graph/instances> {{
    ?event a sc:DramaticEvent ;
           sc:in_work ?work .
    ?work a sc:Work ;
          rdfs:label "{work_label}" .
    OPTIONAL {{ ?event sc:motif_type ?Motif . }}
    OPTIONAL {{ ?event sc:dramatic_scene ?Scene . }}
    OPTIONAL {{ ?event sc:speaker_label ?Speaker . }}
  }}
}}"""
    df_events, _ = run_select(query_events, "")

    if df_chars is None:
        df_chars = pd.DataFrame()
    if df_events is None:
        df_events = pd.DataFrame()

    return df_chars, df_events


def get_graph_html(work_label: str) -> str:
    query = f"""PREFIX sc: <https://w3id.org/shakespeare-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?char_label ?event_motif WHERE {{
  GRAPH <https://w3id.org/shakespeare-crm/graph/instances> {{
    ?work a sc:Work ;
          rdfs:label "{work_label}" .
    ?event a sc:DramaticEvent ;
           sc:in_work ?work ;
           sc:motif_type ?event_motif ;
           sc:speaker_label ?speaker .
    ?char a sc:FictionalCharacter ;
          sc:appears_in_work ?work ;
          rdfs:label ?char_label .
    FILTER(UCASE(STR(?char_label)) = UCASE(STR(?speaker)))
  }}
}}"""
    df, _ = run_select(query, "")

    nodes = [{"id": work_label, "group": 1}]
    links = []

    if df is not None and not df.empty:
        chars = df["char_label"].dropna().unique().tolist()
        for char in chars:
            nodes.append({"id": char, "group": 2})
            links.append({"source": work_label, "target": char, "value": 1})

        for _, row in df.iterrows():
            char = row["char_label"]
            motif = row["event_motif"]
            if pd.notna(motif):
                motif_id = f"Motif: {motif}"
                if not any(n["id"] == motif_id for n in nodes):
                    nodes.append({"id": motif_id, "group": 3})
                links.append({"source": char, "target": motif_id, "value": 1})

    graph_data = {"nodes": nodes, "links": links}

    html = f"""
    <!DOCTYPE html>
    <meta charset="utf-8">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
      .node text {{ pointer-events: none; font: 10px sans-serif; }}
    </style>
    <body>
    <div id="d3-container" style="width:100%; height:600px;"></div>
    <script>
    const data = {json.dumps(graph_data)};
    const width = 800;
    const height = 600;

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const svg = d3.select("#d3-container").append("svg")
        .attr("viewBox", [0, 0, width, height]);

    const link = svg.append("g")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(data.links)
      .join("line")
        .attr("stroke-width", d => Math.sqrt(d.value));

    const node = svg.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(data.nodes)
      .join("circle")
        .attr("r", 10)
        .attr("fill", d => color(d.group))
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    node.append("title")
        .text(d => d.id);

    const labels = svg.append("g")
      .selectAll("text")
      .data(data.nodes)
      .join("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(d => d.id);

    simulation.on("tick", () => {{
      link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

      node
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);

      labels
          .attr("x", d => d.x)
          .attr("y", d => d.y);
    }});

    function dragstarted(event) {{
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }}
    function dragged(event) {{
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }}
    function dragended(event) {{
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }}
    </script>
    </body>
    """
    return html


def build_blocks() -> gr.Blocks:
    default_ep = _query_url_from_env()
    default_q = _STARTER_QUERIES["Works in instance graph"]

    works_list = []
    try:
        works_list = get_works()
    except Exception:
        pass

    if not works_list:
        works_list = ["Hamlet", "Macbeth"]

    with gr.Blocks(title="ShakespeareCRM Prototype") as demo:
        with gr.Tabs():
            with gr.Tab("SPARQL Explorer"):
                gr.Markdown("# ShakespeareCRM — SPARQL (read-only)\nQueries run **server-side** via HTTP.")
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

            with gr.Tab("IMDB View"):
                gr.Markdown("# Shakespeare IMDB View")
                gr.Markdown("Select a work to see its characters and dramatic events.")

                work_dropdown = gr.Dropdown(choices=works_list, value=works_list[0] if works_list else None, label="Select Work")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Cast (Characters)")
                        chars_table = gr.Dataframe(label="Characters", interactive=False)
                    with gr.Column():
                        gr.Markdown("### Dramatic Events (Motifs & Scenes)")
                        events_table = gr.Dataframe(label="Events", interactive=False)

                def update_imdb(work: str):
                    c, e = get_imdb_view(work)
                    return c, e

                work_dropdown.change(update_imdb, inputs=[work_dropdown], outputs=[chars_table, events_table])
                # Load initially
                demo.load(update_imdb, inputs=[work_dropdown], outputs=[chars_table, events_table])

            with gr.Tab("Graph Visualization"):
                gr.Markdown("# Graph Visualization")
                gr.Markdown("A force-directed D3 graph visualizing characters and motifs for a selected work.")
                vis_work_dropdown = gr.Dropdown(choices=works_list, value=works_list[0] if works_list else None, label="Select Work")

                d3_html = gr.HTML(label="Graph")

                def update_graph(work: str):
                    return get_graph_html(work)

                vis_work_dropdown.change(update_graph, inputs=[vis_work_dropdown], outputs=[d3_html])
                # Load initially
                demo.load(update_graph, inputs=[vis_work_dropdown], outputs=[d3_html])

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
