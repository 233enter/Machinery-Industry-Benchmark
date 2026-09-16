from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest
import yaml

from migb.phase2.annotation.adapters import (
    GLMRelayAnnotationAdapter,
    MissingCredentialsError,
    GrokRelayAnnotationAdapter,
    RemoteInferenceDisabledError,
)
from migb.phase2.annotation.agreement import classify_annotation_pair
from migb.phase2.annotation.artifacts import (
    GATE2C_ARTIFACT_NAMES,
    annotation_attempt_row,
    artifact_row_identity,
    final_annotation_row,
    gate2c_artifact_paths,
)
from migb.phase2.annotation.prompt import (
    PROMPT_REVISION,
    prompt_hash,
    prompt_template_hash,
    render_annotation_prompt,
)
from migb.phase2.annotation.retry import (
    MAX_EVIDENCE_RETRY_COUNT,
    can_retry,
    decide_item_retry,
    ensure_same_final_evidence,
    mark_first_pass_superseded,
)
from migb.phase2.annotation.schema import (
    AnnotationRequest,
    AnnotationSchemaError,
    SCHEMA_REVISION,
    annotation_schema_hash,
    schema_definition,
    validate_model_output,
)
from migb.phase2.annotation.taxonomy import load_taxonomy_snapshot, taxonomy_payload_hash


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "configs/phase2/taxonomy_annotation_v0.1.yaml"
CONFIG_PATH = ROOT / "configs/phase2/gate2c_annotation_v0.1.yaml"
SCHEMA_PATH = ROOT / "schemas/phase2/taxonomy_annotation_v0.1.json"


def _request(item_id: str = "item-1", evidence_revision: str = "evidence-v0.3-primary") -> AnnotationRequest:
    return AnnotationRequest(
        calibration_sample_id="sample-1",
        calibration_item_id=item_id,
        evidence_revision=evidence_revision,
        taxonomy_revision="taxonomy-v0.1",
        prompt_revision=PROMPT_REVISION,
        schema_revision=SCHEMA_REVISION,
        evidence="齿轮传动与机械设计的技术摘要。",
        filename_title="齿轮传动研究",
        metadata_title="机械设计研究",
        page_count=3,
        relative_path="group/item-1.pdf",
    )


def _output(
    *,
    evidence_usability: str = "usable",
    taxonomy_fit: str = "clear_fit",
    confidence: str = "medium",
    secondary_domains: list[str] | None = None,
) -> dict[str, object]:
    return {
        "primary_domain": "D03",
        "secondary_domains": [] if secondary_domains is None else secondary_domains,
        "taxonomy_fit": taxonomy_fit,
        "confidence": confidence,
        "evidence_usability": evidence_usability,
        "evidence_keywords": ["齿轮传动", "机械设计"],
        "evidence_rationale": "Evidence 明确描述机械设计主题。",
        "review_note": None,
    }


def _response(
    adapter: GrokRelayAnnotationAdapter | GLMRelayAnnotationAdapter,
    *,
    request: AnnotationRequest | None = None,
    output: dict[str, object] | None = None,
    evidence_revision: str | None = None,
    attempt_id: str = "attempt-1",
):
    request = request or _request(evidence_revision=evidence_revision or "evidence-v0.3-primary")
    taxonomy = load_taxonomy_snapshot(TAXONOMY_PATH)
    built = adapter.build_request(request, taxonomy)
    attempt = adapter.parse_response(
        request,
        {"output_text": json.dumps(output or _output(), ensure_ascii=False)},
        attempt_id=attempt_id,
        request_id=f"request-{attempt_id}",
        provenance=built["provenance"],
    )
    assert attempt.response is not None
    return attempt.response


