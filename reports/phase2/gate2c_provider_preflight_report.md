# Gate 2C-B Provider Preflight Report

Project: Mechanical Industry General Benchmark

Version: 0.1

Status: Blocked - Provider Preflight

Phase: Phase 2 - Taxonomy Calibration & Source Selection

Stage: `gate2c-b-provider-preflight`

## 1. Execution Boundary

本报告只记录 Provider capability preflight，不是 Benchmark Run。由于当前执行环境没有
两组 Provider credentials，本次没有发起 `/models` 或 synthetic `/chat/completions` 请求，
没有读取 Source PDF，没有创建 Runtime Annotation Artifact，也没有执行 20-item 或
600-item Annotation。

| Field | Value |
| --- | --- |
| Run ID | Not created; preflight stopped before network request |
| Configuration revision | `gate2c-annotator-config-v0.2` |
| Prompt revision | `taxonomy-annotation-prompt-v0.1` |
| Schema revision | `taxonomy-annotation-schema-v0.1` |
| Taxonomy revision | `taxonomy-v0.1` |
| Synthetic input | `Synthetic Spur Gear Wear Study` only |
| Benchmark dry-run authorization | `false` |

## 2. Frozen Annotators

| Annotator | Provider ID | Requested model | API key environment | Base URL environment |
| --- | --- | --- | --- | --- |
| A | `grok_relay` | `grok-4.6` | `GROK_API_KEY` | `GROK_BASE_URL` |
| B | `glm_relay` | `glm-5.3` | `GLM_API_KEY` | `GLM_BASE_URL` |

Both endpoints use the Owner-specified shared Relay URL:

```text
http://139.196.137.155/v1
```

The URL is injected through the environment; it is not hard-coded into Python code or stored as
a credential. The two API Keys must be different and are never mixed.

## 3. Provider Preflight Results

No credential values, prefixes, suffixes, or lengths were printed, logged, persisted, or
committed.

| Check | Annotator A / Grok | Annotator B / GLM |
| --- | --- | --- |
| Credential presence | `GROK_API_KEY present=false` | `GLM_API_KEY present=false` |
| `/models` discovery | Not attempted; selected credential absent | Not attempted; selected credential absent |
| Available relevant models excerpt | Not available | Not available |
| Requested model accessible | Not verified | Not verified |
| Synthetic preflight | Not attempted | Not attempted |
| Resolved model | `null` | `null` |
| Structured output mode | Not resolved | Not resolved |
| Canonical Schema validation | Not evaluated | Not evaluated |
| Silent model substitution | Not evaluated; implementation fails closed | Not evaluated; implementation fails closed |

The preflight implementation uses `/models` with each selected Key independently, requires exact
model ID matching, then uses `/chat/completions` for the fixed synthetic request. Capability
negotiation order is `json_schema` → `json_object` → `prompt_json_only`; each mode is attempted
at most once and every successful response is checked by the local canonical Schema validator.
No alias is automatically accepted.

## 4. Transport Security

```text
transport_security = plaintext_http
```

Security Risk: API credentials and annotation payloads are not protected by TLS at the configured
relay endpoint.

This transport risk does not automatically block the technical Provider preflight. However,
20-item Benchmark Dry-run authorization remains pending explicit Project Owner acceptance of the
risk or a switch to an HTTPS endpoint.

## 5. Final Verdict

```text
Gate 2C-B Provider Preflight: BLOCKED BY PROVIDER PREFLIGHT
```

The required environment variables are:

```text
GROK_API_KEY
GROK_BASE_URL
GLM_API_KEY
GLM_BASE_URL
```

After they are injected without exposing their values, rerun this preflight. Do not substitute a
model alias, change the frozen model IDs, or run the 20-item dry-run directly.

## 6. Validation

| Check | Result |
| --- | --- |
| Mock/unit tests | `85 passed` |
| 20-item dry-run | Not run |
| 600-item annotation | Not run |
| OCR / Source Selection | Not run |
| Runtime Annotation Artifact | Not created |
