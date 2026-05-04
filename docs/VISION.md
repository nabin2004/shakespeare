# Vision and concept

**ShakespeareCRM** — v0.1

ShakespeareCRM is not a chatbot. It is not another “ask Shakespeare questions” toy. It is a **queryable, explorable, semantically rich knowledge system** that models William Shakespeare’s complete body of work — plays, poems, characters, performances, manuscripts, and adaptations — as formal **cultural heritage objects** using the **CIDOC-CRM** ontology.

The central premise: **literature has structure.** Characters betray each other in patterns. Themes recur across decades. Performances link manuscripts to audiences across centuries. Once modeled formally, these structures become queryable, visualizable, and extensible in ways that plain text never can be.

## Why this project

Shakespeare’s works are among the most densely cross-referenced objects in cultural heritage — characters, events, performances, manuscripts, adaptations, and interpretations spanning 400+ years. That density makes it a strong stress-test for CIDOC-CRM and a compelling demonstration of what knowledge graphs can do for literary corpora.

## The core problem

Existing resources fall into two buckets: full-text repositories (Folger, Project Gutenberg) and structured databases (Wikidata). Neither supports rich **semantic** queries such as:

- Show every act of betrayal involving royalty across all tragedies.
- What chain of events most frequently precedes a Shakespearean death?
- Trace how Hamlet has been adapted from 1603 to 2024.

ShakespeareCRM fills that gap by modeling the **world** of the works — not only the text — as a formal knowledge graph.

## Stack philosophy

Every tool is deliberate:

| Tool | Role | Why not the alternative |
|------|------|-------------------------|
| CIDOC-CRM | Domain ontology | OWL-only can be too abstract; Dublin Core too flat. CRM models events, actors, and physical objects with relationships that match cultural heritage semantics. |
| LinkML | Schema definition | Raw OWL/Turtle is error-prone and hard to version. LinkML is YAML-first and compiles to OWL, JSON Schema, Python, and more. |
| Oxigraph | RDF triple store | Jena is heavy; Virtuoso is complex to deploy. Oxigraph is modern, Rust-based SPARQL 1.1, single binary or WASM. |
| YASGUI | SPARQL interface | Raw endpoints are unusable for most users. YASGUI is the de facto browser standard. |
| WIDoC | Ontology docs | Hand-written docs go stale. WIDoC generates HTML from OWL and tracks the ontology. |

## Project: “Talk to Shakespeare’s world”

The killer product is an **interactive thinking engine**: users explore Shakespeare’s literary world as a **structured graph** — natural language as the interface, SPARQL as the engine, visualization as the output.

### Five killer features

1. **Cross-play intelligence** — Query all works; similar character arcs; recurring dramatic patterns (usurper, poisoner, feigned madman).
2. **Narrative motif tracking** — Motifs as first-class types on events and relationships, not keyword search (“madness” as structural role).
3. **Causal event reasoning** — CIDOC-CRM events support temporal/causal chains (e.g. precursors to death in the corpus).
4. **Adaptation tracing** — Stage, film, translation, retelling as derivations over time.
5. **Dual-mode explanation** — Plain prose for casual users; CRM-accurate detail for researchers — same underlying results.

## LLM integration strategy

The LLM is **constrained**:

1. User asks a natural-language question.
2. LLM converts it to **SPARQL** against the Oxigraph endpoint (with schema-aware prompting).
3. Oxigraph executes the query and returns **RDF results only**.
4. LLM **narrates** those results in natural language.
5. Frontend renders tables and interactive graph views.

### Critical rule

**The LLM translates and narrates. The graph answers. The LLM must not invent facts.** If a query fails or returns no rows, the system must not substitute answers from training data. That grounding is both a safety property and a research stance (structured KG + constrained LLM vs. hallucination-prone RAG).

---

*For ontology mapping and schema strategy, see [ONTOLOGY.md](ONTOLOGY.md).*
