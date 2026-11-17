"""Runtime settings, read from environment variables.

Everything here is local. There is deliberately no setting for a cloud model:
if Ollama is unreachable the app degrades to keyword search, it does not fall back.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Hardware profiles. Model names are defaults only; see docs/MODEL_SETUP.md for how to
# check what is current in the Ollama library and how to override them.
PROFILES: dict[str, dict[str, str]] = {
    "m4": {"embed_model": "nomic-embed-text", "chat_model": "qwen2.5:7b"},
    "ryzen": {"embed_model": "nomic-embed-text", "chat_model": "llama3.2:3b"},
}


@dataclass(frozen=True)
class Settings:
    vault_path: Path
    db_path: Path
    provider: str  # "ollama" or "fake"
    ollama_url: str
    embed_model: str
    chat_model: str
    profile: str
    # Hybrid-search score below which Q&A refuses to answer. Tuned on the dev split only.
    abstain_threshold: float
    top_k: int


def load_settings() -> Settings:
    profile = os.environ.get("LNC_PROFILE", "m4")
    if profile not in PROFILES:
        raise ValueError(f"LNC_PROFILE must be one of {sorted(PROFILES)}, got {profile!r}")
    defaults = PROFILES[profile]
    return Settings(
        vault_path=Path(os.environ.get("LNC_VAULT", REPO_ROOT / "demo_vault")).expanduser(),
        db_path=Path(os.environ.get("LNC_DB", REPO_ROOT / "data" / "companion.db")).expanduser(),
        provider=os.environ.get("LNC_PROVIDER", "ollama"),
        ollama_url=os.environ.get("LNC_OLLAMA_URL", "http://127.0.0.1:11434"),
        embed_model=os.environ.get("LNC_EMBED_MODEL", defaults["embed_model"]),
        chat_model=os.environ.get("LNC_CHAT_MODEL", defaults["chat_model"]),
        profile=profile,
        abstain_threshold=float(os.environ.get("LNC_ABSTAIN_THRESHOLD", "0.35")),
        top_k=int(os.environ.get("LNC_TOP_K", "5")),
    )
