"""Provider-shaped request builders with a deliberately disabled inference boundary."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from .prompt import PROMPT_REVISION, prompt_hash, render_annotation_prompt
from .schema import (
    AnnotationAttempt,
    AnnotationRequest,
    AnnotationResponse,
    AnnotationSchemaError,
    SCHEMA_REVISION,
    annotation_schema_hash,
    schema_definition,
    validate_model_output,
)
from .taxonomy import TaxonomySnapshot, taxonomy_payload_hash


class RemoteInferenceDisabledError(RuntimeError):
    """Raised because Gate 2C-A intentionally has no remote inference runner."""


class MissingCredentialsError(RuntimeError):
    """Raised when an explicitly requested credential is absent from the environment."""


class AnnotationAdapter(ABC):
    """Common offline boundary for provider-specific request construction."""

    provider: str

    def __init__(
        self,
        *,
        annotator_id: str,
        annotation_pass: str,
        model: str,
        api_key_env: str,
        max_output_tokens: int = 2048,
        base_url_env: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        if not annotator_id.strip() or not annotation_pass.strip() or not model.strip():
            raise ValueError("annotator_id, annotation_pass, and model are required")
        if not api_key_env.strip():
            raise ValueError("api_key_env is required")
        if max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        self.annotator_id = annotator_id
        self.annotation_pass = annotation_pass
        self.model = model
        self.api_key_env = api_key_env
        self.max_output_tokens = max_output_tokens
        self.base_url_env = base_url_env
        self.reasoning_effort = reasoning_effort

    def credential_value(self, environ: Mapping[str, str] | None = None) -> str:
        """Read a key only from the process environment; never return it in a request."""

        source = os.environ if environ is None else environ
        value = source.get(self.api_key_env)
        if not value:
            raise MissingCredentialsError(
                f"missing credential environment variable: {self.api_key_env}"
            )
        return value

    def prepare_request(
        self,
        request: AnnotationRequest,
        taxonomy: TaxonomySnapshot,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Validate environment availability and then build a non-network request."""

        self.credential_value(environ)
        if self.base_url_env is not None:
            source = os.environ if environ is None else environ
            if not source.get(self.base_url_env):
                raise MissingCredentialsError(
                    f"missing endpoint environment variable: {self.base_url_env}"
                )
        return self.build_request(request, taxonomy)

    def build_request(
        self,
        request: AnnotationRequest,
        taxonomy: TaxonomySnapshot,
    ) -> dict[str, Any]:
        if request.taxonomy_revision != taxonomy.taxonomy_revision:
            raise ValueError("request taxonomy_revision does not match taxonomy snapshot")
        if request.prompt_revision != PROMPT_REVISION:
            raise ValueError(
                f"request prompt_revision must be {PROMPT_REVISION}; got {request.prompt_revision}"
            )
        if request.schema_revision != SCHEMA_REVISION:
            raise ValueError(
                f"request schema_revision must be {SCHEMA_REVISION}; got {request.schema_revision}"
            )
        rendered_prompt = render_annotation_prompt(request, taxonomy)
        return {
            "provider": self.provider,
            "annotator_id": self.annotator_id,
            "annotation_pass": self.annotation_pass,
            "payload": self._build_provider_payload(rendered_prompt),
            "provenance": {
                "prompt_revision": request.prompt_revision,
                "prompt_hash": prompt_hash(rendered_prompt),
                "taxonomy_revision": taxonomy.taxonomy_revision,
                "taxonomy_payload_hash": taxonomy_payload_hash(taxonomy),
                "schema_revision": request.schema_revision,
                "schema_hash": annotation_schema_hash(),
                "peer_annotation_visible": False,
            },
        }

    @abstractmethod
    def _build_provider_payload(self, prompt: str) -> dict[str, Any]:
        """Build a provider request body without credentials or network effects."""

    def infer(self, request: AnnotationRequest, taxonomy: TaxonomySnapshot) -> None:
        """Keep actual remote inference out of Gate 2C-A."""

        raise RemoteInferenceDisabledError(
            "remote model inference is disabled during Gate 2C-A; use mock responses only"
        )

    def parse_response(
        self,
        request: AnnotationRequest,
        raw_response: Any,
        *,
        attempt_id: str,
        request_id: str | None = None,
        resolved_model: str | None = None,
        model_version_if_available: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        reasoning_tokens_if_available: int | None = None,
        latency_ms: int | None = None,
        provenance: Mapping[str, Any] | None = None,
    ) -> AnnotationAttempt:
        """Parse a supplied mock/provider-shaped response without repairing it with an LLM."""

        try:
            model_output = _extract_model_output(raw_response)
            validated = validate_model_output(model_output)
            response_provenance = {} if provenance is None else dict(provenance)
            response = AnnotationResponse(
                calibration_sample_id=request.calibration_sample_id,
                calibration_item_id=request.calibration_item_id,
                annotator_id=self.annotator_id,
                annotation_pass=self.annotation_pass,
                taxonomy_revision=request.taxonomy_revision,
                prompt_revision=request.prompt_revision,
                schema_revision=request.schema_revision,
                evidence_revision=request.evidence_revision,
                relative_path=request.relative_path,
                review_status=(
                    "annotated_a" if self.annotation_pass.lower().endswith("a") else "annotated_b"
                ),
                provider=self.provider,
                requested_model=self.model,
                resolved_model=resolved_model,
                model_version_if_available=model_version_if_available,
                request_id=request_id,
                started_at=started_at,
                completed_at=completed_at,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reasoning_tokens_if_available=reasoning_tokens_if_available,
                latency_ms=latency_ms,
                prompt_hash=response_provenance.get("prompt_hash"),
                taxonomy_payload_hash=response_provenance.get("taxonomy_payload_hash"),
                schema_hash=response_provenance.get("schema_hash", annotation_schema_hash()),
                peer_annotation_visible=False,
                **validated,
            )
            return AnnotationAttempt(
                attempt_id=attempt_id,
                request=request,
                annotator_id=self.annotator_id,
                annotation_pass=self.annotation_pass,
                parse_status="passed",
                response=response,
            )
        except (AnnotationSchemaError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return AnnotationAttempt(
                attempt_id=attempt_id,
                request=request,
                annotator_id=self.annotator_id,
                annotation_pass=self.annotation_pass,
                parse_status="failed",
                error_type=type(exc).__name__,
                error_message=str(exc),
            )


class OpenAIAnnotationAdapter(AnnotationAdapter):
    """OpenAI request builder; it never imports or calls an OpenAI SDK."""

    provider = "openai"

    def _build_provider_payload(self, prompt: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_output_tokens": self.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "taxonomy_annotation",
                    "strict": True,
                    "schema": schema_definition(),
                },
            },
        }
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort
        return payload


