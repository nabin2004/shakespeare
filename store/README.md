# Oxigraph persistence

Local Oxigraph **database files or volumes** should live here at runtime (or as mounted Docker volumes).

Do not commit live store binaries. Add patterns under this path to [.gitignore](../.gitignore) if your deployment uses a subdirectory (e.g. `store/data/`).

Phase 0: define Docker volume mapping in [../docker/docker-compose.yml](../docker/docker-compose.yml).