def test_taxonomy_snapshot_and_schema_hashes_are_stable() -> None:
    snapshot = load_taxonomy_snapshot(TAXONOMY_PATH)
    assert len(snapshot.domains) == 12
    assert snapshot.domains[0].domain_id == "D01"
    assert snapshot.domains[-1].domain_id == "D12"
    assert snapshot.payload_hash == taxonomy_payload_hash(snapshot)
    assert snapshot.source_document == "docs/02_benchmark_taxonomy.md"

    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["taxonomy_payload_hash"] == snapshot.payload_hash
    assert config["prompt_template_hash"] == prompt_template_hash(snapshot)
    assert config["schema_hash"] == annotation_schema_hash()

    schema_document = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema_document == schema_definition()
    assert annotation_schema_hash() == hashlib.sha256(
        json.dumps(schema_document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def test_annotation_schema_rejects_invalid_domain_and_secondary_values() -> None:
    valid = _output()
    assert validate_model_output(valid)["primary_domain"] == "D03"

    invalid_domain = {**valid, "primary_domain": "D99"}
    with pytest.raises(AnnotationSchemaError, match="primary_domain"):
        validate_model_output(invalid_domain)

    invalid_secondary = {**valid, "secondary_domains": ["D03"]}
    with pytest.raises(AnnotationSchemaError, match="cannot contain primary_domain"):
        validate_model_output(invalid_secondary)

    duplicate_secondary = {**valid, "secondary_domains": ["D01", "D01"]}
    with pytest.raises(AnnotationSchemaError, match="duplicates"):
        validate_model_output(duplicate_secondary)

    invalid_evidence_usability = {**valid, "evidence_usability": "unknown"}
    with pytest.raises(AnnotationSchemaError, match="evidence_usability"):
        validate_model_output(invalid_evidence_usability)

    unknown = {**valid, "requires_evidence_retry": True}
    with pytest.raises(AnnotationSchemaError, match="unknown annotation fields"):
        validate_model_output(unknown)


def test_prompt_is_deterministic_and_excludes_routing_metadata() -> None:
    request = _request()
    taxonomy = load_taxonomy_snapshot(TAXONOMY_PATH)
    first = render_annotation_prompt(request, taxonomy)
    second = render_annotation_prompt(request, taxonomy)
    assert first == second
    assert prompt_hash(first) == prompt_hash(second)
    assert first.index("SYSTEM") < first.index("TAXONOMY") < first.index("EVIDENCE QUALITY RULES")
    assert first.index("ANNOTATION RULES") < first.index("DOCUMENT METADATA") < first.index(
        "EVIDENCE\n<<<BEGIN_FINAL_EVIDENCE>>>"
    )
    assert "parent_group" not in first
    assert "relative_path" not in first
    assert "group/item-1.pdf" not in first
    assert "Problem item" not in first
    assert "NO web access" in first
    assert "chain-of-thought" in first


def test_provider_request_construction_and_configuration_are_separate_from_credentials() -> None:
    taxonomy = load_taxonomy_snapshot(TAXONOMY_PATH)
    request = _request()
    grok = GrokRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="grok-4.6",
        api_key_env="GROK_API_KEY",
        base_url_env="GROK_BASE_URL",
        reasoning_effort="low",
    )
    built_a = grok.build_request(request, taxonomy)
    payload_a = built_a["payload"]
    assert built_a["provider"] == "grok_relay"
    assert grok.provider_id == "grok_relay"
    assert payload_a["model"] == "grok-4.6"
    assert payload_a["reasoning_effort"] == "low"
    assert payload_a["response_format"]["type"] == "json_schema"
    assert "temperature" not in payload_a
    assert "top_p" not in payload_a
    assert "GROK_API_KEY" not in json.dumps(built_a)
    assert built_a["provenance"]["peer_annotation_visible"] is False

    glm = GLMRelayAnnotationAdapter(
        annotator_id="annotator_b",
        annotation_pass="b",
        model="glm-5.3",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
    )
    built_b = glm.build_request(request, taxonomy, structured_output_mode="json_object")
    assert built_b["provider"] == "glm_relay"
    assert glm.provider_id == "glm_relay"
    assert built_b["payload"]["model"] == "glm-5.3"
    assert built_b["payload"]["response_format"] == {"type": "json_object"}
    assert "temperature" not in built_b["payload"]
    assert "top_p" not in built_b["payload"]
    prompt_only = glm.build_request(request, taxonomy, structured_output_mode="prompt_json_only")
    assert "response_format" not in prompt_only["payload"]


def test_credentials_are_environment_only_and_remote_inference_is_disabled() -> None:
    taxonomy = load_taxonomy_snapshot(TAXONOMY_PATH)
    adapter = GrokRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="grok-4.6",
        api_key_env="GROK_API_KEY",
        base_url_env="GROK_BASE_URL",
    )
    with pytest.raises(MissingCredentialsError, match="GROK_API_KEY"):
        adapter.prepare_request(_request(), taxonomy, environ={})
    assert adapter.credential_value({"GROK_API_KEY": "unit-test-value"}) == "unit-test-value"
    with pytest.raises(RemoteInferenceDisabledError):
        adapter.infer(_request(), taxonomy)


