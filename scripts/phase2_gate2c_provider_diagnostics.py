#!/usr/bin/env python3
"""Run the bounded historical Gate 2C Provider diagnostics without Benchmark annotation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from migb.phase2.annotation.adapters import GLMRelayAnnotationAdapter
from migb.phase2.annotation.preflight import (
    ProviderPreflightResult,
    load_provider_environment,
    owner_verified_model_discovery,
    run_provider_preflight,
    synthetic_annotation_request,
    synthetic_identity_probe,
)
from migb.phase2.annotation.taxonomy import load_taxonomy_snapshot


DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/phase2/gate2c_annotation_v0.1.yaml"
DEFAULT_TAXONOMY = REPOSITORY_ROOT / "configs/phase2/taxonomy_annotation_v0.1.yaml"
DEFAULT_PROVIDER_ENV_FILE = REPOSITORY_ROOT / "configs/phase2/gate2c_provider.local.env"
IDENTITY_CANDIDATES = ("glm-5.1", "glm-4.7", "glm-5.3-flash")
HISTORICAL_REJECTED_B_MODEL = "glm-5.2"


def _adapter_from_config(label: str, raw: dict[str, Any]) -> GLMRelayAnnotationAdapter:
    if raw.get("provider") != "glm_relay":
        raise ValueError(f"annotator {label} must use glm_relay for this diagnostic")
    return GLMRelayAnnotationAdapter(
        annotator_id=raw["annotator_id"],
        annotation_pass=label,
        model=raw["model"],
        api_key_env=raw["api_key_env"],
        base_url_env=raw["base_url_env"],
    )


def _attempt_summary(attempt: Any) -> dict[str, Any]:
    return {
        "annotator_id": attempt.annotator_id,
        "provider": attempt.provider,
        "requested_model": attempt.requested_model,
        "mode": attempt.mode,
        "http_success": attempt.http_success,
        "http_status": attempt.http_status,
        "resolved_model": attempt.resolved_model,
        "model_match": attempt.model_match,
        "schema_valid": attempt.schema_valid,
        "mode_usable": attempt.mode_usable,
        "unsupported_response_format": attempt.unsupported_response_format,
        "failure_category": attempt.failure_category,
        "validation_error_field": attempt.validation_error_field,
        "validation_error_type": attempt.validation_error_type,
        "validation_error_message": attempt.validation_error_message,
        "request_id": attempt.request_id,
        "input_tokens": attempt.input_tokens,
        "output_tokens": attempt.output_tokens,
        "reasoning_tokens": attempt.reasoning_tokens,
        "latency_ms": attempt.latency_ms,
        "passed": attempt.passed,
    }


def _provider_summary(result: ProviderPreflightResult) -> dict[str, Any]:
    return {
        "annotator_id": result.annotator_id,
        "provider": result.provider,
        "requested_model": result.requested_model,
        "model_discovery_source": result.discovery.discovery_source,
        "requested_model_accessible": result.discovery.requested_model_accessible,
        "structured_output_mode": result.structured_output_mode,
        "passed": result.passed,
        "error_type": result.error_type,
        "attempts": [_attempt_summary(attempt) for attempt in result.attempts],
    }


def _identity_summary(result: Any) -> dict[str, Any]:
    return {
        "provider": result.provider,
        "annotator_id": result.annotator_id,
        "candidate_model": result.requested_model,
        "http_success": result.http_success,
        "http_status": result.http_status,
        "resolved_model": result.resolved_model,
        "model_match": result.model_match,
        "exact_match": result.passed,
        "failure_category": result.failure_category,
        "error_type": result.error_type,
        "request_id": result.request_id,
        "latency_ms": result.latency_ms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument(
        "--provider-env-file",
        type=Path,
        default=Path(os.environ.get("MIGB_PROVIDER_ENV_FILE", DEFAULT_PROVIDER_ENV_FILE)),
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    raw_config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw_config, dict):
        raise ValueError("Gate 2C configuration must be a mapping")
    raw_annotators = raw_config.get("annotators")
    execution = raw_config.get("execution")
    if not isinstance(raw_annotators, dict) or not isinstance(execution, dict):
        raise ValueError("Gate 2C configuration is missing annotators or execution")
    if execution.get("model_discovery_source") != "owner_verified":
        raise ValueError("Provider diagnostics require owner-verified model discovery")

    adapter_a = _adapter_from_config("a", raw_annotators["a"])
    current_b_raw = raw_annotators["b"]
    adapter_b = GLMRelayAnnotationAdapter(
        annotator_id=current_b_raw["annotator_id"],
        annotation_pass="b",
        model=HISTORICAL_REJECTED_B_MODEL,
        api_key_env=current_b_raw["api_key_env"],
        base_url_env=current_b_raw["base_url_env"],
    )
    taxonomy = load_taxonomy_snapshot(args.taxonomy)
    request = synthetic_annotation_request(taxonomy.taxonomy_revision)
    environment = load_provider_environment(args.provider_env_file, os.environ)
    verified_models = tuple(execution.get("owner_verified_models", ()))
    discovery_a = owner_verified_model_discovery(
        adapter_a,
        verified_models,
        environ=environment,
    )
    result_a = run_provider_preflight(
        adapter_a,
        request,
        taxonomy,
        environ=environment,
        timeout=args.timeout,
        discovery=discovery_a,
    )

    identity_results: list[dict[str, Any]] = []
    first_exact_match: str | None = None
    for candidate in IDENTITY_CANDIDATES:
        candidate_adapter = GLMRelayAnnotationAdapter(
            annotator_id="annotator_b_identity_probe",
            annotation_pass="b",
            model=candidate,
            api_key_env="GLM_API_KEY",
            base_url_env="GLM_BASE_URL",
        )
        identity = synthetic_identity_probe(
            candidate_adapter,
            environ=environment,
            timeout=args.timeout,
        )
        identity_results.append(_identity_summary(identity))
        if identity.passed:
            first_exact_match = candidate
            break

    summary = {
        "config_revision": raw_config.get("annotation_revision"),
        "prompt_revision": raw_config.get("prompt_revision"),
        "schema_revision": raw_config.get("schema_revision"),
        "taxonomy_revision": raw_config.get("taxonomy_revision"),
        "credential_presence": {
            "GLM_API_KEY": bool(environment.get("GLM_API_KEY")),
        },
        "transport_security": adapter_a.transport_security(environment),
        "model_discovery_source": "owner_verified",
        "annotator_a": _provider_summary(result_a),
        "historical_rejected_annotator_b": {
            "requested_model": adapter_b.model,
            "status": "blocked_by_confirmed_model_substitution",
            "formal_schema_preflight": "not_rerun",
        },
        "identity_candidates": identity_results,
        "first_exact_match_candidate": first_exact_match,
        "recommended_b_candidate": first_exact_match,
        "gate2c_b_provider_preflight": "BLOCKED BY PROVIDER PREFLIGHT",
        "twenty_item_dry_run_authorized": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
