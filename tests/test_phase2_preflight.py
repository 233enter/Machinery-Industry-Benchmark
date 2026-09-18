from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from migb.phase2.annotation.adapters import (
    GLMRelayAnnotationAdapter,
    GrokRelayAnnotationAdapter,
)
from migb.phase2.annotation.preflight import (
    CredentialIsolationError,
    RelayHTTPResponse,
    credentials_are_distinct,
    discover_models,
    load_provider_environment,
    owner_verified_model_discovery,
    require_distinct_credentials,
    run_dual_provider_preflight,
    run_provider_preflight,
    synthetic_annotation_request,
    synthetic_identity_probe,
)
from migb.phase2.annotation.taxonomy import load_taxonomy_snapshot


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = load_taxonomy_snapshot(ROOT / "configs/phase2/taxonomy_annotation_v0.1.yaml")
BASE_URL = "http://relay.example/v1"


def _adapters() -> tuple[GrokRelayAnnotationAdapter, GLMRelayAnnotationAdapter]:
    return (
        GrokRelayAnnotationAdapter(),
        GLMRelayAnnotationAdapter(),
    )


def _output() -> dict[str, Any]:
    return {
        "primary_domain": "D03",
        "secondary_domains": [],
        "taxonomy_fit": "clear_fit",
        "confidence": "medium",
        "evidence_usability": "usable",
        "evidence_keywords": ["spur gear", "surface wear"],
        "evidence_rationale": "The Evidence describes gear transmission and wear.",
        "review_note": None,
    }


def _success_response(model: str | None) -> RelayHTTPResponse:
    payload: dict[str, Any] = {
        "id": "synthetic-request-id",
        "choices": [
            {
                "message": {
                    "content": json.dumps(_output(), ensure_ascii=False),
                }
            }
        ],
        "usage": {
            "prompt_tokens": 41,
            "completion_tokens": 19,
            "completion_tokens_details": {"reasoning_tokens": 0},
        },
    }
    if model is not None:
        payload["model"] = model
    return RelayHTTPResponse(
        status_code=200,
        payload=payload,
        headers={"x-request-id": "synthetic-header-request-id"},
    )


def _schema_invalid_response(model: str | None) -> RelayHTTPResponse:
    response = _success_response(model)
    payload = dict(response.payload)
    payload["choices"] = [
        {
            "message": {
                "content": json.dumps(
                    {**_output(), "secondary_domains": ["D01", "D01"]},
                    ensure_ascii=False,
                )
            }
        }
    ]
    return RelayHTTPResponse(
        status_code=200,
        payload=payload,
        headers=response.headers,
    )


def test_discovery_uses_each_selected_key_and_exact_model_id() -> None:
    grok, glm = _adapters()
    calls: list[tuple[str, str, Mapping[str, str]]] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del payload, timeout
        calls.append((method, url, headers))
        model = "grok-4.6" if headers["Authorization"] == "Bearer grok-unit-value" else "glm-5.3"
        return RelayHTTPResponse(
            status_code=200,
            payload={"data": [{"id": model}, {"id": f"{model}-latest"}]},
            headers={},
        )

    environ = {
        "GROK_API_KEY": "grok-unit-value",
        "GLM_API_KEY": "glm-unit-value",
        "GROK_BASE_URL": BASE_URL,
        "GLM_BASE_URL": BASE_URL,
    }
    grok_result = discover_models(grok, environ=environ, requester=requester)
    glm_result = discover_models(glm, environ=environ, requester=requester)

    assert grok_result.requested_model_accessible is True
    assert glm_result.requested_model_accessible is True
    assert grok_result.relevant_models == ("grok-4.6", "grok-4.6-latest")
    assert glm_result.relevant_models == ("glm-5.3", "glm-5.3-latest")
    assert [call[2]["Authorization"] for call in calls] == [
        "Bearer grok-unit-value",
        "Bearer glm-unit-value",
    ]
    assert [call[1] for call in calls] == [f"{BASE_URL}/models"] * 2


