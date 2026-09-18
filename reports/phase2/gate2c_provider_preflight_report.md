# Gate 2C-B Provider Preflight Report

Project: Mechanical Industry General Benchmark

Version: 0.1

Status: Blocked - Provider Preflight

Phase: Phase 2 - Taxonomy Calibration & Source Selection

Stage: `gate2c-b-provider-preflight`

## 1. Execution Boundary

本报告只记录 Provider capability preflight，不是 Benchmark Run。本次只加载本地 Provider
配置，分别调用 `/models` 和固定 synthetic `/chat/completions`；没有读取 Source PDF，
没有创建 Runtime Annotation Artifact，也没有执行 20-item 或 600-item Annotation。

| Field | Value |
| --- | --- |
| Run ID | Not created; this is a synthetic-only preflight |
| Configuration revision | `gate2c-annotator-config-v0.2` |
| Prompt revision | `taxonomy-annotation-prompt-v0.1` |
| Schema revision | `taxonomy-annotation-schema-v0.1` |
| Taxonomy revision | `taxonomy-v0.1` |
| Synthetic input | `Synthetic Spur Gear Wear Study` only |
| Provider env file | `configs/phase2/gate2c_provider.local.env` (Git-ignored, owner-only) |
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
| Credential presence | `GROK_API_KEY present=true` | `GLM_API_KEY present=true` |
| Credential isolation | Both credentials present and distinct | Both credentials present and distinct |
| `/models` discovery | HTTP 200; exact `grok-4.6` found | HTTP 200; exact `glm-5.3` found |
| Available relevant models excerpt | Contains requested model `grok-4.6` | Contains requested model `glm-5.3` |
| Requested model accessible | `true` | `true` |
| Synthetic endpoint | `/chat/completions` | `/chat/completions` |
| Synthetic preflight | Failed at `json_schema`, HTTP 400 | Passed at `json_schema`, HTTP 200 |
| Resolved model | `null` (no response model on failed request) | `glm-5.3` |
| Structured output mode | Not resolved | `json_schema` |
| Canonical Schema validation | `false` (no successful annotation payload) | `true` |
| Request ID | `2dbca621-5f1b-4169-ac24-8ee95001e014` | `2026091611451456483f565dac4ddd` |
| Input / output tokens | `null / null` | `2296 / 1216` |
| Latency | `1791 ms` | `37539 ms` |
| Silent model substitution | No confirmed substitution; resolved model unavailable | No; response model exactly matched |

The preflight implementation uses `/models` with each selected Key independently, requires exact
model ID matching, then uses `/chat/completions` for the fixed synthetic request. Capability
negotiation order is `json_schema` → `json_object` → `prompt_json_only`; each mode is attempted
at most once and every successful response is checked by the local canonical Schema validator.
No alias is automatically accepted. Grok's HTTP 400 did not satisfy the current explicit
unsupported-format classifier, so no fallback mode was attempted in this run; the Provider
Preflight therefore remains blocked and requires a reviewed follow-up, without changing model ID.

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

The required environment variables are loaded from the Git-ignored local file:

```text
GROK_API_KEY
GROK_BASE_URL
GLM_API_KEY
GLM_BASE_URL
```

Grok model availability and GLM model availability both passed. GLM synthetic inference passed;
Grok synthetic inference failed at the first structured-output attempt with HTTP 400. Do not
substitute a model alias, change the frozen model IDs, or run the 20-item dry-run directly.

## 6. Validation

| Check | Result |
| --- | --- |
| Mock/unit tests | `87 passed` |
| Technical Provider Preflight | `BLOCKED` because Grok synthetic preflight failed |
| 20-item dry-run | Not run |
| 600-item annotation | Not run |
| OCR / Source Selection | Not run |
| Runtime Annotation Artifact | Not created |

## 7. Current Owner Decision: GLM-only Configuration

本节为当前有效 Provider Preflight 结果；第 2–6 节中的 Grok / GLM 组合属于历史配置。
Project Owner 因 Grok 4.6 服务预计不可用，取消 Grok Annotator，并将 configuration
revision 更新为 `gate2c-annotator-config-v0.3`。

| Check | Annotator A | Annotator B |
| --- | --- | --- |
| Annotator ID | `annotator_a` | `annotator_b` |
| Provider | `glm_relay` | `glm_relay` |
| Requested model | `glm-5.3` | `glm-5.2` |
| Credential presence | `GLM_API_KEY present=true` | Shared `GLM_API_KEY present=true` |
| Credential policy | Shared GLM credential allowed | Shared GLM credential allowed |
| Model discovery | Owner-verified; exact model available | Owner-verified; exact model available |
| Synthetic request count | `1` | `1` |
| Structured output attempted | `json_schema` | `json_schema` |
| HTTP status | `200` | `200` |
| Resolved model | `glm-5.3` | `glm-5.3` |
| Model match | `true` | `false` |
| Canonical Schema validation | `false` (`AnnotationSchemaError`) | `true` |
| Latency | `22924 ms` | `20967 ms` |
| Input / output / reasoning tokens | `2296 / 1544 / 1326` | `2296 / 1445 / 1251` |
| Result | Failed Schema Validation | Failed resolved-model match |

The A/B requests used the same synthetic Evidence, Taxonomy snapshot, Prompt semantics and
Schema, but were sent as independent requests. The `glm-5.2` request resolved to `glm-5.3`,
which is a confirmed silent model substitution and is rejected. The `glm-5.3` request returned
the requested model but failed local canonical Schema Validation. No `/models` request was made
in this run because discovery was explicitly recorded as `owner_verified`.

```text
transport_security = plaintext_http
Gate 2C-B Provider Preflight = BLOCKED BY PROVIDER PREFLIGHT
20-item Dual-Annotator Dry-run = NOT AUTHORIZED
```

No credential values, prefixes, suffixes, lengths, or Authorization headers were printed,
logged, persisted, or committed.

## 8. Current Validation

| Check | Result |
| --- | --- |
| Mock/unit tests | `89 passed` |
| `/models` request | Not made; discovery source was `owner_verified` |
| Synthetic requests | `2 total`, one per independent Annotator |
| Technical Provider Preflight | `BLOCKED` |
| 20-item dry-run | Not run |
| 600-item annotation | Not run |
| OCR / Source Selection | Not run |
| Runtime Annotation Artifact | Not created |
