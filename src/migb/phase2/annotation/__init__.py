"""Offline Gate 2C annotation contracts and provider boundaries.

This package deliberately contains no remote inference client.  Adapters build
provider-shaped requests and parse supplied mock responses; a later execution
layer must explicitly own any network authorization.
"""

from .agreement import AgreementDecision, classify_annotation_pair, same_final_evidence
from .adapters import (
    AnnotationAdapter,
    GLMAnnotationAdapter,
    MissingCredentialsError,
    OpenAIAnnotationAdapter,
    RemoteInferenceDisabledError,
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
    "GLMAnnotationAdapter",
    "MissingCredentialsError",
    "OpenAIAnnotationAdapter",
    "RemoteInferenceDisabledError",
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
    "taxonomy_payload_hash",
    "validate_model_output",
]
