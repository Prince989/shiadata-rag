"""
Centralised, validated configuration.

Everything that used to be a bare os.getenv() call or a hardcoded model id
lives here. Settings are read once and cached, so import order no longer
determines whether a key is visible (previously HadithService only worked
because retrieval_pipeline.py happened to call load_dotenv() first).
"""

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.paths import CHROMA_DIR, PROJECT_ROOT

ENV_FILE = PROJECT_ROOT / ".env"

_GOOGLE_KEY_PATTERN = re.compile(r"^GOOGLE_API_KEY(\d*)$")


def _collect_google_keys(env_file: Path) -> list[str]:
    """
    Gather GOOGLE_API_KEY, GOOGLE_API_KEY1..N into an ordered, de-duplicated list.

    Reads the .env file *and* the process environment, because pydantic-settings
    parses the .env itself without exporting anything into os.environ -- so
    scanning os.environ alone silently finds nothing.

    De-duplication is deliberate: the pool is currently populated with the same
    key repeated under several names, which makes round-robin pure theatre while
    looking like real capacity. Collapsing duplicates makes the true pool size
    visible in the startup log.
    """
    sources: dict[str, str] = {}
    if env_file.exists():
        sources.update(
            {k: v for k, v in dotenv_values(env_file, encoding="utf-8-sig").items() if v}
        )
    # Real environment variables take precedence over the .env file.
    sources.update(os.environ)

    found: dict[int, str] = {}
    for name, value in sources.items():
        match = _GOOGLE_KEY_PATTERN.match(name)
        if not match or not value or not value.strip():
            continue
        index = int(match.group(1)) if match.group(1) else 0
        found[index] = value.strip()

    ordered: list[str] = []
    seen: set[str] = set()
    for index in sorted(found):
        key = found[index]
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8-sig",  # the .env carries a BOM
        extra="ignore",
        case_sensitive=False,
    )

    # --- Credentials -----------------------------------------------------
    # Required. Every collection was embedded with an OpenAI model, so without
    # this the service boots happily and then 401s on the first query. Failing
    # at startup instead is the whole point.
    openai_api_key: str = Field(..., min_length=10)

    # Populated in the validator below from GOOGLE_API_KEY*.
    google_api_keys: list[str] = Field(default_factory=list)

    # Shared secret for the NestJS -> Python hop. When unset every guarded
    # route returns 503 rather than silently running unauthenticated.
    internal_api_key: str | None = None

    # --- Server ----------------------------------------------------------
    host: str = "127.0.0.1"
    port: int = 8000
    environment: Literal["development", "production"] = "development"
    reload: bool = False
    thread_pool_size: int = Field(default=24, ge=1, le=200)

    # --- Storage ---------------------------------------------------------
    chroma_dir: Path = CHROMA_DIR

    # --- Models ----------------------------------------------------------
    embedding_model: str = "text-embedding-3-small"
    theology_llm_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-3.5-flash"

    # --- Retrieval defaults ---------------------------------------------
    theology_top_k: int = Field(default=7, ge=1, le=50)
    theology_fetch_k: int = Field(default=30, ge=1, le=200)
    theology_lambda_mult: float = Field(default=0.5, ge=0.0, le=1.0)

    # --- Logging ---------------------------------------------------------
    log_level: str = "INFO"
    log_retrieved_chunks: bool = False

    @model_validator(mode="after")
    def _load_google_keys(self) -> "Settings":
        if not self.google_api_keys:
            # object.__setattr__ avoids re-triggering validation
            object.__setattr__(self, "google_api_keys", _collect_google_keys(ENV_FILE))
        return self

    @field_validator("chroma_dir")
    @classmethod
    def _resolve_chroma_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else (PROJECT_ROOT / value).resolve()

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "production"

    @property
    def primary_google_key(self) -> str | None:
        return self.google_api_keys[0] if self.google_api_keys else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
