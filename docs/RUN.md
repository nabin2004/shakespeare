# How to run each component

One reference for Phase 0 tooling: triple store, codegen, ingestion, UI, docs, optional data prep, tests, and roadmap placeholders.

**Assumptions:** repository root as current working directory, [uv](https://github.com/astral-sh/uv) installed, Docker available for Oxigraph/WIDOCO.

---

## 1. Python environment

```bash
uv sync
```

**Optional dependency groups:**

| Group | Command | When |
|--------|---------|------|
| Dev / tests | `uv sync --group dev` | `pytest` |
| Gradio UI | `uv sync --group ui` | `shakespeare-sparql-ui` |
| spaCy segmentation | `uv sync --group curation-nlp` | `shakespeare-curate prepare --spacy` |

---

## 2. Ontology generation (LinkML → OWL / Turtle)

Edits belong in `schemas/`; artifacts land in `ontology/` (generated).

```bash
uv run generate-ontology
```

Produces outputs such as `ontology/shakespeare_crm.ttl` and `ontology/shakespeare_crm.owl`. Required before loading the store or building WIDOCO.

---

## 3. Oxigraph (SPARQL store)

Starts the triple store (data persists in the `oxigraph_data` Compose volume).

```bash
docker compose -f docker/docker-compose.yml up oxigraph
```

| Endpoint | URL |
|-----------|-----|
| YASGUI / browser UI | [http://localhost:7878/](http://localhost:7878/) |
| Query (`POST`) | `http://localhost:7878/query` |
| Update (`POST`) | `http://localhost:7878/update` |
| Graph Store | `http://localhost:7878/store?graph=…` |

Scoped details: [docker/oxigraph/README.md](../docker/oxigraph/README.md).

---

## 4. Load TBox + Hamlet seed into Oxigraph

Requires a running Oxigraph (section 3) and generated Turtle (section 2).

```bash
uv run shakespeare-oxigraph-load
```

Equivalent script:

```bash
uv run python data/ingest/hamlet.py
```

**Useful flags:**

- `--skip-clear` — append without clearing named graphs first (risk of duplicates).
- `--no-build-seed` — skip regenerating seed; `--instances` must already exist.
- `--ontology PATH`, `--instances PATH` — override file locations.
- `--base-url URL` — default from env `OXIGRAPH_URL` or `http://localhost:7878`.

---

## 5. Gradio SPARQL UI

Browser UI that POSTs SELECT queries to Oxigraph from the Python process (read-only path for the browser).

```bash
uv sync --group ui
uv run shakespeare-sparql-ui
```

Defaults: host `127.0.0.1`, port `7860` → [http://127.0.0.1:7860](http://127.0.0.1:7860).

**Overrides:**

```bash
uv run shakespeare-sparql-ui --host 0.0.0.0 --port 7860 --share   # --share = public Gradio tunnel
```

**Endpoints:** set `SPARQL_ENDPOINT` to a full query URL, or set `OXIGRAPH_URL` (base, default `http://localhost:7878`); the UI uses `{OXIGRAPH_URL}/query` when `SPARQL_ENDPOINT` is unset.

---

## 6. WIDOCO (ontology HTML + WebVOWL)

Requires `uv run generate-ontology` so `ontology/shakespeare_crm.owl` exists.

**Regenerate static site into `docs/widoco/`** (gitignored output):

```bash
docker compose -f docker/docker-compose.yml --profile docs build widoco-generate
docker compose -f docker/docker-compose.yml --profile docs run --rm widoco-generate
```

**Serve at [http://localhost:8080/](http://localhost:8080/)** (regenerates, then nginx):

```bash
docker compose -f docker/docker-compose.yml --profile docs up --build widoco
```

More detail: [docker/widoco/README.md](../docker/widoco/README.md).

**Compose-only placeholder** (no real stack):

```bash
docker compose -f docker/docker-compose.yml --profile scaffold up scaffold_placeholder
```

---

## 7. Scripts for Cleaning Raw Data (MIT HTML corpus → JSON)

Batch export from a local MIT Shakespeare HTML tree to clean JSON format. By default, it uses `data/raw/shakespeare` as the input root and outputs to `data/processed/mit_html`.

```bash
uv run mit-html-parse
```

**Common options:** 
- `--root path/to/raw/shakespeare` (override the default raw data path)
- `--play hamlet` (parse a specific play only)
- `--poetry` (also emit JSON for poems)
- `--prefer-full` (use full.html per play with compound anchors)
- `--out DIR` (override the default `data/processed/mit_html` output path).

---

## 8. STRUCTSENSE-style curation pipeline (`shakespeare-curate`)

The pipeline is broken down into multiple steps (prepare, run, review, validate, and export). Here is an example of running the sequence:

1. **Prepare passages** from an input file (e.g., `1henryiv.json`):
   ```bash
   uv run shakespeare-curate prepare data/processed/mit_html/plays/1henryiv.json -o passages.json --spacy
   ```

2. **Run the curation tasks** using a specified task pack (using `--mock` for offline/CI environments without a live LLM):
   ```bash
   uv run shakespeare-curate run passages.json --task-pack src/shakespeare_tools/curation/examples/hamlet_task_pack.yaml -o draft.json --mock
   ```

3. **Apply reviews** to the draft to approve suggestions:
   ```bash
   uv run shakespeare-curate apply-review draft.json -o merged.json --auto-approve
   ```

4. **Validate** the generated structures in the merged file:
   ```bash
   uv run shakespeare-curate validate merged.json
   ```

5. **Export to Turtle/RDF** for loading into the knowledge graph:
   ```bash
   uv run shakespeare-curate export-turtle merged.json -o out.ttl
   ```

---

## 9. Tests

```bash
uv sync --group dev
uv run pytest tests/
```

Covers MIT HTML parsing, curation pipeline (mock), and Oxigraph loader behavior where applicable.

---

## 10. Roadmap / not wired as runnable apps

| Piece | Location | Status |
|--------|-----------|--------|
| Next.js frontend | `frontend/` | Scaffold / Phase 2+ — no app in tree to `npm run` yet. |
| FastAPI SPARQL proxy | `api/` | Phase 2+ — `api/nl_to_sparql.py` is stubs only. |

---

## Environment variables (quick reference)

| Variable | Used by |
|----------|---------|
| `OXIGRAPH_URL` | `shakespeare-oxigraph-load`, Gradio UI (base URL for `/query`) |
| `SPARQL_ENDPOINT` | Gradio UI (full query URL; overrides `OXIGRAPH_URL`-derived default) |
| `CURATION_LLM_MODEL` | Curation pipeline (override with `shakespeare-curate run --model`) |

---

## Typical local order

1. `uv sync` (+ `--group ui` if using Gradio)  
2. `uv run generate-ontology`  
3. `docker compose -f docker/docker-compose.yml up oxigraph`  
4. `uv run shakespeare-oxigraph-load`  
5. Query via [http://localhost:7878/](http://localhost:7878/) or `uv run shakespeare-sparql-ui`  

Example SPARQL: [docs/example_queries.sparql](example_queries.sparql).
