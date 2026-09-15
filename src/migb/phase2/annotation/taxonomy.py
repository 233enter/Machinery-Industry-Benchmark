"""Load and fingerprint the reviewed Benchmark Taxonomy snapshot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class TaxonomySnapshotError(ValueError):
    """Raised when a Taxonomy snapshot is malformed or tampered with."""


@dataclass(frozen=True)
class TaxonomyDomain:
    domain_id: str
    domain_name: str
    definition: str
    in_scope_examples: tuple[str, ...]
    boundary_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_name": self.domain_name,
            "definition": self.definition,
            "in_scope_examples": list(self.in_scope_examples),
            "boundary_notes": list(self.boundary_notes),
        }


@dataclass(frozen=True)
class TaxonomySnapshot:
    taxonomy_revision: str
    source_document: str
    source_commit: str
    payload_hash: str
    domains: tuple[TaxonomyDomain, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "taxonomy_revision": self.taxonomy_revision,
            "source_document": self.source_document,
            "source_commit": self.source_commit,
            "domains": [domain.to_dict() for domain in self.domains],
        }


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def taxonomy_payload_hash(snapshot: TaxonomySnapshot) -> str:
    """Return the hash over snapshot content excluding the stored hash field."""

    return hashlib.sha256(_canonical_json_bytes(snapshot.payload())).hexdigest()


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TaxonomySnapshotError(f"{key} must be a non-empty string")
    return value


def load_taxonomy_snapshot(path: str | Path) -> TaxonomySnapshot:
    """Load a YAML snapshot and verify its source metadata and payload hash."""

    snapshot_path = Path(path)
    try:
        with snapshot_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except OSError as exc:
        raise TaxonomySnapshotError(f"cannot read taxonomy snapshot {snapshot_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise TaxonomySnapshotError(
            f"invalid YAML in taxonomy snapshot {snapshot_path}: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise TaxonomySnapshotError("taxonomy snapshot root must be a mapping")
    taxonomy_revision = _required_string(raw, "taxonomy_revision")
    source_document = _required_string(raw, "source_document")
    source_commit = _required_string(raw, "source_commit")
    stored_hash = _required_string(raw, "payload_hash")
    raw_domains = raw.get("domains")
    if not isinstance(raw_domains, list):
        raise TaxonomySnapshotError("domains must be a list")

    domains: list[TaxonomyDomain] = []
    for index, raw_domain in enumerate(raw_domains):
        if not isinstance(raw_domain, dict):
            raise TaxonomySnapshotError(f"domains[{index}] must be a mapping")
        domain_id = _required_string(raw_domain, "domain_id")
        domain_name = _required_string(raw_domain, "domain_name")
        definition = _required_string(raw_domain, "definition")
        examples = raw_domain.get("in_scope_examples")
        notes = raw_domain.get("boundary_notes")
        if not isinstance(examples, list) or not examples or any(
            not isinstance(value, str) or not value.strip() for value in examples
        ):
            raise TaxonomySnapshotError(
                f"domains[{index}].in_scope_examples must be a non-empty string list"
            )
        if not isinstance(notes, list) or any(
            not isinstance(value, str) or not value.strip() for value in notes
        ):
            raise TaxonomySnapshotError(
                f"domains[{index}].boundary_notes must be a string list"
            )
        domains.append(
            TaxonomyDomain(
                domain_id=domain_id,
                domain_name=domain_name,
                definition=definition,
                in_scope_examples=tuple(examples),
                boundary_notes=tuple(notes),
            )
        )

    expected_ids = tuple(f"D{index:02d}" for index in range(1, 13))
    actual_ids = tuple(domain.domain_id for domain in domains)
    if actual_ids != expected_ids:
        raise TaxonomySnapshotError(
            f"taxonomy snapshot must contain D01-D12 in order; got {actual_ids}"
        )
    if len(set(actual_ids)) != len(actual_ids):  # pragma: no cover - covered by order check
        raise TaxonomySnapshotError("taxonomy domain IDs must be unique")

    snapshot = TaxonomySnapshot(
        taxonomy_revision=taxonomy_revision,
        source_document=source_document,
        source_commit=source_commit,
        payload_hash=stored_hash,
        domains=tuple(domains),
    )
    actual_hash = taxonomy_payload_hash(snapshot)
    if stored_hash != actual_hash:
        raise TaxonomySnapshotError(
            f"taxonomy payload hash mismatch: {stored_hash} != {actual_hash}"
        )
    return snapshot
