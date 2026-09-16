"""Safe Provider Preflight for the Gate 2C OpenAI-compatible Relay contract."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from .adapters import (
    STRUCTURED_OUTPUT_MODES,
    OpenAICompatibleAnnotationAdapter,
)
from .prompt import PROMPT_REVISION
from .schema import AnnotationRequest, SCHEMA_REVISION
from .taxonomy import TaxonomySnapshot


class CredentialIsolationError(RuntimeError):
    """Raised when two configured Provider credentials are the same value."""


@dataclass(frozen=True)
class RelayHTTPResponse:
    """A response envelope that never stores request headers or credential values."""

    status_code: int | None
    payload: Any | None
    headers: Mapping[str, str]
    error_type: str | None = None


RelayRequester = Callable[
    [str, str, Mapping[str, str], Mapping[str, Any] | None, float], RelayHTTPResponse
]


SYNTHETIC_TITLE = "Synthetic Spur Gear Wear Study"
SYNTHETIC_EVIDENCE = (
    "This synthetic document studies spur gear tooth contact, gear transmission design, "
    "surface wear and service life."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def synthetic_annotation_request(taxonomy_revision: str) -> AnnotationRequest:
    """Build the fixed, real-corpus-free request used by Provider preflight."""

    return AnnotationRequest(
        calibration_sample_id="provider-preflight-synthetic-v0.1",
        calibration_item_id="synthetic-spur-gear-wear-study",
        evidence_revision="synthetic-evidence-v0.1",
        taxonomy_revision=taxonomy_revision,
        prompt_revision=PROMPT_REVISION,
        schema_revision=SCHEMA_REVISION,
        evidence=SYNTHETIC_EVIDENCE,
        filename_title=SYNTHETIC_TITLE,
        metadata_title=SYNTHETIC_TITLE,
    )


def _decode_json(raw: bytes) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def default_relay_requester(
    method: str,
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any] | None,
    timeout: float,
) -> RelayHTTPResponse:
    """Send one JSON request without returning or logging credential-bearing data."""

    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = UrlRequest(url, data=body, headers=dict(headers), method=method)
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - configured endpoint
            return RelayHTTPResponse(
                status_code=int(response.status),
                payload=_decode_json(response.read()),
                headers={key.lower(): value for key, value in response.headers.items()},
            )
    except HTTPError as exc:
        # Read the body only for local capability classification; never return its text.
        payload_value = _decode_json(exc.read())
        return RelayHTTPResponse(
            status_code=int(exc.code),
            payload=payload_value,
            headers={key.lower(): value for key, value in exc.headers.items()},
            error_type="http_error",
        )
    except (TimeoutError, URLError, OSError, ValueError):
        return RelayHTTPResponse(
            status_code=None,
            payload=None,
            headers={},
            error_type="transport_error",
        )


def credentials_are_distinct(
    first_env: str,
    second_env: str,
    environ: Mapping[str, str] | None = None,
) -> bool | None:
    """Compare two present credential values without exposing either value.

    ``None`` means at least one credential is absent and the caller must report
    presence failure separately.
    """

    source = os.environ if environ is None else environ
    first = source.get(first_env)
    second = source.get(second_env)
    if not first or not second:
        return None
    return first != second


def require_distinct_credentials(
    first_env: str,
    second_env: str,
    environ: Mapping[str, str] | None = None,
) -> None:
    """Fail closed unless both configured provider credentials are distinct."""

    if credentials_are_distinct(first_env, second_env, environ) is not True:
        raise CredentialIsolationError(
            "both provider credentials must be present and distinct"
        )


def _model_ids(payload: Any) -> tuple[str, ...]:
    if isinstance(payload, Mapping):
        raw_models = payload.get("data")
    else:
        raw_models = payload
    if not isinstance(raw_models, list):
        return ()
    ids: list[str] = []
    for model in raw_models:
        if isinstance(model, Mapping) and isinstance(model.get("id"), str):
            ids.append(model["id"])
        elif isinstance(model, str):
            ids.append(model)
    return tuple(dict.fromkeys(ids))


def relevant_model_excerpt(model_ids: tuple[str, ...], requested_model: str) -> tuple[str, ...]:
    """Return a small deterministic excerpt without accepting aliases."""

    family = requested_model.split("-", 1)[0].lower()
    relevant = [model_id for model_id in model_ids if family in model_id.lower()]
    if requested_model in model_ids and requested_model not in relevant:
        relevant.insert(0, requested_model)
    return tuple(relevant[:20])


@dataclass(frozen=True)
class ModelDiscoveryResult:
    provider: str
    base_url: str | None
    transport_security: str | None
    requested_model: str
    status_code: int | None
    model_ids: tuple[str, ...]
    relevant_models: tuple[str, ...]
    requested_model_accessible: bool
    error_type: str | None


def discover_models(
    adapter: OpenAICompatibleAnnotationAdapter,
    *,
    environ: Mapping[str, str] | None = None,
    requester: RelayRequester = default_relay_requester,
    timeout: float = 30.0,
) -> ModelDiscoveryResult:
    """Discover models with exactly the credential selected by ``adapter``."""

    try:
        base_url = adapter.base_url(environ)
        transport_security = adapter.transport_security(environ)
    except Exception as exc:  # endpoint errors are safe to summarize by type
        return ModelDiscoveryResult(
            provider=adapter.provider,
            base_url=None,
            transport_security=None,
            requested_model=adapter.model,
            status_code=None,
            model_ids=(),
            relevant_models=(),
            requested_model_accessible=False,
            error_type=type(exc).__name__,
        )

    try:
        credential = adapter.credential_value(environ)
    except Exception as exc:  # credential errors are safe to summarize by type
        return ModelDiscoveryResult(
            provider=adapter.provider,
            base_url=base_url,
            transport_security=transport_security,
            requested_model=adapter.model,
            status_code=None,
            model_ids=(),
            relevant_models=(),
            requested_model_accessible=False,
            error_type=type(exc).__name__,
        )

    response = requester(
        "GET",
        f"{base_url}/models",
        {"Authorization": f"Bearer {credential}"},
        None,
        timeout,
    )
    model_ids = _model_ids(response.payload)
    return ModelDiscoveryResult(
        provider=adapter.provider,
        base_url=base_url,
        transport_security=transport_security,
        requested_model=adapter.model,
        status_code=response.status_code,
        model_ids=model_ids,
        relevant_models=relevant_model_excerpt(model_ids, adapter.model),
        requested_model_accessible=adapter.model in model_ids,
        error_type=response.error_type
        or ("http_error" if response.status_code is not None and response.status_code >= 400 else None)
        or ("invalid_models_response" if response.status_code == 200 and not model_ids else None),
    )


def _response_model(payload: Any) -> str | None:
    if isinstance(payload, Mapping) and isinstance(payload.get("model"), str):
        return payload["model"]
    return None


def _request_id(payload: Any, headers: Mapping[str, str]) -> str | None:
    if isinstance(payload, Mapping) and isinstance(payload.get("id"), str):
        return payload["id"]
    return headers.get("x-request-id") or headers.get("request-id")


def _usage_value(usage: Any, *keys: str) -> int | None:
    if not isinstance(usage, Mapping):
        return None
    for key in keys:
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return None


def _usage_metadata(payload: Any) -> tuple[int | None, int | None, int | None]:
    if not isinstance(payload, Mapping):
        return None, None, None
    usage = payload.get("usage")
    input_tokens = _usage_value(usage, "prompt_tokens", "input_tokens")
    output_tokens = _usage_value(usage, "completion_tokens", "output_tokens")
    reasoning_tokens = None
    if isinstance(usage, Mapping):
        details = usage.get("completion_tokens_details") or usage.get("output_tokens_details")
        reasoning_tokens = _usage_value(details, "reasoning_tokens")
    return input_tokens, output_tokens, reasoning_tokens


def _is_unsupported_response_format(payload: Any, status_code: int | None) -> bool:
    if status_code not in {400, 422}:
        return False
    try:
        message = json.dumps(payload, ensure_ascii=False).lower()
    except (TypeError, ValueError):
        return False
    format_terms = ("response_format", "json_schema", "json mode", "json_object")
    support_terms = ("unsupported", "not support", "invalid", "unknown")
    return any(term in message for term in format_terms) and any(
        term in message for term in support_terms
    )


@dataclass(frozen=True)
class SyntheticPreflightAttempt:
    provider: str
    endpoint: str
    requested_model: str
    mode: str
    http_status: int | None
    request_id: str | None
    resolved_model: str | None
    model_match: bool
    schema_valid: bool
    passed: bool
    unsupported_response_format: bool
    error_type: str | None
    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    started_at: str
    completed_at: str
    latency_ms: int


def synthetic_preflight_attempt(
    adapter: OpenAICompatibleAnnotationAdapter,
    request: AnnotationRequest,
    taxonomy: TaxonomySnapshot,
    *,
    mode: str,
    attempt_id: str,
    environ: Mapping[str, str] | None = None,
    requester: RelayRequester = default_relay_requester,
    timeout: float = 60.0,
) -> SyntheticPreflightAttempt:
    """Send one synthetic chat-completions capability probe."""

    if mode not in STRUCTURED_OUTPUT_MODES:
        raise ValueError(f"unsupported structured output mode: {mode}")
    built = adapter.build_request(request, taxonomy, structured_output_mode=mode)
    endpoint = adapter.endpoint("/chat/completions", environ)
    headers = {
        "Authorization": f"Bearer {adapter.credential_value(environ)}",
        "Content-Type": "application/json",
    }
    started_at = _utc_now()
    started = time.monotonic()
    response = requester("POST", endpoint, headers, built["payload"], timeout)
    completed_at = _utc_now()
    latency_ms = max(0, int(round((time.monotonic() - started) * 1000)))
    resolved_model = _response_model(response.payload)
    model_match = resolved_model is None or resolved_model == adapter.model
    input_tokens, output_tokens, reasoning_tokens = _usage_metadata(response.payload)
    parsed_attempt = adapter.parse_response(
        request,
        response.payload,
        attempt_id=attempt_id,
        request_id=_request_id(response.payload, response.headers),
        resolved_model=resolved_model,
        started_at=started_at,
        completed_at=completed_at,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens_if_available=reasoning_tokens,
        latency_ms=latency_ms,
        provenance=built["provenance"],
    )
    schema_valid = parsed_attempt.parse_status == "passed"
    unsupported = _is_unsupported_response_format(response.payload, response.status_code)
    http_success = response.status_code is not None and 200 <= response.status_code < 300
    passed = http_success and model_match and schema_valid
    error_type = response.error_type
    if not http_success and error_type is None:
        error_type = "http_error"
    if http_success and not schema_valid:
        error_type = parsed_attempt.error_type or "schema_validation_failed"
    if http_success and not model_match:
        error_type = "resolved_model_mismatch"
    return SyntheticPreflightAttempt(
        provider=adapter.provider,
        endpoint=endpoint,
        requested_model=adapter.model,
        mode=mode,
        http_status=response.status_code,
        request_id=_request_id(response.payload, response.headers),
        resolved_model=resolved_model,
        model_match=model_match,
        schema_valid=schema_valid,
        passed=passed,
        unsupported_response_format=unsupported,
        error_type=error_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        started_at=started_at,
        completed_at=completed_at,
        latency_ms=latency_ms,
    )


@dataclass(frozen=True)
class ProviderPreflightResult:
    provider: str
    requested_model: str
    discovery: ModelDiscoveryResult
    attempts: tuple[SyntheticPreflightAttempt, ...]
    structured_output_mode: str | None
    passed: bool
    error_type: str | None


@dataclass(frozen=True)
class DualProviderPreflightResult:
    """Combined result for two independently credentialed Annotators."""

    provider_results: tuple[ProviderPreflightResult, ...]
    credential_presence: Mapping[str, bool]
    credentials_distinct: bool | None
    passed: bool
    error_type: str | None


def run_provider_preflight(
    adapter: OpenAICompatibleAnnotationAdapter,
    request: AnnotationRequest,
    taxonomy: TaxonomySnapshot,
    *,
    environ: Mapping[str, str] | None = None,
    requester: RelayRequester = default_relay_requester,
    timeout: float = 60.0,
) -> ProviderPreflightResult:
    """Run model discovery then capability negotiation for one provider/key."""

    discovery = discover_models(
        adapter,
        environ=environ,
        requester=requester,
        timeout=min(timeout, 30.0),
    )
    if not discovery.requested_model_accessible:
        return ProviderPreflightResult(
            provider=adapter.provider,
            requested_model=adapter.model,
            discovery=discovery,
            attempts=(),
            structured_output_mode=None,
            passed=False,
            error_type=discovery.error_type or "requested_model_not_discovered",
        )

    attempts: list[SyntheticPreflightAttempt] = []
    for index, mode in enumerate(STRUCTURED_OUTPUT_MODES, start=1):
        attempt = synthetic_preflight_attempt(
            adapter,
            request,
            taxonomy,
            mode=mode,
            attempt_id=f"preflight-{adapter.provider}-{index}",
            environ=environ,
            requester=requester,
            timeout=timeout,
        )
        attempts.append(attempt)
        if attempt.passed:
            return ProviderPreflightResult(
                provider=adapter.provider,
                requested_model=adapter.model,
                discovery=discovery,
                attempts=tuple(attempts),
                structured_output_mode=mode,
                passed=True,
                error_type=None,
            )
        if not attempt.unsupported_response_format or not attempt.model_match:
            break
    return ProviderPreflightResult(
        provider=adapter.provider,
        requested_model=adapter.model,
        discovery=discovery,
        attempts=tuple(attempts),
        structured_output_mode=None,
        passed=False,
        error_type=attempts[-1].error_type if attempts else "synthetic_preflight_failed",
    )


def _blocked_provider_preflight(
    adapter: OpenAICompatibleAnnotationAdapter,
    error_type: str,
    environ: Mapping[str, str] | None = None,
) -> ProviderPreflightResult:
    """Return a non-network result when dual-provider safety blocks a request."""

    try:
        base_url = adapter.base_url(environ)
        transport_security = adapter.transport_security(environ)
    except Exception:
        base_url = None
        transport_security = None
    discovery = ModelDiscoveryResult(
        provider=adapter.provider,
        base_url=base_url,
        transport_security=transport_security,
        requested_model=adapter.model,
        status_code=None,
        model_ids=(),
        relevant_models=(),
        requested_model_accessible=False,
        error_type=error_type,
    )
    return ProviderPreflightResult(
        provider=adapter.provider,
        requested_model=adapter.model,
        discovery=discovery,
        attempts=(),
        structured_output_mode=None,
        passed=False,
        error_type=error_type,
    )


def run_dual_provider_preflight(
    adapters: tuple[OpenAICompatibleAnnotationAdapter, OpenAICompatibleAnnotationAdapter]
    | list[OpenAICompatibleAnnotationAdapter],
    request: AnnotationRequest,
    taxonomy: TaxonomySnapshot,
    *,
    environ: Mapping[str, str] | None = None,
    requester: RelayRequester = default_relay_requester,
    timeout: float = 60.0,
) -> DualProviderPreflightResult:
    """Run A/B discovery and synthetic capability negotiation with key isolation."""

    if len(adapters) != 2:
        raise ValueError("dual-provider preflight requires exactly two adapters")
    first, second = adapters
    source = os.environ if environ is None else environ
    presence = {
        first.api_key_env: bool(source.get(first.api_key_env)),
        second.api_key_env: bool(source.get(second.api_key_env)),
    }
    distinct = credentials_are_distinct(
        first.api_key_env,
        second.api_key_env,
        environ,
    )
    if distinct is False:
        blocked = (
            _blocked_provider_preflight(first, "credential_isolation_failed", environ),
            _blocked_provider_preflight(second, "credential_isolation_failed", environ),
        )
        return DualProviderPreflightResult(
            provider_results=blocked,
            credential_presence=presence,
            credentials_distinct=False,
            passed=False,
            error_type="credential_isolation_failed",
        )

    results = tuple(
        run_provider_preflight(
            adapter,
            request,
            taxonomy,
            environ=environ,
            requester=requester,
            timeout=timeout,
        )
        for adapter in (first, second)
    )
    all_passed = distinct is True and all(result.passed for result in results)
    error_type = None
    if distinct is not True:
        error_type = "credentials_missing_or_not_distinct"
    elif not all_passed:
        error_type = next(
            (result.error_type for result in results if not result.passed),
            "provider_preflight_failed",
        )
    return DualProviderPreflightResult(
        provider_results=results,
        credential_presence=presence,
        credentials_distinct=distinct,
        passed=all_passed,
        error_type=error_type,
    )
