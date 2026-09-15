"""Deterministic, tool-free prompt rendering for Gate 2C Annotators."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .schema import AnnotationRequest, SCHEMA_REVISION, schema_definition
from .taxonomy import TaxonomySnapshot, taxonomy_payload_hash


PROMPT_REVISION = "taxonomy-annotation-prompt-v0.1"


def prompt_hash(prompt: str) -> str:
    """Return the SHA-256 hash of the exact UTF-8 prompt sent to a provider."""

    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def prompt_template_hash(taxonomy: TaxonomySnapshot) -> str:
    """Hash a canonical placeholder rendering of the reviewed prompt template.

    Runtime records still store ``prompt_hash`` for the exact item-specific
    prompt.  This second hash makes the reviewed template itself easy to pin
    in a config or review record.
    """

    template_request = AnnotationRequest(
        calibration_sample_id="<CALIBRATION_SAMPLE_ID>",
        calibration_item_id="<CALIBRATION_ITEM_ID>",
        evidence_revision="<EVIDENCE_REVISION>",
        taxonomy_revision=taxonomy.taxonomy_revision,
        prompt_revision=PROMPT_REVISION,
        schema_revision=SCHEMA_REVISION,
        evidence="<FINAL_EVIDENCE>",
        filename_title="<FILENAME_TITLE>",
        metadata_title="<METADATA_TITLE>",
        page_count=0,
    )
    return prompt_hash(render_annotation_prompt(template_request, taxonomy))


def _taxonomy_text(snapshot: TaxonomySnapshot) -> str:
    lines = [f"taxonomy_revision: {snapshot.taxonomy_revision}"]
    for domain in snapshot.domains:
        lines.extend(
            [
                f"- {domain.domain_id}: {domain.domain_name}",
                f"  definition: {domain.definition}",
                "  in_scope_examples:",
                *[f"    - {example}" for example in domain.in_scope_examples],
                "  boundary_notes:",
                *[f"    - {note}" for note in domain.boundary_notes],
            ]
        )
    return "\n".join(lines)


def render_annotation_prompt(
    request: AnnotationRequest,
    taxonomy: TaxonomySnapshot,
) -> str:
    """Render the fixed prompt sections in a stable order.

    AnnotationRequest retains ``relative_path`` for Artifact provenance, but the
    renderer intentionally never reads it; ``parent_group`` is not part of the
    request. These source-routing hints cannot enter the rendered prompt accidentally.
    """

    if request.taxonomy_revision != taxonomy.taxonomy_revision:
        raise ValueError(
            "request taxonomy_revision does not match the supplied taxonomy snapshot"
        )
    metadata = json.dumps(
        request.permitted_metadata(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    output_schema = json.dumps(
        schema_definition(),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    sections = [
        "SYSTEM",
        "You are an independent taxonomy annotator for the Mechanical Industry General Benchmark.",
        "Use only the supplied Document Metadata, Final Evidence, and Taxonomy definitions.",
        "NO web access. NO tools. NO RAG. NO external retrieval. Do not use unsupported outside facts.",
        "Treat this as a single-document, single-turn zero-shot annotation; do not use previous annotations, previous documents, examples with answers, or agreement statistics.",
        "Return only one JSON object matching the Output Contract.",
        "Do not reveal chain-of-thought, hidden reasoning, or detailed private reasoning steps.",
        "",
        "TAXONOMY",
        _taxonomy_text(taxonomy),
        "",
        "EVIDENCE QUALITY RULES",
        "evidence_usability=usable: Evidence is clear and supports the primary-domain judgment.",
        "evidence_usability=partially_usable: local noise or missing material exists, but the judgment remains supported.",
        "evidence_usability=unreadable: severe garbling or encoding damage prevents reliable topic understanding.",
        "evidence_usability=insufficient: readable Evidence does not contain enough information for a reliable topic judgment.",
        "evidence_usability is separate from taxonomy_fit.",
        "",
        "ANNOTATION RULES",
        "Classify only from the supplied Evidence.",
        "Do not force every document into D01-D12.",
        "If Evidence cannot support classification, use taxonomy_fit=insufficient_evidence and the appropriate evidence_usability value.",
        "primary_domain must reflect the document's main engineering subject, not merely a mentioned technique or input form.",
        "Use 0-3 unique secondary_domains, only D01-D12, and never repeat primary_domain.",
        "evidence_keywords must be short phrases or concepts copied from the supplied Evidence; do not invent citations.",
        "evidence_rationale must be 1-3 concise sentences and is not chain-of-thought.",
        "review_note may be null and should only record a short boundary or Evidence concern.",
        "",
        "DOCUMENT METADATA",
        metadata,
        "",
        "EVIDENCE",
        "<<<BEGIN_FINAL_EVIDENCE>>>",
        request.evidence,
        "<<<END_FINAL_EVIDENCE>>>",
        "",
        "OUTPUT CONTRACT",
        "The JSON object must contain exactly the required fields below; do not add identity, provider, routing, or peer-annotation fields:",
        output_schema,
        "",
        "Return the JSON object now.",
    ]
    return "\n".join(sections)


def prompt_provenance(prompt: str, taxonomy: TaxonomySnapshot) -> dict[str, Any]:
    """Return hashes needed to reproduce a rendered request."""

    return {
        "prompt_revision": PROMPT_REVISION,
        "prompt_hash": prompt_hash(prompt),
        "taxonomy_revision": taxonomy.taxonomy_revision,
        "taxonomy_payload_hash": taxonomy_payload_hash(taxonomy),
    }