def test_provider_response_parser_accepts_mock_response_and_rejects_malformed_output() -> None:
    adapter = GrokRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="grok-4.6",
        api_key_env="GROK_API_KEY",
        base_url_env="GROK_BASE_URL",
    )
    response = _response(adapter)
    assert response.primary_domain == "D03"
    assert response.provider == "grok_relay"
    assert response.schema_hash == annotation_schema_hash()
    assert response.peer_annotation_visible is False

    failed = adapter.parse_response(
        _request(),
        {"output_text": '{"primary_domain": "D99"}'},
        attempt_id="bad-format",
    )
    assert failed.parse_status == "failed"
    assert failed.response is None
    assert failed.error_type == "AnnotationSchemaError"


def test_retry_is_item_level_and_supersedes_both_first_pass_rows() -> None:
    adapter_a = GrokRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="grok-4.6",
        api_key_env="GROK_API_KEY",
        base_url_env="GROK_BASE_URL",
    )
    adapter_b = GLMRelayAnnotationAdapter(
        annotator_id="annotator_b",
        annotation_pass="b",
        model="glm-5.3",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
    )
    usable = _response(adapter_a)
    unreadable = _response(adapter_b, output=_output(evidence_usability="unreadable"))
    decision = decide_item_retry(usable, unreadable)
    assert decision.required is True
    assert decision.triggered_by_a is False
    assert decision.triggered_by_b is True
    assert decision.reasons == ("b.evidence_usability=unreadable",)
    superseded_a, superseded_b = mark_first_pass_superseded(usable, unreadable)
    assert superseded_a.superseded is True
    assert superseded_b.superseded is True
    assert superseded_a.superseded_reason == "evidence_retry"
    assert MAX_EVIDENCE_RETRY_COUNT == 1
    assert can_retry(0) is True
    assert can_retry(1) is False

    partial_low = _response(
        adapter_a,
        output=_output(evidence_usability="partially_usable", confidence="low"),
    )
    assert partial_low.requires_evidence_retry is False
    assert decide_item_retry(partial_low, usable).required is False

    insufficient_fit = _response(
        adapter_a,
        output=_output(taxonomy_fit="insufficient_evidence"),
    )
    assert decide_item_retry(insufficient_fit, usable).required is True


def test_agreement_requires_same_final_contract_and_handles_conflicts() -> None:
    adapter_a = GrokRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="grok-4.6",
        api_key_env="GROK_API_KEY",
        base_url_env="GROK_BASE_URL",
    )
    adapter_b = GLMRelayAnnotationAdapter(
        annotator_id="annotator_b",
        annotation_pass="b",
        model="glm-5.3",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
    )
    a = _response(adapter_a)
    b = _response(adapter_b)
    assert classify_annotation_pair(a, b).status == "provisionally_agreed"

    cross_a = _response(adapter_a, output=_output(taxonomy_fit="cross_domain", secondary_domains=["D01"]))
    cross_b = _response(adapter_b, output=_output(taxonomy_fit="cross_domain", secondary_domains=["D02"]))
    assert classify_annotation_pair(cross_a, cross_b).reason == "cross_domain secondary_domains disagreement"

    final_b = _response(adapter_b, request=_request(evidence_revision="evidence-v0.3-ocr-final"))
    assert classify_annotation_pair(a, final_b).status == "conflict"
    with pytest.raises(ValueError, match="contract mismatch"):
        ensure_same_final_evidence(a, final_b)

    low_b = _response(adapter_b, output=_output(confidence="low"))
    assert classify_annotation_pair(a, low_b).reason == "low confidence requires review"

    unreadable_a = _response(adapter_a, output=_output(evidence_usability="unreadable"))
    assert classify_annotation_pair(unreadable_a, b).reason == (
        "Evidence retry remains required before final agreement"
    )


