"""Gate 2C annotation contracts and explicit provider boundaries.

Adapters build provider-shaped requests and parse supplied mock responses.
The separate preflight module owns the narrowly scoped, explicitly authorized
model-discovery and synthetic capability checks; production annotation remains
outside this package boundary.
"""

from .agreement import AgreementDecision, classify_annotation_pair, same_final_evidence
from .adapters import (
    AnnotationAdapter,
    GLMRelayAnnotationAdapter,
    GrokRelayAnnotationAdapter,
    MissingCredentialsError,
    OpenAICompatibleAnnotationAdapter,
    RemoteInferenceDisabledError,
    STRUCTURED_OUTPUT_MODES,
)
from .preflight import (
    CredentialIsolationError,
    DualProviderPreflightResult,
    ModelDiscoveryResult,
    ProviderPreflightResult,
    RelayHTTPResponse,
    SyntheticPreflightAttempt,
    credentials_are_distinct,
    discover_models,
    load_provider_environment,
    owner_verified_model_discovery,
    require_distinct_credentials,
    run_dual_provider_preflight,
    run_provider_preflight,
    synthetic_annotation_request,
    synthetic_preflight_attempt,
)
from .retry import RetryDecision, decide_item_retry, mark_first_pass_superseded
from .prompt import PROMPT_REVISION, prompt_hash, prompt_template_hash, render_annotation_prompt
from .schema import (
    AnnotationAttempt,
    AnnotationRequest,
    AnnotationResponse,
    AnnotationSchemaError,
    annotation_schema_hash,
    validate_model_output,
)
from .taxonomy import (
    TaxonomySnapshot,
    TaxonomySnapshotError,
    load_taxonomy_snapshot,
    taxonomy_payload_hash,
)

__all__ = [
    "AgreementDecision",
    "AnnotationAdapter",
    "AnnotationAttempt",
    "AnnotationRequest",
    "AnnotationResponse",
    "AnnotationSchemaError",
    "GLMRelayAnnotationAdapter",
    "GrokRelayAnnotationAdapter",
    "MissingCredentialsError",
    "OpenAICompatibleAnnotationAdapter",
    "RemoteInferenceDisabledError",
    "STRUCTURED_OUTPUT_MODES",
    "CredentialIsolationError",
    "DualProviderPreflightResult",
    "ModelDiscoveryResult",
    "ProviderPreflightResult",
    "RelayHTTPResponse",
    "SyntheticPreflightAttempt",
    "RetryDecision",
    "TaxonomySnapshot",
    "TaxonomySnapshotError",
    "PROMPT_REVISION",
    "annotation_schema_hash",
    "classify_annotation_pair",
    "decide_item_retry",
    "load_taxonomy_snapshot",
    "mark_first_pass_superseded",
    "prompt_hash",
    "prompt_template_hash",
    "render_annotation_prompt",
    "same_final_evidence",
    "credentials_are_distinct",
    "discover_models",
    "load_provider_environment",
    "owner_verified_model_discovery",
    "require_distinct_credentials",
    "run_dual_provider_preflight",
    "run_provider_preflight",
    "synthetic_annotation_request",
    "synthetic_preflight_attempt",
    "taxonomy_payload_hash",
    "validate_model_output",
]
