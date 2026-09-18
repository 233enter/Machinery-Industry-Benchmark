"""Safe Provider Preflight for the Gate 2C OpenAI-compatible Relay contract."""

from __future__ import annotations

import json
import os
import shlex
import stat
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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

PROVIDER_ENV_VARS = frozenset(
    {
        "GROK_API_KEY",
        "GROK_BASE_URL",
        "GLM_API_KEY",
        "GLM_BASE_URL",
    }
)


class ProviderEnvironmentFileError(ValueError):
    """Raised when the local Provider environment file is unsafe or malformed."""


def load_provider_environment(
    path: str | Path | None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Load local-only Provider variables, with explicit process env precedence.

    The file is intentionally limited to the four Gate 2C variables and must
    not be group/world readable.  Values remain in process memory only.
    """

    merged = dict(os.environ if environ is None else environ)
    if path is None:
        return merged
    env_path = Path(path)
    if not env_path.exists():
        return merged
    if not env_path.is_file():
        raise ProviderEnvironmentFileError(
            f"Provider environment path is not a regular file: {env_path}"
        )
    mode = stat.S_IMODE(env_path.stat().st_mode)
    if mode & 0o077:
        raise ProviderEnvironmentFileError(
            "Provider environment file must be readable only by its owner"
        )

    file_values: dict[str, str] = {}
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ProviderEnvironmentFileError(
            f"cannot read Provider environment file: {env_path}"
        ) from exc
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ProviderEnvironmentFileError(
                f"invalid Provider environment assignment at line {line_number}"
            )
        name, raw_value = line.split("=", 1)
        name = name.strip()
        if name not in PROVIDER_ENV_VARS:
            raise ProviderEnvironmentFileError(
                f"unsupported Provider environment variable at line {line_number}"
            )
        value = raw_value.strip()
        if value:
            try:
                parsed = shlex.split(value, comments=False, posix=True)
            except ValueError as exc:
                raise ProviderEnvironmentFileError(
                    f"invalid Provider environment value at line {line_number}"
                ) from exc
            if len(parsed) != 1:
                raise ProviderEnvironmentFileError(
                    f"Provider environment value must be one shell word at line {line_number}"
                )
            value = parsed[0]
        file_values[name] = value

    # Explicit process environment values take precedence over the local file.
    for name, value in file_values.items():
        merged.setdefault(name, value)
    return merged


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
    discovery_source: str = "network"


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


def owner_verified_model_discovery(
    adapter: OpenAICompatibleAnnotationAdapter,
    verified_model_ids: tuple[str, ...] | list[str],
    *,
    environ: Mapping[str, str] | None = None,
) -> ModelDiscoveryResult:
    """Create a non-network discovery record from an Owner-verified model list."""

    try:
        base_url = adapter.base_url(environ)
        transport_security = adapter.transport_security(environ)
    except Exception as exc:
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
            discovery_source="owner_verified",
        )

    model_ids = tuple(dict.fromkeys(verified_model_ids))
    requested_model_accessible = adapter.model in model_ids
    return ModelDiscoveryResult(
        provider=adapter.provider,
        base_url=base_url,
        transport_security=transport_security,
        requested_model=adapter.model,
        status_code=None,
        model_ids=model_ids,
        relevant_models=relevant_model_excerpt(model_ids, adapter.model),
        requested_model_accessible=requested_model_accessible,
        error_type=None if requested_model_accessible else "owner_verified_model_missing",
        discovery_source="owner_verified",
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
    annotator_id: str
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
        annotator_id=adapter.annotator_id,
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
    annotator_id: str
    provider: str
    requested_model: str
    discovery: ModelDiscoveryResult
    attempts: tuple[SyntheticPreflightAttempt, ...]
    structured_output_mode: str | None
    passed: bool
    error_type: str | None


@dataclass(frozen=True)
class DualProviderPreflightResult:
    """Combined result for two independently invoked Annotators."""

    provider_results: tuple[ProviderPreflightResult, ...]
    credential_presence: Mapping[str, bool]
    credentials_shared: bool
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
    discovery: ModelDiscoveryResult | None = None,
) -> ProviderPreflightResult:
    """Run discovery (or use an injected record) then capability negotiation."""

    if discovery is None:
        discovery = discover_models(
            adapter,
            environ=environ,
            requester=requester,
            timeout=min(timeout, 30.0),
        )
    if not discovery.requested_model_accessible:
        return ProviderPreflightResult(
            annotator_id=adapter.annotator_id,
            provider=adapter.provider,
            requested_model=adapter.model,
            discovery=discovery,
            attempts=(),
            structured_output_mode=None,
            passed=False,
            error_type=discovery.error_type or "requested_model_not_discovered",
        )

    try:
        adapter.credential_value(environ)
    except Exception as exc:
        return ProviderPreflightResult(
            annotator_id=adapter.annotator_id,
            provider=adapter.provider,
            requested_model=adapter.model,
            discovery=discovery,
            attempts=(),
            structured_output_mode=None,
            passed=False,
            error_type=type(exc).__name__,
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
                annotator_id=adapter.annotator_id,
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
        annotator_id=adapter.annotator_id,
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
        annotator_id=adapter.annotator_id,
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
    discoveries: tuple[ModelDiscoveryResult, ModelDiscoveryResult] | None = None,
) -> DualProviderPreflightResult:
    """Run independent A/B synthetic probes with explicit credential semantics."""

    if len(adapters) != 2:
        raise ValueError("dual-provider preflight requires exactly two adapters")
    if discoveries is not None and len(discoveries) != 2:
        raise ValueError("dual-provider preflight requires two discovery records")
    first, second = adapters
    source = os.environ if environ is None else environ
    presence = {
        first.api_key_env: bool(source.get(first.api_key_env)),
        second.api_key_env: bool(source.get(second.api_key_env)),
    }
    shared_credentials = first.provider == second.provider and first.api_key_env == second.api_key_env
    distinct = None if shared_credentials else credentials_are_distinct(
        first.api_key_env,
        second.api_key_env,
        environ,
    )
    if not shared_credentials and distinct is False:
        blocked = (
            _blocked_provider_preflight(first, "credential_isolation_failed", environ),
            _blocked_provider_preflight(second, "credential_isolation_failed", environ),
        )
        return DualProviderPreflightResult(
            provider_results=blocked,
            credential_presence=presence,
            credentials_shared=False,
            credentials_distinct=False,
            passed=False,
            error_type="credential_isolation_failed",
        )

    discovery_records = discoveries or (None, None)
    results = tuple(
        run_provider_preflight(
            adapter,
            request,
            taxonomy,
            environ=environ,
            requester=requester,
            timeout=timeout,
            discovery=discovery,
        )
        for adapter, discovery in zip((first, second), discovery_records, strict=True)
    )
    credential_policy_satisfied = shared_credentials or distinct is True
    all_passed = credential_policy_satisfied and all(result.passed for result in results)
    error_type = None
    if not credential_policy_satisfied:
        error_type = "credentials_missing_or_not_distinct"
    elif not all_passed:
        error_type = next(
            (result.error_type for result in results if not result.passed),
            "provider_preflight_failed",
        )
    return DualProviderPreflightResult(
        provider_results=results,
        credential_presence=presence,
        credentials_shared=shared_credentials,
        credentials_distinct=distinct,
        passed=all_passed,
        error_type=error_type,
    )