def test_gate2c_artifact_layout_and_row_identity_are_explicit() -> None:
    paths = gate2c_artifact_paths("/data/suzhe/migb", "g2c-dryrun-20260915T000000Z-abcdef1")
    assert tuple(paths) == GATE2C_ARTIFACT_NAMES
    assert str(paths["annotation_attempts.jsonl"]).endswith(
        "/phase2/runs/g2c-dryrun-20260915T000000Z-abcdef1/annotation_attempts.jsonl"
    )
    with pytest.raises(ValueError, match="directory-safe"):
        gate2c_artifact_paths("/data/suzhe/migb", "bad/run")

    adapter = GrokRelayAnnotationAdapter(
        annotator_id="annotator_a",
        annotation_pass="a",
        model="grok-4.6",
        api_key_env="GROK_API_KEY",
        base_url_env="GROK_BASE_URL",
    )
    response = _response(adapter)
    attempt = adapter.parse_response(
        _request(),
        {"output_text": json.dumps(_output(), ensure_ascii=False)},
        attempt_id="attempt-identity",
    )
    row = annotation_attempt_row(attempt, gate2c_run_id="g2c-test")
    assert artifact_row_identity(row) == (
        "g2c-test",
        "sample-1",
        "item-1",
        "annotator_a",
        "a",
        "attempt-identity",
    )
    assert row["relative_path"] == "group/item-1.pdf"
    final = final_annotation_row(
        response,
        gate2c_run_id="g2c-test",
        attempt_id="attempt-1",
        first_pass_artifact_ref="annotation_attempts.jsonl#attempt-1",
    )
    assert final["first_pass_artifact_ref"].endswith("attempt-1")
    assert final["relative_path"] == "group/item-1.pdf"
    with pytest.raises(ValueError, match="superseded"):
        final_annotation_row(
            response.with_superseded(),
            gate2c_run_id="g2c-test",
            attempt_id="attempt-1",
        )


def test_gate2c_config_declares_models_without_secrets() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["annotation_revision"] == "gate2c-annotator-config-v0.2"
    assert config["annotators"]["a"]["provider"] == "grok_relay"
    assert config["annotators"]["a"]["model"] == "grok-4.6"
    assert config["annotators"]["a"]["api_key_env"] == "GROK_API_KEY"
    assert config["annotators"]["a"]["base_url_env"] == "GROK_BASE_URL"
    assert config["annotators"]["b"]["provider"] == "glm_relay"
    assert config["annotators"]["b"]["model"] == "glm-5.3"
    assert config["annotators"]["b"]["api_key_env"] == "GLM_API_KEY"
    assert config["annotators"]["b"]["base_url_env"] == "GLM_BASE_URL"
    assert config["execution"]["preflight_endpoint"] == "/chat/completions"
    assert config["execution"]["model_discovery_endpoint"] == "/models"
    assert config["execution"]["provider_preflight_network_enabled"] is True
    assert config["execution"]["structured_output_capability_order"] == [
        "json_schema",
        "json_object",
        "prompt_json_only",
    ]
    assert config["execution"]["max_transport_retries"] == 3
    assert config["execution"]["max_format_retries"] == 1
    assert config["execution"]["max_evidence_retry_count"] == 1
    serialized = json.dumps(config).lower()
    assert "sk-" not in serialized
    assert "secret" not in serialized