def test_dual_preflight_preserves_provider_identity_with_shared_endpoint() -> None:
    adapters = _adapters()
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    calls: list[tuple[str, str, Mapping[str, str], Mapping[str, Any] | None]] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del timeout
        calls.append((method, url, headers, payload))
        if method == "GET":
            model = "grok-4.6" if headers["Authorization"] == "Bearer grok-unit-value" else "glm-5.3"
            return RelayHTTPResponse(200, {"data": [{"id": model}]}, {})
        model = "grok-4.6" if headers["Authorization"] == "Bearer grok-unit-value" else "glm-5.3"
        return _success_response(model)

    environ = {
        "GROK_API_KEY": "grok-unit-value",
        "GLM_API_KEY": "glm-unit-value",
        "GROK_BASE_URL": BASE_URL,
        "GLM_BASE_URL": BASE_URL,
    }
    result = run_dual_provider_preflight(
        adapters,
        request,
        TAXONOMY,
        environ=environ,
        requester=requester,
    )

    assert result.passed is True
    assert result.credentials_distinct is True
    assert [item.provider for item in result.provider_results] == ["grok_relay", "glm_relay"]
    assert [item.structured_output_mode for item in result.provider_results] == [
        "json_schema",
        "json_schema",
    ]
    assert all(item.discovery.base_url == BASE_URL for item in result.provider_results)
    assert [call[2]["Authorization"] for call in calls if call[0] == "GET"] == [
        "Bearer grok-unit-value",
        "Bearer glm-unit-value",
    ]
    assert [call[2]["Authorization"] for call in calls if call[0] == "POST"] == [
        "Bearer grok-unit-value",
        "Bearer glm-unit-value",
    ]
    assert all(call[1] == f"{BASE_URL}/models" for call in calls if call[0] == "GET")
    assert all(call[1] == f"{BASE_URL}/chat/completions" for call in calls if call[0] == "POST")


def test_shared_glm_credential_supports_two_independent_model_annotators_without_discovery_call() -> None:
    adapter_a = GLMRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="glm-5.3",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
    )
    adapter_b = GLMRelayAnnotationAdapter(
        annotator_id="annotator_b",
        annotation_pass="b",
        model="glm-5.2",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
    )
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    environ = {
        "GLM_API_KEY": "shared-glm-unit-value",
        "GLM_BASE_URL": BASE_URL,
    }
    discoveries = (
        owner_verified_model_discovery(
            adapter_a,
            ("glm-5.3", "glm-5.2"),
            environ=environ,
        ),
        owner_verified_model_discovery(
            adapter_b,
            ("glm-5.3", "glm-5.2"),
            environ=environ,
        ),
    )
    calls: list[tuple[str, Mapping[str, Any] | None]] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, timeout
        calls.append((method, payload))
        assert method == "POST"
        assert headers["Authorization"] == "Bearer shared-glm-unit-value"
        assert payload is not None
        return _success_response(str(payload["model"]))

    result = run_dual_provider_preflight(
        (adapter_a, adapter_b),
        request,
        TAXONOMY,
        environ=environ,
        requester=requester,
        discoveries=discoveries,
    )

    assert result.passed is True
    assert result.credentials_shared is True
    assert result.credentials_distinct is None
    assert [item.annotator_id for item in result.provider_results] == [
        "annotator_a",
        "annotator_b",
    ]
    assert [item.requested_model for item in result.provider_results] == ["glm-5.3", "glm-5.2"]
    assert [item.provider for item in result.provider_results] == ["glm_relay", "glm_relay"]
    assert [item.structured_output_mode for item in result.provider_results] == [
        "json_schema",
        "json_schema",
    ]
    assert [method for method, _ in calls] == ["POST", "POST"]
    assert [payload["model"] for _, payload in calls if payload is not None] == [
        "glm-5.3",
        "glm-5.2",
    ]
    assert all(item.discovery.discovery_source == "owner_verified" for item in result.provider_results)


def test_shared_glm_credential_missing_fails_before_synthetic_requests() -> None:
    adapter_a = GLMRelayAnnotationAdapter(model="glm-5.3")
    adapter_b = GLMRelayAnnotationAdapter(
        annotator_id="annotator_b",
        annotation_pass="b",
        model="glm-5.2",
    )
    environ = {"GLM_BASE_URL": BASE_URL}
    discoveries = (
        owner_verified_model_discovery(adapter_a, ("glm-5.3", "glm-5.2"), environ=environ),
        owner_verified_model_discovery(adapter_b, ("glm-5.3", "glm-5.2"), environ=environ),
    )

    def requester(*args: Any, **kwargs: Any) -> RelayHTTPResponse:
        raise AssertionError("missing GLM credential must not call the relay")

    result = run_dual_provider_preflight(
        (adapter_a, adapter_b),
        synthetic_annotation_request(TAXONOMY.taxonomy_revision),
        TAXONOMY,
        environ=environ,
        requester=requester,
        discoveries=discoveries,
    )

    assert result.passed is False
    assert result.credentials_shared is True
    assert all(item.error_type == "MissingCredentialsError" for item in result.provider_results)


