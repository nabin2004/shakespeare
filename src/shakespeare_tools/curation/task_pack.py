"""Load task pack YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from shakespeare_tools.curation.models import TaskPack


def load_task_pack(path: Path | str) -> TaskPack:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Task pack must be a mapping: {p}")
    return TaskPack.model_validate(data)
