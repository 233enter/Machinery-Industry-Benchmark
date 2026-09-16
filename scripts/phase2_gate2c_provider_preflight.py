#!/usr/bin/env python3
"""Run the Gate 2C dual-provider capability preflight without persisting secrets."""

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

from migb.phase2.annotation.adapters import (
    GLMRelayAnnotationAdapter,
    GrokRelayAnnotationAdapter,
)
from migb.phase2.annotation.preflight import (
    DualProviderPreflightResult,
    ProviderPreflightResult,
    load_provider_environment,
    run_dual_provider_preflight,
    synthetic_annotation_request,
)
from migb.phase2.annotation.taxonomy import load_taxonomy_snapshot


DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/phase2/gate2c_annotation_v0.1.yaml"
DEFAULT_TAXONOMY = REPOSITORY_ROOT / "configs/phase2/taxonomy_annotation_v0.1.yaml"
DEFAULT_PROVIDER_ENV_FILE = REPOSITORY_ROOT / "configs/phase2/gate2c_provider.local.env"


def _adapter_from_config(label: str, raw: dict[str, Any]):
    if label == "a":
        adapter_type = GrokRelayAnnotationAdapter
        expected_provider = "grok_relay"
    elif label == "b":
        adapter_type = GLMRelayAnnotationAdapter
        expected_provider = "glm_relay"
    else:  # pragma: no cover - configuration is fixed to A/B
        raise ValueError(f"unsupported annotator label: {label}")

    if raw.get("provider") != expected_provider:
        raise ValueError(f"annotator {label} provider does not match the frozen contract")
    return adapter_type(
        annotator_id=raw["annotator_id"],
        annotation_pass=label,
        model=raw["model"],
        api_key_env=raw["api_key_env"],
        base_url_env=raw["base_url_env"],
    )


def _attempt_summary(attempt: Any) -> dict[str, Any]:
    return {
        "provider_id": attempt.provider,
        "endpoint": attempt.endpoint,
        "requested_model": attempt.requested_model,
        "resolved_model": attempt.resolved_model,
        "structured_output_mode_attempted": attempt.mode,
        "http_status": attempt.http_status,
        "request_id": attempt.request_id,
        "schema_valid": attempt.schema_valid,
        "model_match": attempt.model_match,
        "unsupported_response_format": attempt.unsupported_response_format,
        "input_tokens": attempt.input_tokens,
        "output_tokens": attempt.output_tokens,
        "reasoning_tokens": attempt.reasoning_tokens,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "latency_ms": attempt.latency_ms,
        "passed": attempt.passed,
        "error_type": attempt.error_type,
    }


def _provider_summary(result: ProviderPreflightResult) -> dict[str, Any]:
    discovery = result.discovery
    return {
        "provider_id": result.provider,
        "requested_model": result.requested_model,
        "base_url": discovery.base_url,
        "transport_security": discovery.transport_security,
        "models_http_status": discovery.status_code,
        "available_models_relevant": list(discovery.relevant_models),
        "requested_model_accessible": discovery.requested_model_accessible,
        "models_error_type": discovery.error_type,
        "structured_output_mode": result.structured_output_mode,
        "schema_valid": bool(result.attempts and result.attempts[-1].schema_valid),
        "resolved_model": (
            result.attempts[-1].resolved_model if result.attempts else None
        ),
        "synthetic_attempts": [_attempt_summary(attempt) for attempt in result.attempts],
        "passed": result.passed,
        "error_type": result.error_type,
    }


def _summary(
    raw_config: dict[str, Any],
    result: DualProviderPreflightResult,
) -> dict[str, Any]:
    return {
        "config_revision": raw_config.get("annotation_revision"),
        "prompt_revision": raw_config.get("prompt_revision"),
        "schema_revision": raw_config.get("schema_revision"),
        "taxonomy_revision": raw_config.get("taxonomy_revision"),
        "credential_presence": dict(result.credential_presence),
        "credentials_distinct": result.credentials_distinct,
        "provider_preflight_passed": result.passed,
        "provider_preflight_error_type": result.error_type,
        "providers": [_provider_summary(item) for item in result.provider_results],
        "benchmark_dry_run_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument(
        "--provider-env-file",
        type=Path,
        default=Path(os.environ.get("MIGB_PROVIDER_ENV_FILE", DEFAULT_PROVIDER_ENV_FILE)),
        help="local-only Provider env file; process environment values take precedence",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    with args.config.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)
    if not isinstance(raw_config, dict):
        raise ValueError("Gate 2C configuration must be a mapping")
    raw_annotators = raw_config.get("annotators")
    if not isinstance(raw_annotators, dict):
        raise ValueError("Gate 2C configuration must contain annotators")

    adapters = (
        _adapter_from_config("a", raw_annotators["a"]),
        _adapter_from_config("b", raw_annotators["b"]),
    )
    taxonomy = load_taxonomy_snapshot(args.taxonomy)
    request = synthetic_annotation_request(taxonomy.taxonomy_revision)
    runtime_environment = load_provider_environment(args.provider_env_file, os.environ)
    result = run_dual_provider_preflight(
        adapters,
        request,
        taxonomy,
        environ=runtime_environment,
        timeout=args.timeout,
    )
    print(json.dumps(_summary(raw_config, result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
