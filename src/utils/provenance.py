"""Helpers shared by every download script.

Every download should call `log_download()` so that data/provenance/downloads.jsonl
records what was fetched, from where, when, and its checksum. That file is small and
IS committed to git, even though the raw data itself is not.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


def repo_root() -> Path:
    """Repo root, assuming this file lives at src/chicago_forecast/utils/provenance.py."""
    return Path(__file__).resolve().parents[3]


def load_config(name: str) -> dict:
    """Load config/<name>.yml, e.g. load_config('geography')."""
    path = repo_root() / "config" / f"{name}.yml"
    with open(path) as f:
        return yaml.safe_load(f)


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def log_download(
    *,
    source: str,
    url: str,
    params: dict | None,
    out_path: Path,
    notes: str = "",
    log_path: Path | None = None,
) -> dict:
    """Append one JSON line describing a downloaded file.

    Never put API keys in `url` or `params`; strip them before calling.
    """
    root = repo_root()
    log_path = log_path or root / "data" / "provenance" / "downloads.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        rel = str(out_path.resolve().relative_to(root))
    except ValueError:
        rel = str(out_path)

    record = {
        "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "url": url,
        "params": params or {},
        "file": rel,
        "sha256": sha256_file(out_path),
        "bytes": out_path.stat().st_size,
        "notes": notes,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record