def test_identity_probe_uses_minimal_request_and_requires_exact_resolved_model() -> None:
    adapter = GLMRelayAnnotationAdapter(
        annotator_id="annotator_b_identity_probe",
        annotation_pass="b",
        model="glm-5.1",
    )
    calls: list[tuple[str, Mapping[str, Any] | None]] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, headers, timeout
        calls.append((method, payload))
        return RelayHTTPResponse(
            status_code=200,
            payload={"id": "identity-request-id", "model": "glm-5.1"},
            headers={},
        )

    result = synthetic_identity_probe(
        adapter,
        environ={"GLM_API_KEY": "glm-unit-value", "GLM_BASE_URL": BASE_URL},
        requester=requester,
    )

    assert result.passed is True
    assert result.model_match is True
    assert result.resolved_model == "glm-5.1"
    assert [method for method, _ in calls] == ["POST"]
    assert calls[0][1] is not None
    assert calls[0][1]["model"] == "glm-5.1"
    assert "response_format" not in calls[0][1]


def test_structured_output_negotiation_falls_back_in_order() -> None:
    adapter = GrokRelayAnnotationAdapter()
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    modes: list[str] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, headers, timeout
        if method == "GET":
            return RelayHTTPResponse(200, {"data": [{"id": adapter.model}]}, {})
        assert payload is not None
        response_format = payload.get("response_format")
        if isinstance(response_format, Mapping):
            mode = str(response_format.get("type"))
        else:
            mode = "prompt_json_only"
        modes.append(mode)
        if mode in {"json_schema", "json_object"}:
            return RelayHTTPResponse(
                status_code=400,
                payload={"error": {"message": f"unsupported response_format {mode}"}},
                headers={},
                error_type="http_error",
            )
        return _success_response(adapter.model)

    result = run_provider_preflight(
        adapter,
        request,
        TAXONOMY,
        environ={
            "GROK_API_KEY": "grok-unit-value",
            "GROK_BASE_URL": BASE_URL,
        },
        requester=requester,
    )

    assert result.passed is True
    assert result.structured_output_mode == "prompt_json_only"
    assert modes == ["json_schema", "json_object", "prompt_json_only"]
    assert [attempt.mode for attempt in result.attempts] == modes
    assert result.attempts[-1].schema_valid is True
    assert result.attempts[-1].resolved_model == "grok-4.6"


def test_schema_invalid_2xx_continues_to_json_object() -> None:
    adapter = GLMRelayAnnotationAdapter(model="glm-5.3")
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    modes: list[str] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, headers, timeout
        if method == "GET":
            return RelayHTTPResponse(200, {"data": [{"id": adapter.model}]}, {})
        assert payload is not None
        mode = str(payload.get("response_format", {}).get("type", "prompt_json_only"))
        modes.append(mode)
        return _schema_invalid_response(adapter.model) if mode == "json_schema" else _success_response(adapter.model)

    result = run_provider_preflight(
        adapter,
        request,
        TAXONOMY,
        environ={"GLM_API_KEY": "glm-unit-value", "GLM_BASE_URL": BASE_URL},
        requester=requester,
    )

    assert result.passed is True
    assert result.structured_output_mode == "json_object"
    assert modes == ["json_schema", "json_object"]
    first = result.attempts[0]
    assert first.http_success is True
    assert first.model_match is True
    assert first.schema_valid is False
    assert first.mode_usable is False
    assert first.failure_category == "schema_incompatible_mode"
    assert first.validation_error_field == "secondary_domains"
    assert first.validation_error_type == "AnnotationSchemaError"
    assert first.validation_error_message is not None


def test_schema_invalid_modes_continue_to_prompt_json_only() -> None:
    adapter = GLMRelayAnnotationAdapter(model="glm-5.3")
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    modes: list[str] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, headers, timeout
        if method == "GET":
            return RelayHTTPResponse(200, {"data": [{"id": adapter.model}]}, {})
        assert payload is not None
        mode = str(payload.get("response_format", {}).get("type", "prompt_json_only"))
        modes.append(mode)
        return _success_response(adapter.model) if mode == "prompt_json_only" else _schema_invalid_response(adapter.model)

    result = run_provider_preflight(
        adapter,
        request,
        TAXONOMY,
        environ={"GLM_API_KEY": "glm-unit-value", "GLM_BASE_URL": BASE_URL},
        requester=requester,
    )

    assert result.passed is True
    assert result.structured_output_mode == "prompt_json_only"
    assert modes == ["json_schema", "json_object", "prompt_json_only"]
    assert all(attempt.failure_category == "schema_incompatible_mode" for attempt in result.attempts[:2])


def test_schema_invalid_then_model_mismatch_stops_negotiation() -> None:
    adapter = GLMRelayAnnotationAdapter(model="glm-5.3")
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    modes: list[str] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, headers, timeout
        if method == "GET":
            return RelayHTTPResponse(200, {"data": [{"id": adapter.model}]}, {})
        assert payload is not None
        mode = str(payload.get("response_format", {}).get("type", "prompt_json_only"))
        modes.append(mode)
        if mode == "json_schema":
            return _schema_invalid_response(adapter.model)
        return _success_response("glm-5.3-flash")

    result = run_provider_preflight(
        adapter,
        request,
        TAXONOMY,
        environ={"GLM_API_KEY": "glm-unit-value", "GLM_BASE_URL": BASE_URL},
        requester=requester,
    )

    assert result.passed is False
    assert result.error_type == "resolved_model_mismatch"
    assert modes == ["json_schema", "json_object"]
    assert result.attempts[-1].failure_category == "resolved_model_mismatch"


