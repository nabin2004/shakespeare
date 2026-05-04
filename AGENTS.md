# ShakespeareCRM — Agent playbook

Read this file before changing schema, data, or runtime code. The full charter lives in [docs/VISION.md](docs/VISION.md).

## Mission

Build a **research-grade** knowledge graph of Shakespeare’s world using CIDOC-CRM semantics. The product is **query and exploration** (SPARQL + visualization), not open-ended LLM answers. See [docs/VISION.md](docs/VISION.md) for features and positioning.

## Hard constraints (non-negotiable)

- **LinkML is the single source of truth** for classes and slots. Master file: [schemas/shakespeare_crm.yaml](schemas/shakespeare_crm.yaml). Generate OWL/Turtle/JSON Schema/Python from it; **never** hand-edit generated files under [ontology/](ontology/).
- **Ontology vs data:** Use **named graphs** from day one (e.g. separate graph IRIs for ontology, instance data, and inferred material — exact IRIs documented when Phase 0 lands in schema/docs).
- **LLM role:** Translate natural language → SPARQL (and optionally narrate query results). **Do not** let the LLM state facts not returned by the graph. If SPARQL returns empty, say so — **no training-data fallback**.
- **SPARQL safety:** Validate or parse generated SPARQL before execution; block injection and unknown predicates relative to the schema.
- **Public write path:** Do **not** expose Oxigraph’s SPARQL Update endpoint directly to the browser. Writes (if any) go through [api/](api/) with authentication and validation; public deploys stay **read-only**.
- **Ingestion:** Prefer **Folger TEI** as canonical structure. Generated Turtle under [data/triples/](data/triples/) is a **build artifact** — fix schema or [data/ingest/](data/ingest/) scripts, not committed triple dumps, when the model is wrong.
- **Idempotency:** Ingestion scripts must be **repeatable** (deterministic URIs; no duplicate junk on re-run).
- **Modeling order:** **Hamlet first** — one play fully modeled and query-tested before scaling to the full corpus.
- **Events over flat edges:** Prefer CIDOC-CRM **E5 Event** (with types, participants, time) over a single “X killed Y” predicate.

When in doubt about awkward modeling, read [docs/PITFALLS.md](docs/PITFALLS.md).

## Repository map

| Path | Responsibility | Edit policy |
|------|----------------|-------------|
| [schemas/](schemas/) | LinkML schema and extensions | **Human/agent edits** — primary |
| [ontology/](ontology/) | OWL/Turtle from LinkML | **Generated only** |
| [data/raw/](data/raw/) | Downloaded TEI and dumps | Optional local; large files gitignored |
| [data/triples/](data/triples/) | Output Turtle per domain | Generated / optional commit |
| [data/ingest/](data/ingest/) | Parsers and loaders | Agent edits |
| [docs/](docs/) | Vision, roadmap, SPARQL examples | Agent edits |
| [api/](api/) | FastAPI, NL-to-SPARQL | Phase 2+ |
| [frontend/](frontend/) | Next.js, YASGUI, D3 | Phase 2–3+ |
| [docker/](docker/) | Compose, Oxigraph, WIDoC | Phase 0+ |
| [scripts/](scripts/) | Codegen, CI helpers | Any phase |
| [tests/](tests/) | SPARQL golden tests, validation | Any phase |

## Phase gates (exit criteria)

### Phase 0 — Foundation (start here)

**Status:** Not started (scaffold only until implemented.)

- [ ] Docker Compose runs Oxigraph locally (and optional WIDoC service).
- [ ] Core LinkML schema for Play, Character, DramaticEvent, Performance (CIDOC-aligned).
- [ ] Compile schema → OWL/Turtle; load into Oxigraph; SPARQL endpoint responds.
- [ ] **Hamlet** fully modeled as Turtle (or generated from ingest) and loaded.
- [ ] WIDoC generates ontology HTML (path/URL documented, ideally wired in CI later).
- [ ] **Five** SPARQL queries in [docs/example_queries.sparql](docs/example_queries.sparql) validated against the Hamlet graph.

**Success:** Working Oxigraph with Hamlet, queryable via SPARQL, with WIDoC docs available at the documented URL/path.

### Phase 1 — Data layer

- [ ] Ingest Folger TEI for all plays; Python pipeline TEI → CRM Turtle.
- [ ] Characters, events, act/scene structure; metadata (dates, genre, performances).
- [ ] Optional Wikidata federation for performance/historical records.
- [ ] Quality milestone: **50,000+** triples (adjust if scope changes — document actual target).

### Phase 2 — Query interface

- [ ] YASGUI embedded in frontend; example queries preloaded.
- [ ] FastAPI SPARQL proxy (CORS, auth hooks).
- [ ] NL-to-SPARQL via LLM with few-shot examples from **this** schema; validation before execute.
- [ ] **20+** curated example queries; results viewer (table, JSON, graph preview).

### Phase 3 — Visualization

- [ ] D3 force-directed graph with progressive disclosure (expand on click).
- [ ] Filters (play, genre, motif, time).
- [ ] Motif explorer; adaptation timeline.
- [ ] Public read-only deploy (SPARQL + UI).

### Phase 4 — Enrichment and publishing

- [ ] External linking (Wikidata, DBpedia); LOD publication.
- [ ] NLP-assisted motif extraction (if in scope).
- [ ] Paper + Zenodo dataset with DOI; see [docs/PUBLISHING.md](docs/PUBLISHING.md).

## Testing expectations

- Add **SPARQL correctness tests** under [tests/](tests/) that run against a known small graph (Hamlet fixture).
- **Example queries** double as regression tests and documentation.
- Schema changes should trigger regeneration of ontology artifacts and doc builds in CI (when CI exists).

## Contributing norms (short)

Keep PRs **focused**. One play modeled completely before corpus-wide shortcuts. Do not mix fictional characters with real persons without explicit modeling (see [docs/PITFALLS.md](docs/PITFALLS.md)).

## When stuck

- Ontology modeling edge cases: [docs/PITFALLS.md](docs/PITFALLS.md)  
- Product phases and timelines: [docs/ROADMAP.md](docs/ROADMAP.md)  
- Layer boundaries: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
