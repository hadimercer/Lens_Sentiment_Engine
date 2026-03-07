"""Application configuration and runtime constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    openai_api_key: str | None
    created_by: str
    max_batch_size: int = 10_000
    warn_batch_size: int = 500
    extra_confirm_batch_size: int = 1_000
    retry_count: int = 2
    db_connect_timeout: int = 5

    @property
    def app_mode(self) -> str:
        return "live" if self.openai_api_key else "demo"

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def artifacts_dir(self) -> Path:
        return self.project_root / "docs" / "artifacts"

    @property
    def schema_path(self) -> Path:
        return self.artifacts_dir / "lens_schema.sql"

    @property
    def seed_path(self) -> Path:
        return self.artifacts_dir / "lens_seed.sql"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        created_by=os.getenv("LENS_CREATED_BY", "Lens Portfolio Analyst"),
    )


def estimate_api_calls(record_count: int) -> int:
    """Estimate record-level calls plus theme and summary calls."""
    return max(record_count, 0) + 2
