from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_csv_rows(path: str) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]
