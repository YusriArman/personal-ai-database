"""Find markdown files in a vault. Read-only: nothing here ever writes to the vault."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules"}


@dataclass(frozen=True)
class VaultFile:
    rel_path: str  # POSIX-style path relative to the vault root
    text: str
    content_hash: str
    mtime: float


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_vault(vault: Path) -> list[VaultFile]:
    if not vault.is_dir():
        raise FileNotFoundError(f"Vault folder not found: {vault}")
    files: list[VaultFile] = []
    for path in sorted(vault.rglob("*.md")):
        rel = path.relative_to(vault)
        if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts[:-1]):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        files.append(
            VaultFile(
                rel_path=rel.as_posix(),
                text=text,
                content_hash=hash_text(text),
                mtime=path.stat().st_mtime,
            )
        )
    return files
