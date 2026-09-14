"""Environment configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an environment configuration is invalid."""


@dataclass(frozen=True)
class SourceRootConfig:
    source_root_id: str
    path: Path
    access_policy: str = "read_only"
    enabled: bool = True

    def snapshot(self) -> dict[str, Any]:
        return {
            "source_root_id": self.source_root_id,
            "path": str(self.path),
            "access_policy": self.access_policy,
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class InventorySettings:
    worker_count: int = 4
    text_page_char_threshold: int = 50

    def __post_init__(self) -> None:
        if self.worker_count < 1:
            raise ConfigError("inventory.worker_count must be positive")
        if self.text_page_char_threshold < 0:
            raise ConfigError("inventory.text_page_char_threshold cannot be negative")

    def snapshot(self) -> dict[str, int]:
        return {
            "worker_count": self.worker_count,
            "text_page_char_threshold": self.text_page_char_threshold,
        }


@dataclass(frozen=True)
class EnvironmentConfig:
    source_roots: tuple[SourceRootConfig, ...]
    migb_data_root: Path
    inventory: InventorySettings
    config_path: Path | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "source_roots": [root.snapshot() for root in self.source_roots],
            "migb_data_root": str(self.migb_data_root),
            "inventory": self.inventory.snapshot(),
        }


_SECRET_KEY_PARTS = ("password", "private_key", "api_key", "token", "secret")


def _reject_secret_keys(value: Any, location: str = "config") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in _SECRET_KEY_PARTS):
                raise ConfigError(f"secret-like configuration key is not allowed: {location}.{key}")
            _reject_secret_keys(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_keys(child, f"{location}[{index}]")


def _require_absolute_path(value: Any, field_name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string")
    path = Path(value)
    if not path.is_absolute():
        raise ConfigError(f"{field_name} must be an absolute path")
    return path


def load_config(path: str | Path) -> EnvironmentConfig:
    """Load and validate an environment YAML file."""

    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except OSError as exc:
        raise ConfigError(f"cannot read config {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")
    _reject_secret_keys(raw)

    raw_roots = raw.get("source_roots")
    if not isinstance(raw_roots, list) or not raw_roots:
        raise ConfigError("source_roots must be a non-empty list")

    roots: list[SourceRootConfig] = []
    seen_ids: set[str] = set()
    for index, raw_root in enumerate(raw_roots):
        if not isinstance(raw_root, dict):
            raise ConfigError(f"source_roots[{index}] must be a mapping")
        source_root_id = raw_root.get("source_root_id")
        if not isinstance(source_root_id, str) or not source_root_id.strip():
            raise ConfigError(f"source_roots[{index}].source_root_id is required")
        if source_root_id in seen_ids:
            raise ConfigError(f"duplicate source_root_id: {source_root_id}")
        seen_ids.add(source_root_id)
        access_policy = raw_root.get("access_policy", "read_only")
        if access_policy != "read_only":
            raise ConfigError(f"{source_root_id}.access_policy must be read_only")
        enabled = raw_root.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ConfigError(f"{source_root_id}.enabled must be boolean")
        roots.append(
            SourceRootConfig(
                source_root_id=source_root_id,
                path=_require_absolute_path(raw_root.get("path"), f"source_roots[{index}].path"),
                access_policy=access_policy,
                enabled=enabled,
            )
        )

    raw_inventory = raw.get("inventory", {})
    if not isinstance(raw_inventory, dict):
        raise ConfigError("inventory must be a mapping")
    worker_count = raw_inventory.get("worker_count", 4)
    threshold = raw_inventory.get("text_page_char_threshold", 50)
    if isinstance(worker_count, bool) or not isinstance(worker_count, int):
        raise ConfigError("inventory.worker_count must be an integer")
    if isinstance(threshold, bool) or not isinstance(threshold, int):
        raise ConfigError("inventory.text_page_char_threshold must be an integer")

    return EnvironmentConfig(
        source_roots=tuple(roots),
        migb_data_root=_require_absolute_path(raw.get("migb_data_root"), "migb_data_root"),
        inventory=InventorySettings(worker_count=worker_count, text_page_char_threshold=threshold),
        config_path=config_path,
    )
