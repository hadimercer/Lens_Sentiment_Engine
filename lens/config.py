"""Application configuration and runtime constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_ALLOWED_MODELS = ("gpt-5-mini", "gpt-4o-mini", "gpt-5")


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    openai_api_key: str | None
    created_by: str
    openai_model: str = DEFAULT_OPENAI_MODEL
    admin_run_password: str | None = None
    allowed_models: tuple[str, ...] = DEFAULT_ALLOWED_MODELS
    max_batch_size: int = 10_000
    warn_batch_size: int = 500
    extra_confirm_batch_size: int = 1_000
    retry_count: int = 2
    db_connect_timeout: int = 5

    @property
    def app_mode(self) -> str:
        return "live" if self.openai_api_key else "demo"

    @property
    def admin_auth_enabled(self) -> bool:
        return bool(self.admin_run_password)

    @property
    def live_runs_locked(self) -> bool:
        return self.app_mode == "live" and self.admin_auth_enabled

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



def _build_allowed_models(primary_model: str) -> tuple[str, ...]:
    ordered = [primary_model] + [model for model in DEFAULT_ALLOWED_MODELS if model != primary_model]
    return tuple(dict.fromkeys(ordered))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    configured_model = (os.getenv("OPENAI_MODEL") or "").strip() or DEFAULT_OPENAI_MODEL
    return Settings(
        database_url=os.getenv("DATABASE_URL") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        created_by=os.getenv("LENS_CREATED_BY", "Lens Portfolio Analyst"),
        openai_model=configured_model,
        admin_run_password=os.getenv("LENS_ADMIN_PASSWORD") or None,
        allowed_models=_build_allowed_models(configured_model),
    )



def estimate_api_calls(record_count: int) -> int:
    """Estimate record-level calls plus theme and summary calls."""
    return max(record_count, 0) + 2
