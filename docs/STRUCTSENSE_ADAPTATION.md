# STRUCTSENSE ideas adapted for ShakespeareCRM

This document maps [STRUCTSENSE: A task-agnostic agentic framework for structured information extraction with human-in-the-loop evaluation and benchmarking](https://arxiv.org/abs/2507.03674) (Chhetri et al., arXiv:2507.03674v2) to **ShakespeareCRM** KG curation, and records deliberate departures.

## What we adopt (conceptual alignment)

| Paper element | Where in STRUCTSENSE | Use here |
|---------------|---------------------|----------|
| Multi-agent decomposition | Fig. 1, §3 | **Extractor → Alignment → Judge → (human) Feedback** as discrete stages; orchestrated with [Pydantic AI](https://ai.pydantic.dev/) instead of Crew.AI. |
| Ontology-guided alignment | §3 Alignment agent; Table 1 (polysemy) | Ground mentions in **`sc:` / CIDOC** TBox; enforce domain disambiguation (work vs fictional character vs historical person) per [PITFALLS.md](PITFALLS.md). |
| LLM-as-judge + confidence | §3 Judge agent (score 0–1) | Judge scores are **gates** for human review, not shipping criteria. |
| Human-in-the-loop | §3 Feedback agent; §5–§7 | Review JSON alongside each run; corrections merge into the draft before Turtle export. |
| Shared execution context | §4 (memory modules in their stack) | **`CurationContext`**: passage IDs, TEI anchors, prior extractions; injected via Pydantic AI deps. |
| Task + agent configuration | §3 (separate configs) | **Task packs** (YAML): play scope, target classes, prompts; separate from model/API settings. |
| Evaluation framing | §5 (precision/recall/F1; mixed NER evaluation) | Golden tests on small fixtures; optional future annotator review workflow (AIProofBuddy-style flags: correct/incorrect/missing). |

## What we do not adopt (replacement rationale)

| Paper implementation | Replacement here |
|------------------------|------------------|
| **Crew.AI** (§4) | **Pydantic AI** — typed dependencies, structured outputs, fits this repo’s Python stack. |
| **GROBID / PDF APIs** (§4) | **Folger TEI** (and optional [MIT HTML](../src/shakespeare_tools/mit_html/) tooling) as canonical dramatic text sources — not scholarly PDFs. |
| **Weaviate** for ontology vectors (§4) | **Default:** in-process label index over generated OWL/Turtle + optional **read-only SPARQL** to Oxigraph. Vector/hybrid retrieval can plug in later behind the same alignment interface. |
| **Neuroscience ontology set** (Uberon, ADO, …) | **Shakespeare CRM** TBox (`schemas/shakespeare_crm.yaml` → OWL) and CIDOC CRM anchors. |

## Citations (for provenance)

When citing the framework in papers or dataset documentation, use the arXiv identifier above. Internal code comments may refer to this file as **`STRUCTSENSE_ADAPTATION`**.

## Related project rules

- LinkML remains the single source of truth: [AGENTS.md](../AGENTS.md).
- Do not hand-edit generated ontology files under `ontology/`.
- Public deploys stay read-only on the graph store; curation merges go through validated server-side or operator workflows — see [CURATION_PIPELINE.md](CURATION_PIPELINE.md).
