# Gate 2C-B 20-item Annotation Dry-run Report

Project: Mechanical Industry General Benchmark

Version: 0.1

Status: Blocked - Provider Preflight

Phase: Phase 2 - Taxonomy Calibration & Source Selection

Stage: `gate2c-b-dryrun`

## 1. Run Identity

| Field | Value |
| --- | --- |
| Run ID | Not created; blocked before runtime start |
| Git commit before preflight | `826e705` |
| Canonical worktree before preflight | `dirty=false` |
| Gate 2B source run | `p2b-20260915T023641Z-cbde565` |
| Runtime directory | Not created |
| Execution decision | `STOP` |

The remote project checkout was read-only checked at
`/data/suzhe/Machinery-Industry-Benchmark`; its HEAD was `b9988f3f45c81d2a9468e3ccdc4b434f60f54692`
and it was clean. It did not contain the Gate 2C-A configuration or annotation package from
`826e705`, so no remote code synchronization was attempted.

## 2. Provider Preflight

No credential values were printed, logged, persisted, or committed.

| Annotator | Requested provider/model | Credential presence | Synthetic call | Result |
| --- | --- | --- | ---: | --- |
| A | `openai / gpt-5.6-sol` | `OPENAI_API_KEY=false` | 0 | Blocked; request not attempted |
| B | configured GLM provider / `glm-5.2` | `GLM_API_KEY=false`; `GLM_BASE_URL=false` | 0 | Blocked; endpoint and capability not checked |

The offline adapter definitions specify `json_schema` for the OpenAI-shaped request and
`json_object` for the GLM-shaped request, but neither mode was presented as provider-verified.
No model availability, structured-output, usage metadata, request ID, or endpoint capability
claim was made.

## 3. Input and Execution Results

The fixed Gate 2B 20-item Main Review Set was not sent to either provider. No sampling,
replacement, dropping, OCR, annotation, parsing, agreement, conflict processing, or artifact
runtime was performed.

| Metric | Result |
| --- | --- |
| Dry-run target / processed | `20 / 0` |
| A final success / B final success | `0 / 0` |
| Total model requests | `0` |
| Transport retries / format retries | `0 / 0` |
| OCR retry items / OCR success | `0 / 0` |
| A2/B2 same Evidence | Not applicable |
| Deferred items | Not applicable |
| Agreement / conflict | Not applicable |
| Token usage / cost / latency | Not applicable |

## 4. Artifact Validation

No Runtime Annotation Artifact was created. The following files therefore do not exist for this
blocked attempt:

```text
annotation_attempts.jsonl
annotation_final.parquet
evidence_retries.parquet
taxonomy_agreements.parquet
taxonomy_conflicts.parquet
manifest.json
statistics.json
```

Source PDFs and the Gate 2B canonical Runtime Artifact were not accessed for execution and were
not modified.

## 5. Gate 2C-B Verdict

```text
Gate 2C-B: BLOCKED BY PROVIDER PREFLIGHT
```

The preflight cannot pass until the remote execution environment provides the required
`OPENAI_API_KEY`, `GLM_API_KEY`, and `GLM_BASE_URL` variables. After they are provisioned,
re-run the provider capability preflight first. Do not substitute another model, expose
credentials, or proceed directly to the fixed 20-item dry-run.

## 6. Next Step

Provide the three remote environment variables without recording their values, synchronize the
remote checkout with the reviewed Gate 2C-A commit, and rerun the two-provider preflight. Only
if both providers pass may a new dry-run Run ID and Runtime Artifact directory be created.

## 7. Provider Preflight Resolution

本节记录 2026-09-16 的新 Provider Preflight；第 2 节保留为此前 OpenAI/GLM 5.2 配置下的
历史阻塞记录。本次使用 configuration revision `gate2c-annotator-config-v0.2`，未修改
Prompt、Schema 或 Taxonomy revision。

No credential values, prefixes, suffixes, lengths, or Authorization headers were printed,
logged, persisted, or committed.

| Check | Annotator A / Grok | Annotator B / GLM |
| --- | --- | --- |
| Provider | `grok_relay` | `glm_relay` |
| Requested model | `grok-4.6` | `glm-5.3` |
| API Key presence | `GROK_API_KEY present=true` | `GLM_API_KEY present=true` |
| Credential isolation | Distinct from B | Distinct from A |
| `/models` availability | HTTP 200; exact requested model found | HTTP 200; exact requested model found |
| Synthetic endpoint | `http://139.196.137.155/v1/chat/completions` | `http://139.196.137.155/v1/chat/completions` |
| Structured-output mode | Unresolved; `json_schema` returned HTTP 400 | `json_schema` |
| Resolved model | `null` | `glm-5.3` |
| Schema validation | `false` (no successful annotation payload) | `true` |
| Request ID | `2dbca621-5f1b-4169-ac24-8ee95001e014` | `2026091611451456483f565dac4ddd` |
| Input / output tokens | `null / null` | `2296 / 1216` |
| Latency | `1791 ms` | `37539 ms` |
| Provider result | Failed synthetic preflight | Passed synthetic preflight |

Grok 的 HTTP 400 未被当前 explicit unsupported-format classifier 确认为可回退错误，因而
本次没有继续尝试 `json_object` 或 `prompt_json_only`；没有进行 alias 替换。GLM 返回的
`model` 与 requested model 完全一致。没有确认 silent model substitution。

```text
transport_security = plaintext_http
Technical Provider Preflight: BLOCKED BY PROVIDER PREFLIGHT
20-item Benchmark Dry-run: NO / NOT AUTHORIZED
```

Security Risk: API credentials and annotation payloads are not protected by TLS at the configured
relay endpoint. 本次 technical preflight 不因该风险自动阻塞；但 20-item Dry-run 仍未授权。
