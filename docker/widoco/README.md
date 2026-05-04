# WIDOCO — ontology HTML + WebVOWL

[WIDOCO](https://dgarijo.github.io/WIDOCO/) documents the generated OWL from LinkML (`ontology/shakespeare_crm.owl`). Output is written to **`docs/widoco/`** (gitignored).

## Prerequisites

Produce the OWL file first:

```bash
cd /path/to/shakespeare   # repo root
uv sync
uv run generate-ontology
```

## Generate static docs only

From the **`docker/`** directory (Compose resolves `../ontology` / `../docs` correctly):

```bash
docker compose --profile docs build widoco-generate
docker compose --profile docs run --rm widoco-generate
```

Then open `docs/widoco/index-en.html` in a browser or use **`file://`** (some WebVOWL features prefer HTTP).

## Serve at http://localhost:8080

Regenerates docs on each start, then serves them with nginx:

```bash
cd docker
docker compose --profile docs up --build widoco
```

- Main doc: [http://localhost:8080/](http://localhost:8080/) (serves `index-en.html`)
- WebVOWL embedded bundle: [http://localhost:8080/webvowl/index.html](http://localhost:8080/webvowl/index.html)

If port **8080** is busy, edit the `ports` mapping in [`../docker-compose.yml`](../docker-compose.yml) (e.g. `8081:80`).

## CI

Regenerate when `ontology/*.owl` changes — see [docs/PUBLISHING.md](../../docs/PUBLISHING.md).
