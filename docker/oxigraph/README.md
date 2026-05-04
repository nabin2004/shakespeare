# Oxigraph

Local SPARQL 1.1 store for ShakespeareCRM (Phase 0).

## Run

From the **repository root**:

```bash
docker compose -f docker/docker-compose.yml up oxigraph
```

- **SPARQL UI (YASGUI):** [http://localhost:7878/](http://localhost:7878/)
- **Query:** `POST http://localhost:7878/query` ([SPARQL 1.1 Protocol](https://www.w3.org/TR/sparql11-protocol/#query-operation))
- **Update:** `POST http://localhost:7878/update` (keep non-public in production; see [AGENTS.md](../../AGENTS.md))
- **Graph Store:** `POST http://localhost:7878/store?graph=…` ([Graph Store HTTP Protocol](https://www.w3.org/TR/sparql11-http-rdf-update/))

Data persists in the `oxigraph_data` Docker volume (`serve --location /data`).

The official image is **distroless** (no shell or `curl`), so Compose does not define an in-container healthcheck. Verify readiness by opening the UI or running a query from the host.

## Load ontology + Hamlet seed

After `uv run generate-ontology` (so `ontology/shakespeare_crm.ttl` exists):

```bash
uv run shakespeare-oxigraph-load
# or
uv run python data/ingest/hamlet.py
```

Override base URL: `OXIGRAPH_URL=http://other:7878 uv run shakespeare-oxigraph-load`.

## Gradio UI

```bash
uv sync --group ui
uv run shakespeare-sparql-ui
```

Executes **SELECT** queries server-side only (read-only path from the browser’s perspective).