class GLMAnnotationAdapter(AnnotationAdapter):
    """GLM-compatible request builder with no provider SDK or network behavior."""

    provider = "glm"

    def _build_provider_payload(self, prompt: str) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }


def _extract_model_output(raw_response: Any) -> Mapping[str, Any]:
    if isinstance(raw_response, str):
        parsed = json.loads(raw_response)
        if not isinstance(parsed, Mapping):
            raise AnnotationSchemaError("JSON response must decode to an object")
        return parsed
    if not isinstance(raw_response, Mapping):
        raise AnnotationSchemaError("provider response must be an object or JSON string")

    if all(field in raw_response for field in ("primary_domain", "secondary_domains")):
        return raw_response
    output_text = raw_response.get("output_text")
    if isinstance(output_text, str):
        return _extract_model_output(output_text)
    choices = raw_response.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0]
        if isinstance(choice, Mapping):
            message = choice.get("message")
            if isinstance(message, Mapping):
                content = message.get("content")
                if isinstance(content, str):
                    return _extract_model_output(content)
                if isinstance(content, list):
                    text_parts = [
                        item.get("text")
                        for item in content
                        if isinstance(item, Mapping) and isinstance(item.get("text"), str)
                    ]
                    if text_parts:
                        return _extract_model_output("".join(text_parts))
    content = raw_response.get("content")
    if isinstance(content, str):
        return _extract_model_output(content)
    raise AnnotationSchemaError("could not locate a structured annotation object in response")
