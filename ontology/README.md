# Generated ontology artifacts

## Where is the LinkML YAML?

**Author everything here:** [`schemas/shakespeare_crm.yaml`](../schemas/shakespeare_crm.yaml).

That YAML is the **single source of truth** (tutorial-style: imports `linkml:types`, then `classes:` / `slots:`). CIDOC CRM 7.x is wired in via **mixin anchors** (`E73_Information_Object`, `E39_Actor`, …) with vocabulary prefix `crm:` plus Shakespeare classes under `sc:`.

This **`ontology/`** directory only receives **generated** `.ttl` and `.owl`.

## LinkML workflows (upstream tutorial parity)

[`uv`](https://docs.astral.sh/uv/) installs the **`linkml`** package (`uv sync`). Use the bundled CLIs the same way the LinkML docs do:

### 1. JSON Schema from the schema (API / validation)

```bash
uv sync
uv run gen-json-schema schemas/shakespeare_crm.yaml -o ontology/shakespeare_crm.schema.json
```

(JSON under `ontology/` is gitignored by default.)

### 2. Validate tabular/YAML instances

```bash
uv run linkml-validate -s schemas/shakespeare_crm.yaml -C Work schemas/examples/sample_work.yaml
```

### 3. Convert instance YAML → RDF (Turtle), like `linkml-convert` in the tutorial

```bash
uv run linkml-convert -s schemas/shakespeare_crm.yaml -C Work -t ttl \
  schemas/examples/sample_work.yaml -o /tmp/hamlet_work.ttl
```

Instance `id` values should be **expanded CURIEs** (e.g. `sc:hamlet`) so RDF URI minting works.

### 4. OWL / Turtle **schema** (TBox) for Oxigraph or WIDoC

Convenience wrapper (calls `gen-owl` twice; uses `--no-use-native-uris` so declared `crm:` slot IRIs such as `P11_had_participant` appear in the graph):

```bash
uv run generate-ontology
```

Equivalent by hand:

```bash
uv run gen-owl schemas/shakespeare_crm.yaml --no-use-native-uris -o ontology/shakespeare_crm.ttl -f ttl
uv run gen-owl schemas/shakespeare_crm.yaml --no-use-native-uris -o ontology/shakespeare_crm.owl -f xml
```

**Do not hand-edit** `shakespeare_crm.ttl` / `shakespeare_crm.owl`. Change the LinkML YAML, then rerun the commands above.

[`../.gitignore`](../.gitignore) excludes `ontology/*.owl`, `ontology/*.ttl`, and `ontology/*.json` so local builds stay out of git until you publish artifacts from CI.
