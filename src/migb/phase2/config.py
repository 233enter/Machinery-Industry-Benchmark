"""Configuration for the Phase 2 calibration sample and evidence run."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class Phase2ConfigError(ValueError):
    """Raised when a Phase 2 configuration is invalid."""


@dataclass(frozen=True)
class Phase2InputConfig:
    inventory_run_id: str
    inventory_root: Path
    source_root: Path
    migb_data_root: Path


@dataclass(frozen=True)
class Phase2AuditConfig:
    source_quality_exception: str | int = "all"
    text_absent_target: int = 60
    mixed_text_target: int = 40
    filename_unmatched_target: int = 60


@dataclass(frozen=True)
class Phase2SamplingConfig:
    main_target: int = 600
    base_quota_per_parent_group: int = 15
    audit: Phase2AuditConfig = Phase2AuditConfig()


@dataclass(frozen=True)
class Phase2EvidenceConfig:
    page_indices: tuple[int, ...] = (0, 1, 2)
    max_extracted_chars: int = 12000
    worker_count: int = 4


@dataclass(frozen=True)
class Phase2Config:
    input: Phase2InputConfig
    sampling: Phase2SamplingConfig = Phase2SamplingConfig()
    evidence: Phase2EvidenceConfig = Phase2EvidenceConfig()
    config_path: Path | None = None

    def snapshot(self) -> dict[str, Any]:
        """Return the semantic configuration used for fingerprints and manifests."""

        return {
            "input": {
                "inventory_run_id": self.input.inventory_run_id,
                "inventory_root": str(self.input.inventory_root),
                "source_root": str(self.input.source_root),
                "migb_data_root": str(self.input.migb_data_root),
            },
            "sampling": {
                "main_target": self.sampling.main_target,
                "base_quota_per_parent_group": self.sampling.base_quota_per_parent_group,
                "audit": {
                    "source_quality_exception": self.sampling.audit.source_quality_exception,
                    "text_absent_target": self.sampling.audit.text_absent_target,
                    "mixed_text_target": self.sampling.audit.mixed_text_target,
                    "filename_unmatched_target": self.sampling.audit.filename_unmatched_target,
                },
            },
            "evidence": {
                "page_indices": list(self.evidence.page_indices),
                "max_extracted_chars": self.evidence.max_extracted_chars,
                "worker_count": self.evidence.worker_count,
            },
        }

    def fingerprint(self) -> str:
        payload = json.dumps(
            self.snapshot(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


_SECRET_KEY_PARTS = ("password", "private_key", "api_key", "token", "secret")


def _reject_secret_keys(value: Any, location: str = "config") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in _SECRET_KEY_PARTS):
                raise Phase2ConfigError(
                    f"secret-like configuration key is not allowed: {location}.{key}"
                )
            _reject_secret_keys(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_keys(child, f"{location}[{index}]")


def _required_mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise Phase2ConfigError(f"{name} must be a mapping")
    return raw


def _required_string(raw: dict[str, Any], key: str, location: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise Phase2ConfigError(f"{location}.{key} must be a non-empty string")
    return value


def _absolute_path(raw: dict[str, Any], key: str, location: str) -> Path:
    value = _required_string(raw, key, location)
    path = Path(value)
    if not path.is_absolute():
        raise Phase2ConfigError(f"{location}.{key} must be an absolute path")
    return path


def _positive_int(value: Any, location: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise Phase2ConfigError(f"{location} must be a positive integer")
    return value


def load_phase2_config(path: str | Path) -> Phase2Config:
    """Load the Phase 2 YAML configuration without resolving runtime paths."""

    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except OSError as exc:
        raise Phase2ConfigError(f"cannot read config {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise Phase2ConfigError(f"invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise Phase2ConfigError("configuration root must be a mapping")
    _reject_secret_keys(raw)

    raw_input = _required_mapping(raw.get("input"), "input")
    inventory_run_id = _required_string(raw_input, "inventory_run_id", "input")
    inventory_root = _absolute_path(raw_input, "inventory_root", "input")
    source_root = _absolute_path(raw_input, "source_root", "input")
    raw_migb_data_root = raw_input.get("migb_data_root", raw.get("migb_data_root"))
    if not isinstance(raw_migb_data_root, str) or not raw_migb_data_root.strip():
        raise Phase2ConfigError(
            "input.migb_data_root or migb_data_root must be a non-empty string"
        )
    migb_data_root = Path(raw_migb_data_root)
    if not migb_data_root.is_absolute():
        raise Phase2ConfigError("migb_data_root must be an absolute path")

    raw_sampling = _required_mapping(raw.get("sampling", {}), "sampling")
    main_target = _positive_int(raw_sampling.get("main_target", 600), "sampling.main_target")
    base_quota = _positive_int(
        raw_sampling.get("base_quota_per_parent_group", 15),
        "sampling.base_quota_per_parent_group",
    )
    raw_audit = _required_mapping(raw_sampling.get("audit", {}), "sampling.audit")
    exception_target = raw_audit.get("source_quality_exception", "all")
    if exception_target != "all" and not (
        isinstance(exception_target, int)
        and not isinstance(exception_target, bool)
        and exception_target > 0
    ):
        raise Phase2ConfigError(
            "sampling.audit.source_quality_exception must be 'all' or a positive integer"
        )
    audit = Phase2AuditConfig(
        source_quality_exception=exception_target,
        text_absent_target=_positive_int(
            raw_audit.get("text_absent_target", 60),
            "sampling.audit.text_absent_target",
        ),
        mixed_text_target=_positive_int(
            raw_audit.get("mixed_text_target", 40),
            "sampling.audit.mixed_text_target",
        ),
        filename_unmatched_target=_positive_int(
            raw_audit.get("filename_unmatched_target", 60),
            "sampling.audit.filename_unmatched_target",
        ),
    )

    raw_evidence = _required_mapping(raw.get("evidence", {}), "evidence")
    raw_page_indices = raw_evidence.get("page_indices", [0, 1, 2])
    if not isinstance(raw_page_indices, list) or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in raw_page_indices
    ):
        raise Phase2ConfigError("evidence.page_indices must be a list of non-negative integers")
    page_indices = tuple(raw_page_indices)
    if page_indices != (0, 1, 2):
        raise Phase2ConfigError("Gate 2B evidence.page_indices must be exactly [0, 1, 2]")
    evidence = Phase2EvidenceConfig(
        page_indices=page_indices,
        max_extracted_chars=_positive_int(
            raw_evidence.get("max_extracted_chars", 12000),
            "evidence.max_extracted_chars",
        ),
        worker_count=_positive_int(
            raw_evidence.get("worker_count", 4),
            "evidence.worker_count",
        ),
    )

    return Phase2Config(
        input=Phase2InputConfig(
            inventory_run_id=inventory_run_id,
            inventory_root=inventory_root,
            source_root=source_root,
            migb_data_root=migb_data_root,
        ),
        sampling=Phase2SamplingConfig(
            main_target=main_target,
            base_quota_per_parent_group=base_quota,
            audit=audit,
        ),
        evidence=evidence,
        config_path=config_path,
    )
