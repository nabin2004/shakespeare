# System architecture

The system has four layers. Each layer has one job; interfaces stay explicit and minimal.

| Layer | Components | Responsibility |
|-------|-------------|----------------|
| **UI** | Next.js 15 App Router, YASGUI, D3.js | NL query box, SPARQL editor, graph canvas, motif explorer, adaptation timeline |
| **API** | FastAPI, NL-to-SPARQL | SPARQL proxy (CORS, auth), translation, narration, validation, read-only public policy |
| **Store** | Oxigraph | SPARQL 1.1; named graphs for ontology / data / inference; persistence; optional `SERVICE` federation |
| **Schema** | LinkML → OWL, JSON Schema, Python | Single SoT; CIDOC-CRM alignment + Shakespeare extensions; WIDoC consumes OWL |

## Layer diagram

```mermaid
flowchart TB
  subgraph LayerUI [Layer_UI]
    NextJS[Nextjs_AppRouter]
    YASGUI[YASGUI_embedded]
    D3[D3_graphViewer]
  end
  subgraph LayerAPI [Layer_API]
    FastAPI[FastAPI]
    NL[NL_to_SPARQL]
    Val[Query_validator]
  end
  subgraph LayerStore [Layer_Store]
    Oxi[Oxigraph]
  end
  subgraph LayerSchema [Layer_Schema]
    LML[LinkML]
    OWL[OWL_Turtle]
  end
  LML --> OWL
  OWL --> Oxi
  NextJS --> FastAPI
  YASGUI --> FastAPI
  FastAPI --> Val
  Val --> Oxi
  NL --> FastAPI
  D3 --> NextJS
```

## Natural language query sequence

```mermaid
sequenceDiagram
  participant U as User
  participant F as Frontend
  participant A as FastAPI
  participant L as LLM
  participant X as Oxigraph
  U->>F: Natural_language
  F->>A: POST_question
  A->>L: Generate_SPARQL_schema_aware
  L-->>A: SPARQL_string
  A->>A: Parse_validate_SPARQL
  A->>X: Execute_QUERY
  X-->>A: Binding_rows_RDF
  A->>L: Narrate_bindings_only
  L-->>A: Explanatory_text
  A-->>F: JSON_results_plus_narration
  F-->>U: Table_and_graph
```

## Named graphs

From Phase 0 onward, **separate**:

- Ontology graph (TBox / CRM alignment)  
- Instance data graph(s) (ABox)  
- Inferred material (if materialized) — optional graph

Exact IRIs should be documented in the schema repo and repeated in ingestion scripts so queries can use `GRAPH` clauses for provenance and partial updates.

## External services

- **Wikidata** and other SPARQL endpoints via `SERVICE` where appropriate (Phase 1+), with clear timeouts and caching policy later if needed.

---

*Roadmap: [ROADMAP.md](ROADMAP.md). Agent constraints: [AGENTS.md](../AGENTS.md).*
