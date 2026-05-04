# Ontology design

## CIDOC-CRM entity mapping

How Shakespeare domain objects map to CIDOC-CRM (high level):

| Shakespeare domain | CIDOC-CRM class | Notes |
|--------------------|-----------------|-------|
| Play / Poem | E73 Information Object | Work as intellectual creation |
| First Folio / Quarto | E22 Human-Made Object | Physical instantiation of the text |
| Character | E39 Actor (fictional) | Extend with fictional subclass or `is_fictional` in LinkML — do not conflate with E21 Person |
| Dramatic event (murder, betrayal) | E5 Event | Temporal and causal properties; participants via CRM |
| Performance | E7 Activity | Actors, place, date, production |
| Author (Shakespeare) | E21 Person | Birth/death as E67/E69 (or as events per CRM patterns) |
| Theatre (Globe, etc.) | E53 Place + E40 Legal Body | Place + institutional actor |
| Adaptation (film, translation) | E73 Information Object | Derived from / references original |
| Motif (madness, betrayal) | E55 Type | Applied to events via P2 has type |
| Manuscript / draft | E22 Human-Made Object | Provenance chain |

## LinkML schema strategy

CIDOC alignment is defined in **LinkML YAML**, which compiles to:

- OWL/Turtle for Oxigraph  
- JSON Schema for API validation  
- Python dataclasses (or Pydantic) for ingestion  

**One source of truth:** [schemas/shakespeare_crm.yaml](../schemas/shakespeare_crm.yaml). **Never edit generated OWL by hand** — see [ontology/README.md](../ontology/README.md).

### Compiler workflow (uv + LinkML CLIs)

The project follows the [LinkML tutorial](https://linkml.io/linkml/intro/tutorial.html) pattern: **edit YAML → run standard tools** (`gen-json-schema`, `linkml-validate`, `linkml-convert`, `gen-owl`). Dependencies come from [`pyproject.toml`](../pyproject.toml) (`uv sync`).

CIDOC anchors are mixin classes (`E73_Information_Object`, `E39_Actor`, …) reused by Shakespeare domain classes; property IRIs reuse real CRM predicates where modeled (e.g. `p11_had_participant` → `crm:P11_had_participant`). See [`schemas/shakespeare_crm.yaml`](../schemas/shakespeare_crm.yaml).

```bash
uv sync
uv run gen-json-schema schemas/shakespeare_crm.yaml -o ontology/shakespeare_crm.schema.json    # optional
uv run linkml-validate -s schemas/shakespeare_crm.yaml -C Work schemas/examples/sample_work.yaml
uv run generate-ontology   # convenience: gen-owl → ontology/*.ttl and *.owl
```

Full commands and RDF instance conversion (`linkml-convert`) are spelled out in [ontology/README.md](../ontology/README.md).

### Design decisions (targets)

- Fictional characters: subclass of E39 Actor with `is_fictional: boolean` (or equivalent).
- Dramatic events: subclass or profile of E5 with `motif_type` (or link to E55).
- Textual works: `textual_content` or external full-text index linked by URI (graph models structure, not every line).
- Adaptation: **derivation chain**, not only direct `adapted_from` — support chains of adaptations.

### File layout

- **`schemas/shakespeare_crm.yaml`** — **master LinkML (YAML); edit this first** — CRM mixin anchors + Shakespeare classes  
- `schemas/extensions/` — optional domain extensions (motifs, fictional actors, adaptations)  
- `schemas/examples/` — tiny YAML instances for **`linkml-validate`** / **`linkml-convert`**  
- `src/shakespeare_tools/ontology_gen.py` — thin wrapper calling **`gen-owl`** (`uv run generate-ontology`; matches LinkML CLI usage)  
- `ontology/` — **generated only** — `.owl` / `.ttl`; no YAML here; do not edit by hand ([`ontology/README.md`](../ontology/README.md))

---

*For known modeling traps (textual versions, historical vs fictional), see [PITFALLS.md](PITFALLS.md).*
