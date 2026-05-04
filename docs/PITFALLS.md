# Known hard problems

CIDOC-CRM is powerful; literary + heritage reality stresses the model. Plan for these **before** they become bugs.

## Fictional vs historical conflation

**Hamlet** the character, **Hamlet** the play, and the **historical Prince Amleth** (tradition) are different entities. The ontology must distinguish:

- E21 Person (historical / real persons)  
- E39 Actor or fictional subclass (dramatic character)  
- E73 Information Object (the text / work)

Mixing them corrupts queries that span “character,” “work,” and “history.”

## Multiple text versions

Hamlet has distinct early texts (Q1 1603, Q2 1604, F1 1623) with real textual variance. The model needs:

- Multiple **E22** / **E73** instanciations or versions  
- Version-specific events where they diverge  
- No silent collapse into one “Hamlet” node when scholarship needs separation

## Conflicting historical data

Scholars disagree on dates, performances, and attribution. Prefer:

- Explicit uncertainty (multiple dating events, qualifiers)  
- Argumentation patterns where CRM supports them  
- Avoid a single asserted date when the sources conflict — document provenance instead

## Adaptation depth

Adaptations chain: film ← stage ← translation ← original. Model as a **derivation chain**, not a flat `adapted_from` only — otherwise timeline queries lose depth.

## Graph visualization “spaghetti”

A naive force layout of one play can become a hairball. Plan the UI for:

- **Progressive disclosure** (expand on click)  
- **Filtering** by play, motif, entity type  
- **Level of detail** (summary vs full property bundles)

---

*Architecture context: [ARCHITECTURE.md](ARCHITECTURE.md).*
