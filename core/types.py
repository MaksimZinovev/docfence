"""
Loads document type definitions from .docfence/types/*.toml.
Falls back to a minimal built-in default if no definition exists.
"""

import tomllib
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class TypeDef:
    name: str
    statuses: list[str] = field(default_factory=lambda: ["draft", "active", "frozen", "done"])
    required_fields: list[str] = field(default_factory=lambda: ["id", "status", "owner"])
    defaults: dict = field(default_factory=dict)
    source: str = "built-in"


_FALLBACK = TypeDef(name="unknown")


def find_types_dir(start: Path) -> Path | None:
    """Walk up from start (and CWD) looking for .docfence/types/."""
    search_roots = {start.resolve(), Path.cwd().resolve()}
    for root in search_roots:
        for parent in [root, *root.parents]:
            candidate = parent / ".docfence" / "types"
            if candidate.is_dir():
                return candidate
    return None


def load_types(start: Path) -> dict[str, TypeDef]:
    types: dict[str, TypeDef] = {}
    types_dir = find_types_dir(start)
    if not types_dir:
        return types
    for toml_file in types_dir.glob("*.toml"):
        with open(toml_file, "rb") as f:
            raw = tomllib.load(f)
        name = raw.get("name", toml_file.stem)
        types[name] = TypeDef(
            name=name,
            statuses=raw.get("statuses", _FALLBACK.statuses),
            required_fields=raw.get("required_fields", _FALLBACK.required_fields),
            defaults=raw.get("defaults", {}),
            source=str(toml_file),
        )
    return types


def resolve_type(name: str, registry: dict[str, TypeDef]) -> TypeDef | None:
    return registry.get(name)
