# Development roadmap

Four phases. Each phase should produce something **demonstrable** — not only internal progress.

| Phase | Goal | Status |
|-------|------|--------|
| **Phase 0** | Foundation: LinkML schema, core CIDOC mapping, Oxigraph with sample data | Not started |
| **Phase 1** | Data layer: Folger TEI → Turtle; full plays, characters, events | After P0 |
| **Phase 2** | Query interface: YASGUI, NL-to-SPARQL (LLM), example query library, results viewer | After P1 |
| **Phase 3** | Visualization: D3 graph, motif explorer, adaptation timeline, public deployment | After P2 |
| **Phase 4** | Enrichment: Wikidata linking, LOD, NLP motifs, paper + Zenodo | After P3 |

## Phase 0 — Foundation (weeks 1–2)

**Deliverables**

- Install and run Oxigraph locally (Docker Compose).
- Core LinkML schema: Play, Character, DramaticEvent, Performance (CIDOC-aligned).
- Compile schema to OWL; load into Oxigraph; SPARQL responds.
- Manually model **one complete play (Hamlet)** as Turtle (or via first ingest script).
- Run WIDoC for initial ontology documentation.
- **Five** SPARQL queries proving the model (see [example_queries.sparql](example_queries.sparql)).

**Success criterion:** Working Oxigraph with Hamlet modeled, queryable via SPARQL, WIDoC docs live at the documented path/URL.

## Phase 1 — Data layer (weeks 3–6)

**Deliverables**

- Parse Folger TEI for all plays; ingestion TEI → Turtle.
- Characters, named events, act/scene structure.
- Metadata: composition dates, genre, first performance records.
- Wikidata import or federation for historical performance data.
- Consistency checks; **50,000+** triples as a milestone (adjust with documentation if needed).

## Phase 2 — Query interface (weeks 7–10)

**Deliverables**

- YASGUI embedded with preloaded examples.
- FastAPI SPARQL proxy (CORS, auth hooks).
- NL-to-SPARQL (e.g. OpenAI function calling) with validation; narrate results only.
- **20+** curated example queries.
- Results viewer: table, JSON, graph preview.

## Phase 3 — Visualization (weeks 11–16)

**Deliverables**

- D3 force-directed graph; expand-on-click; filters (play, genre, motif, period).
- Motif explorer; adaptation timeline.
- Public URL with **read-only** SPARQL.

## Phase 4 — Enrichment and publishing (ongoing)

**Deliverables**

- Federate with Wikidata / DBpedia; LOD publication.
- NLP layer for motif extraction (optional scope).
- Paper: modeling Shakespeare’s literary world as CIDOC-CRM cultural heritage.
- Zenodo dataset DOI; venue targets — see [PUBLISHING.md](PUBLISHING.md).

---

*Dos and don’ts for ontology, ingestion, SPARQL, LLM, and docs: enforced in [AGENTS.md](../AGENTS.md).*
