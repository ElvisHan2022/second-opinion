"""Public lane: load hand-collected posts from data/fixtures/public_posts.json.

Optional live Reddit search is out of scope for M1.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.schemas import Source, validate_source

POSTS = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "public_posts.json"


def load_posts(path: Path = POSTS) -> list[Source]:
    data = json.loads(path.read_text(encoding="utf-8"))
    sources = [validate_source(p) for p in data["posts"]]
    ids = [s.id for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("public_posts.json: duplicate post ids")
    for s in sources:
        if s.lane != "public":
            raise ValueError(f"{s.id}: lane must be public")
    return sources
