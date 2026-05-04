# Documentation, datasets, and publication

## Documentation and CI

- Run **WIDoC** (or successor) in CI/CD so every schema change regenerates HTML ontology documentation.
- Stale hand-written ontology docs are worse than none — prefer generated docs from OWL produced by LinkML.

## Dataset releases (targets)

| Artifact | Purpose |
|----------|---------|
| `shakespeare-crm.ttl` | Full RDF dataset (e.g. Zenodo with DOI) |
| `shakespeare-crm.owl` | Ontology upload (e.g. BioPortal, LOV) |
| Curated SPARQL library | GitHub release or `sparql-queries/` directory |
| WIDoC HTML | Stable URL linked from README and dataset metadata |

## Licensing

- **Code:** MIT (see repository [LICENSE](../LICENSE)).
- **Data:** Prefer **CC BY 4.0** for cultural heritage releases unless source terms require otherwise — state attribution for Folger TEI and other upstream sources in dataset README and Zenodo metadata.

## Publication venues (angles)

| Venue | Angle | Type |
|-------|-------|------|
| Semantic Web Journal | Ontology + dataset | Dataset / resource |
| ESWC / ISWC | NL-to-SPARQL grounding (KG + LLM) | Research paper |
| Digital Humanities Quarterly | CIDOC-CRM for literary corpora | Humanities paper |
| EKAW / K-CAP | Ontology design patterns for fiction | Technical paper |

## Demo bar (minimum credible)

- Public **read-only** Oxigraph / SPARQL endpoint  
- YASGUI (or equivalent) with **10+** example queries  
- **One** strong visualization (e.g. cross-play betrayal network)  
- WIDoC docs linked from README  

**Impact goal:** A first-time user runs a preloaded query, sees the graph visualization, and understands this is **structured literary history**, not a search engine or chatbot.

---

*Vision: [VISION.md](VISION.md). Roadmap: [ROADMAP.md](ROADMAP.md).*