def test_resolved_model_mismatch_stops_without_alias_substitution() -> None:
    adapter = GrokRelayAnnotationAdapter()
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    calls: list[str] = []

    def requester(
        method: str,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any] | None,
        timeout: float,
    ) -> RelayHTTPResponse:
        del url, headers, payload, timeout
        calls.append(method)
        if method == "GET":
            return RelayHTTPResponse(200, {"data": [{"id": adapter.model}]}, {})
        return _success_response("grok-4.6-latest")

    result = run_provider_preflight(
        adapter,
        request,
        TAXONOMY,
        environ={"GROK_API_KEY": "grok-unit-value", "GROK_BASE_URL": BASE_URL},
        requester=requester,
    )

    assert result.passed is False
    assert result.error_type == "resolved_model_mismatch"
    assert len(result.attempts) == 1
    assert result.attempts[0].model_match is False
    assert result.attempts[0].resolved_model == "grok-4.6-latest"
    assert calls == ["GET", "POST"]


def test_missing_credential_never_calls_relay_and_reports_transport_class() -> None:
    adapter = GrokRelayAnnotationAdapter()

    def requester(*args: Any, **kwargs: Any) -> RelayHTTPResponse:
        raise AssertionError("relay must not be called without the selected credential")

    result = discover_models(
        adapter,
        environ={"GROK_BASE_URL": BASE_URL},
        requester=requester,
    )

    assert result.base_url == BASE_URL
    assert result.transport_security == "plaintext_http"
    assert result.status_code is None
    assert result.requested_model_accessible is False
    assert result.error_type == "MissingCredentialsError"


def test_same_credential_blocks_dual_preflight_before_network() -> None:
    adapters = _adapters()
    request = synthetic_annotation_request(TAXONOMY.taxonomy_revision)
    calls: list[Any] = []

    def requester(*args: Any, **kwargs: Any) -> RelayHTTPResponse:
        calls.append((args, kwargs))
        raise AssertionError("same credential must not be sent to either provider")

    environ = {
        "GROK_API_KEY": "shared-unit-value",
        "GLM_API_KEY": "shared-unit-value",
        "GROK_BASE_URL": BASE_URL,
        "GLM_BASE_URL": BASE_URL,
    }
    result = run_dual_provider_preflight(
        adapters,
        request,
        TAXONOMY,
        environ=environ,
        requester=requester,
    )

    assert result.passed is False
    assert result.credentials_distinct is False
    assert result.error_type == "credential_isolation_failed"
    assert calls == []
    assert all(item.error_type == "credential_isolation_failed" for item in result.provider_results)


def test_credential_isolation_helper_is_fail_closed() -> None:
    assert credentials_are_distinct("A", "B", {"A": "one", "B": "two"}) is True
    assert credentials_are_distinct("A", "B", {"A": "one", "B": "one"}) is False
    assert credentials_are_distinct("A", "B", {"A": "one"}) is None
    with pytest.raises(CredentialIsolationError):
        require_distinct_credentials("A", "B", {"A": "one", "B": "one"})


def test_local_provider_environment_file_loads_four_variables_safely(tmp_path: Path) -> None:
    path = tmp_path / "provider.env"
    path.write_text(
        "GROK_API_KEY='file-grok'\n"
        "GROK_BASE_URL=http://relay.example/v1\n"
        "GLM_API_KEY=file-glm\n"
        "GLM_BASE_URL=http://relay.example/v1\n",
        encoding="utf-8",
    )
    path.chmod(0o600)

    merged = load_provider_environment(
        path,
        environ={"GROK_API_KEY": "process-grok", "OTHER": "retained"},
    )

    assert merged["GROK_API_KEY"] == "process-grok"
    assert merged["GLM_API_KEY"] == "file-glm"
    assert merged["GROK_BASE_URL"] == BASE_URL
    assert merged["GLM_BASE_URL"] == BASE_URL
    assert merged["OTHER"] == "retained"


def test_local_provider_environment_file_rejects_insecure_permissions(tmp_path: Path) -> None:
    path = tmp_path / "provider.env"
    path.write_text("GROK_API_KEY=value\n", encoding="utf-8")
    path.chmod(0o644)

    with pytest.raises(ValueError, match="owner"):
        load_provider_environment(path, environ={})
