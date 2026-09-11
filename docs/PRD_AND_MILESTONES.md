# ShakespeareCRM Prototype: PRD and Milestones

## Product Requirements Document (PRD)

### Problem Statement
Existing resources for exploring Shakespeare's works fall into two broad buckets: full-text repositories (Folger, MIT HTML, Project Gutenberg) and unstructured databases (Wikidata). Neither supports rich, semantic queries based on the dramatic and structural elements of the texts (such as "trace instances of betrayal across all tragedies"). ShakespeareCRM bridges this gap by modeling the narrative events, characters, and structures of the corpus as a unified cultural heritage object using the **CIDOC-CRM** ontology.

### Vision
To build an explorable, queryable, and visualizable history of Shakespeare's complete works, treating fictional narratives as interconnected events. The project allows researchers and enthusiasts to ask graph-shaped questions and see graph-shaped answers.

### Key Features
1. **CIDOC-CRM Semantic Modeling**: A LinkML-defined schema that translates dramatic acts into the CIDOC-CRM ontology.
2. **SPARQL Endpoint (Oxigraph)**: Local semantic database that allows cross-play intelligence and causal reasoning.
3. **IMDB View of Shakespeare**: A prototype UI (Gradio) that lets users view a play’s characters and events interactively.
4. **Visual Graph Explorer**: A D3-based force-directed graph rendering relationships between a play, its characters, and narrative motifs.

### Prototype Scope (v0.1)
The v0.1 prototype successfully models **Hamlet** (Phase 0 seed) and **Macbeth** (Phase 1 parsed data). It provides a Gradio-based interface running on top of a local Oxigraph server, demonstrating both tabular SPARQL results and interactive D3 graph rendering.

---

## Roadmap & Milestones Update

### Milestone 1: Phase 0 Foundation (Completed)
- Set up LinkML schema and CIDOC-CRM alignments.
- Configured Oxigraph graph database.
- Seeded Hamlet ontology and basic character interactions into the graph.

### Milestone 2: Phase 1 Parsing and Curation (Completed)
- Integrated MIT HTML extraction and curation pipeline.
- Extracted and parsed **Macbeth** into structured JSON.
- Ran the semantic curation pipeline and exported Macbeth to CIDOC-CRM triples.
- Loaded all triples into the Oxigraph endpoint.

### Milestone 3: Prototype Interfaces (Completed)
- Expanded the local UI to include the "IMDB View", providing character/event tables per play.
- Embedded a D3 graph component mapping character relationships to narrative motifs visually.

### Milestone 4: Full Corpus Ingestion (Upcoming Phase)
- Parse all 37+ plays from MIT HTML or Folger TEI.
- Run complete LLM-driven curation over the entire corpus.
- Ensure cross-play querying works consistently.

### Milestone 5: NLP and Natural Language Interface (Phase 2+)
- Build the LLM proxy to translate natural language user questions into SPARQL queries.
- Expand visual dashboard (Next.js/React frontend).
