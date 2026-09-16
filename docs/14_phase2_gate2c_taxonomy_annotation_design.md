# Phase 2 Gate 2C Taxonomy Annotation Execution Design

Project: Mechanical Industry General Benchmark
Document: Phase 2 Gate 2C Taxonomy Annotation Execution Design
Version: 0.1
Status: Reviewed - Provider Preflight Blocked
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2C-B Provider Preflight
Evidence Contract: `evidence-v0.3-adaptive-v0.1`

## 1. 文档目的与边界

Gate 2B 已通过。Project Owner 接受 annotation-side Retry，并拒绝 automatic
pre-annotation OCR trigger。本文件冻结 Gate 2C-A 的执行设计，以及 Gate 2C-B 的首轮
Annotator model/provider 候选、Annotation Artifact、Evidence retry semantics 和 20-item
dry-run 协议。

本文件不执行 20-item 或 600-item Annotation，不执行 Source Selection，也不生成
Benchmark、Ground Truth 或新的 767-item OCR Runtime。Provider capability preflight 只允许
按本文件的 synthetic contract 发起最小探测请求，不得发送真实 Benchmark Item。
Taxonomy 的具体内容仍以现有 Taxonomy Design 和后续正式决策为准，本文件不重新设计
Domain Taxonomy。

## 2. 进入条件与输入边界

Gate 2C 只能在 Gate 2B 的以下结果已被接受后按子阶段进入：

- Sampling / Artifact Pipeline：PASS；
- PyMuPDF primary Evidence：16 / 20 sufficient；
- Validated RapidOCR fallback：4 / 4 Problem items sufficient；
- Control regression：4 / 4 sufficient；
- RapidOCR `3.9.2`、ONNX Runtime `1.23.2`、`CPUExecutionProvider`；
- Default OCR render DPI：200；
- 20 / 20 reviewed Main items 存在 primary 或 validated fallback Evidence 路径。

Gate 2B canonical Runtime 位于：

```text
/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565/
```

Gate 2C 初始输入使用既有 `calibration_sample.parquet`、
`calibration_evidence.jsonl`、`manifest.json` 和 `statistics.json`。这些 Gate 2B 原始
Artifact 必须保持 immutable。Gate 2C 不预先对全部 767 条执行 OCR；只在 Annotator
输出触发时，对对应 Item 执行最多一次 Conditional RapidOCR fallback。

`text_absent` Audit Pool 的 60 条仍保持独立处理边界，不因本设计自动进入 Main
Annotation；`source_quality_exception` 的 7 条仍为 `not_applicable`。

## 3. Gate 2C 子阶段

Gate 2C 属于 Phase 2 内部执行分层，不改变项目 Phase 定义：

| Sub-gate | 名称 | 本阶段目的 | 当前状态 |
| --- | --- | --- | --- |
| Gate 2C-A | Annotation Execution Design Freeze | 冻结 Annotator 配置、prompt、Schema、retry、Artifact 和处理逻辑 | PASSED |
| Gate 2C-B | 20-item Annotation Dry-run | 验证 A/B 独立标注、Evidence retry、重跑和 Artifact 写入 | Provider preflight blocked |
| Gate 2C-C | Full 600-item Taxonomy Calibration | 在 dry-run 通过后执行完整 Main Sample 双 Annotator Calibration | 未授权 |
| Gate 2C-D | Calibration Review + Taxonomy Decision + Source Selection Policy Freeze | 汇总 agreement/conflict、人工复核和 Source Selection Policy 决策 | 未授权 |

在 Gate 2C-B 获得单独授权前，不执行任何 20-item dry-run 或完整 600-item 双 Annotator
Annotation。

## 4. Evidence v0.3 Adaptive Workflow

所有 Gate 2C Item 按以下七个 Stage 处理：

```text
Stage 1  PyMuPDF primary Evidence
Stage 2  Independent Taxonomy Annotation A/B
Stage 3  Evidence insufficiency detection
Stage 4  Conditional RapidOCR fallback
Stage 5  Final Evidence regeneration
Stage 6  Restart Annotation A/B for that item
Stage 7  Agreement / Conflict processing
```

Stage 1 使用既有 Primary Evidence 和 Source Provenance。Stage 2 的 A/B 不互相查看输出，
并使用相同的 Evidence Contract、Taxonomy revision、annotation prompt revision 和
schema revision。Stage 3 只根据 Annotation output 检查 Evidence 是否不足，不使用
filename、parent_group、publication year、Problem item ID 或固定 Unicode threshold。

Stage 4 只有在 retry 条件满足时执行一次 RapidOCR。Stage 5 生成同一份
`final_evidence_revision` 和对应 provenance。Stage 6 使用该相同 Final Evidence 重跑 A/B。
只有最终的 A2/B2 进入 Stage 7。

## 5. Annotation Schema 增量

Gate 2C 使用 `docs/11_phase2_taxonomy_calibration_and_source_selection.md` 中已有的
Annotation Schema，并增加以下独立字段：

### 5.1 Canonical Annotation Record Fields

每条最终有效 Annotation Record 至少包含以下字段：

| Field group | Fields |
| --- | --- |
| Identity | `gate2c_run_id`、`annotation_record_id`、`calibration_sample_id`、`calibration_item_id`、`annotator_id`、`annotation_pass` |
| Source provenance | `relative_path`（仅保留在 Artifact；不得进入 Annotator Prompt） |
| Contract revisions | `taxonomy_revision`、`prompt_revision`、`schema_revision`、`evidence_revision` |
| Taxonomy | `primary_domain`、`secondary_domains`、`taxonomy_fit`、`confidence` |
| Evidence support | `evidence_usability`、`evidence_keywords`、`evidence_rationale`、`review_note` |
| Routing / review | `requires_evidence_retry`、`review_status`、`superseded`、`superseded_reason` |
| Provider metadata | `provider`、`requested_model`、`resolved_model`、`model_version_if_available`、`request_id`、`started_at`、`completed_at`、`input_tokens`、`output_tokens`、`reasoning_tokens_if_available`、`latency_ms` |
| Reproducibility | `prompt_hash`、`taxonomy_payload_hash`、`schema_hash`、`peer_annotation_visible` |

Provider 不可提供的 metadata 字段写 `null`，不得伪造。`peer_annotation_visible` 必须为
`false`。

| Field | 说明 |
| --- | --- |
| `evidence_usability` | 允许值：`usable` / `partially_usable` / `unreadable` / `insufficient` |
| `requires_evidence_retry` | Item-level derived flag；任一独立 Annotator 触发 Evidence retry 时为 `true` |

`evidence_usability` 与 `taxonomy_fit` 是两个不同维度：

- `evidence_usability` 描述当前 Evidence 是否足以支持标注；
- `taxonomy_fit` 描述文档与现有 Taxonomy 的关系；
- 不得用 `taxonomy_fit` 替代 `evidence_usability`，也不得把二者混为一个质量字段。

如果任意一个独立 Annotator 返回：

```text
evidence_usability in {unreadable, insufficient}
```

则：

```text
requires_evidence_retry = true
```

如果 `taxonomy_fit = insufficient_evidence`，同样设置
`requires_evidence_retry = true`。`partially_usable` 不单独触发 OCR；如果 Annotator
仍能确定 `primary_domain` 且 `confidence != low`，可以继续进入 Agreement Logic。
`confidence = low` 进入 Review Queue，但不单独触发 OCR。

### 5.2 Canonical Enum 与输出约束

- `primary_domain`：`D01`–`D12`、`OUT_OF_SCOPE`、`UNCERTAIN`；
- `secondary_domains`：JSON array，0–3 个、唯一、只能为 D01–D12，且不能包含 `primary_domain`；
- `taxonomy_fit`：`clear_fit` / `cross_domain` / `ambiguous` / `taxonomy_gap` /
  `out_of_scope` / `insufficient_evidence`；
- `confidence`：`high` / `medium` / `low`，不使用数字概率；
- `evidence_keywords`：`array[str]`，建议 0–8 个，只能来自输入 Evidence 的短语或概念；
- `evidence_rationale`：1–3 个简洁句子，不要求或保存 Chain-of-Thought；
- `review_note`：短文本或 `null`。

## 6. Retry 与 A/B 一致性 Contract

### 6.1 First-pass 处理

Annotation A1 和 Annotation B1 都使用同一份 PyMuPDF Primary Evidence。A1 不看 B1，B1
不看 A1。每个 Annotator 仍独立记录 `annotator_id`、`annotation_pass`、model/provider/version
（首轮候选配置已冻结；可用版本和 Provider capability check 结果按 Run manifest 记录）、
prompt revision、schema revision、Taxonomy revision 和 inference parameters。

### 6.2 Retry 触发与首轮结果处理

如果 A 或 B 任意一方触发 Evidence retry：

1. 将 `requires_evidence_retry` 设为 `true`；
2. 丢弃 A1/B1 作为最终判定的资格，只保留其 audit provenance；
3. 对该 Item 只执行一次 RapidOCR fallback；
4. 生成 `final_evidence_revision`；
5. 使用相同 Final Evidence 重跑 A2/B2；
6. 只有 A2/B2 进入 agreement、conflict 和 taxonomy metrics。

因此：

```text
max_evidence_retry_count = 1
```

禁止出现 A 使用 PyMuPDF Evidence、B 使用 OCR Evidence 的不对称输入。A2/B2 必须使用：

```text
same OCR Final Evidence
same taxonomy revision
same annotation prompt revision
same schema revision
```

如果 RapidOCR 后仍为 `unreadable` 或 `insufficient`，该 Item 标记为 `deferred` 并进入
Review Queue，不得无限 retry，也不得自动标记为 `sufficient`。

### 6.3 Agreement / Conflict

最终 Agreement / Conflict 处理沿用现有 Taxonomy Annotation Contract：

- 不因某一个 Annotator 的首轮结果更完整而静默选择该结果；
- `primary_domain`、`taxonomy_fit`、cross-domain 的 `secondary_domains` 或低置信度冲突
  均进入既定 Review Queue；
- `taxonomy_gap`、`out_of_scope`、`ambiguous` 和 `insufficient_evidence` 不得被隐藏；
- 详细 agreement / conflict logic 以 docs/11 和 Gate 2C-A 冻结的 contract 为准。

## 7. Gate 2C Artifact Layout

每次 Gate 2C Run 使用独立的 `<gate2c_run_id>`，采用合并 Attempt 与 Final 的 Artifact
设计，避免为同一内容维护四份重复文件。Artifact Layout 为：

```text
/data/suzhe/migb/
  phase2/
    runs/
      <gate2c_run_id>/
        annotation_attempts.jsonl
        annotation_final.parquet
        evidence_retries.parquet
        taxonomy_agreements.parquet
        taxonomy_conflicts.parquet
        manifest.json
        statistics.json
```

| Artifact | 用途 |
| --- | --- |
| `annotation_attempts.jsonl` | 每个实际模型 attempt，包括 A1、B1、A2、B2 和允许的 format retry，以及配置 provenance |
| `annotation_final.parquet` | 每个 `calibration_item_id × annotator_id` 一行，只指向最终有效 Annotation |
| `evidence_retries.parquet` | 每个发生 retry 的 Item 一行，记录触发方、原因、前后 Evidence revision 和 OCR 参数 |
| `taxonomy_agreements.parquet` | 通过既定 Agreement Logic 的合并结果 |
| `taxonomy_conflicts.parquet` | 冲突、低置信度、taxonomy gap 或需人工 Review 的结果 |
| `manifest.json` | Run identity、输入 Artifact、版本、Schema、配置引用和 checksum |
| `statistics.json` | item accounting、retry、agreement、conflict、deferred 和错误统计 |

如果某 Item 没有 retry，`annotation_final.parquet` 可以通过
`first_pass_artifact_ref` 或等价 reference 表示 first pass 即 final，不要求复制大型
Evidence 文本。若发生 retry，`annotation_attempts.jsonl` 必须同时保留 A1/B1 audit
provenance 与 A2/B2 最终结果；`annotation_final.parquet` 只保留 A2/B2 的最终有效引用。

具体字段、序列化方式、checksum convention 和 failure semantics 已在 Gate 2C-A 冻结；
本文件当前不创建上述远程目录或 Runtime Artifact。

## 8. Annotator Configuration Freeze Boundary

以下配置在 Gate 2C-A 中已冻结；Provider capability check 尚未确定的运行时参数保持
`TBD`：

```text
Annotator A model
Annotator B model
model versions
API / provider
temperature
max tokens
taxonomy definition payload
annotation prompt
output JSON schema
retry semantics
OCR fallback integration
artifact schema
run identity
rate limiting
error / retry handling
agreement logic
conflict logic
review queue
cost / accounting
```

Actual Model A / Model B 的首轮候选已在本次 Gate 2C-A 中冻结；Provider capability check
尚未完成的具体 inference parameters 仍保持 `TBD`。本次只允许执行独立的 Provider
capability preflight，不允许进入 20-item 或 600-item Annotation。

### 8.1 Frozen Annotator Configuration

Gate 2C-B 的首轮候选配置冻结为（configuration revision：
`gate2c-annotator-config-v0.2`）：

| Annotator | Provider | Model | Low-variance setting | Credential environment variable |
| --- | --- | --- | --- | --- |
| A (`annotator_a`) | `grok_relay` | `grok-4.6` | capability negotiation；具体参数 `TBD` | `GROK_API_KEY`；endpoint `GROK_BASE_URL` |
| B (`annotator_b`) | `glm_relay` | `glm-5.3` | capability negotiation；具体参数 `TBD` | `GLM_API_KEY`；endpoint `GLM_BASE_URL` |

配置文件为 `configs/phase2/gate2c_annotation_v0.1.yaml`。两个 Annotator 使用同一
OpenAI-compatible Relay base URL，但必须使用不同的 API Key；Provider identity 仍分别
记录为 `grok_relay` 和 `glm_relay`。当前 Owner 提供的 endpoint 为：

```text
GROK_BASE_URL=http://139.196.137.155/v1
GLM_BASE_URL=http://139.196.137.155/v1
```

运行时只从环境变量读取 URL 和 Key，不把 Key 写入配置或 Artifact。不设置或硬编码
`temperature`、`top_p`；Provider 支持的低随机性参数必须在 dry-run 前通过 capability
check 并写入 Run manifest。首选 endpoint 为 `/chat/completions`，model discovery 使用
`/models`。`structured_output_mode` 不预先假定，而是按
`json_schema → json_object → prompt_json_only` 顺序协商；每种模式最多一次 synthetic
call。`max_output_tokens=2048`、`max_transport_retries=3`、`max_format_retries=1` 已
记录在配置中。

为便于本地或远程执行，预检脚本默认读取仓库内被 Git 忽略的
`configs/phase2/gate2c_provider.local.env`；也可以通过 `MIGB_PROVIDER_ENV_FILE` 或
`--provider-env-file` 指定仓库外文件。该文件必须仅限 owner 读取（权限 `600`），进程
环境变量优先于文件内容。该文件不得提交，Key 也不得复制到任何 tracked 文件。

API Key 只能从环境变量读取；真实值不得写入 YAML、JSON、源代码、manifest、report 或
Git。生产式 Benchmark Annotation 仍必须保持关闭；本次 Provider preflight 只使用固定
synthetic Evidence。Relay 当前为明文 HTTP：

```text
transport_security = plaintext_http
```

Security Risk: API credentials and annotation payloads are not protected by TLS at the
configured relay endpoint. 该风险不自动阻塞 technical preflight；但在进入 20-item
Benchmark Dry-run 前，需要 Project Owner 明确接受该风险，或切换到 HTTPS endpoint。

### 8.2 Taxonomy Snapshot

Annotator 使用由 `docs/02_benchmark_taxonomy.md` 生成的独立快照：

```text
path: configs/phase2/taxonomy_annotation_v0.1.yaml
taxonomy_revision: taxonomy-v0.1
source_document: docs/02_benchmark_taxonomy.md
source_commit: 56549b9c8560668b1f069e35adc991fbff639446
payload_hash: 8a92039a394feac87edf6ff020fd6eb522689f364fe7f1a887a4bd12efd4a942
```

快照提供 D01–D12 的 `domain_id`、`domain_name`、`definition`、in-scope concepts 和
boundary notes，不能只向模型提供 D01、D02 等裸 ID。快照 hash 必须在每条 Annotation
Attempt 和 Run manifest 中记录。

### 8.3 Prompt 与 Schema Snapshot

Canonical Prompt renderer 位于 `src/migb/phase2/annotation/prompt.py`，固定输出以下
顺序的 sections：

```text
SYSTEM
TAXONOMY
EVIDENCE QUALITY RULES
ANNOTATION RULES
DOCUMENT METADATA
EVIDENCE
OUTPUT CONTRACT
```

```text
prompt_revision: taxonomy-annotation-prompt-v0.1
prompt_template_hash: 0a757150405b2de98dc3a06c43e9fc42ef0609c45e9ef176b7e10f64db5dab80
schema_revision: taxonomy-annotation-schema-v0.1
schema_path: schemas/phase2/taxonomy_annotation_v0.1.json
schema_hash: 54bd72e898faf3305bfd4a189d2d0435519f6a6df2dd1e5fe23da59701632c13
```

`prompt_template_hash` 是规范占位渲染的 hash；每个实际 Item 仍必须记录精确渲染结果的
`prompt_hash`。Schema 优先使用 strict structured output；无论 Provider 是否声称支持
structured output，都必须由本地 parser 再次校验。解析失败记录
`parse_status=failed`；不调用第二个 LLM 修复 JSON，最多按完整原任务执行一次 format
retry。

Prompt 禁止 web、tools、RAG、external retrieval、previous annotation、previous
document 和带答案示例。输入只包含允许的 Document Metadata、Final Evidence 和 Taxonomy
definition；不发送 `parent_group`、relative path directory、Gate 2B manual label、
Problem / Control identity 或其他 Annotator output。

### 8.4 Provider Adapter Boundary

Provider-specific code 位于：

```text
src/migb/phase2/annotation/__init__.py
src/migb/phase2/annotation/schema.py
src/migb/phase2/annotation/prompt.py
src/migb/phase2/annotation/adapters.py
src/migb/phase2/annotation/agreement.py
src/migb/phase2/annotation/retry.py
src/migb/phase2/annotation/artifacts.py
```

Adapter 只构造 provider-shaped request、解析提供的 mock response 和返回统一 canonical
schema。当前使用
`OpenAICompatibleAnnotationAdapter` 及其 `GrokRelayAnnotationAdapter`、
`GLMRelayAnnotationAdapter` 子类；Provider identity 不得退化为 `openai`。`infer()` 仍
保持 disabled，只有独立的 preflight requester 可以发起 `/models` 和 synthetic
`/chat/completions` 请求。

### 8.5 Provider Capability Preflight

Provider preflight 必须分别使用 A/B 的 Key 调用各自 endpoint 的 `/models`，并以精确
requested model ID 判断可访问性：`grok-4.6` 与 `glm-5.3` 不接受 alias 自动替换。每个
结果至少保留 `provider_id`、`base_url`、`transport_security`、`requested_model`、
`available_models_relevant`、HTTP status 和 error type；不保留完整 Authorization header。

只有在 `/models` 中发现精确 model ID 后，才对该 Annotator 发起一次固定 synthetic
request。Synthetic 输入为：

```text
Title: Synthetic Spur Gear Wear Study
Evidence: This synthetic document studies spur gear tooth contact, gear transmission design,
surface wear and service life.
```

Synthetic request 必须复用正式 Taxonomy snapshot、Prompt revision 和 Annotation Schema。
每个 Annotator 按 `json_schema`、`json_object`、`prompt_json_only` 顺序最多各尝试一次；
每次都由本地 canonical Schema validator 校验。若响应提供 `model`，必须与 requested
model 完全一致；若未提供则记录 `resolved_model=null`，不得自行填充。只有以下条件同时
满足时 Provider Preflight 才能 PASS：两把 Key 均存在且不同、两个精确 model ID 均可访问、
两次 synthetic inference 成功、最终 structured output mode 已确定、canonical Schema
validation 通过，且没有 silent model substitution。

## 9. Gate 2C-B 20-item Dry-run Protocol

### 9.1 样本与信息隔离

Gate 2C-B 必须复用原 Gate 2B 的 20-item Main Evidence Review Set，其中包括原 4 个
Problem Items。Dry-run 的目的不是重新评估 Gate 2B Evidence Sufficiency，而是验证：

- Annotation Schema 和 JSON 输出；
- A/B independence；
- `evidence_usability` detection；
- annotation-side OCR retry；
- A1/B1 discard 与 A2/B2 rerun semantics；
- agreement / conflict classification；
- Artifact writing 和 provenance。

Annotator 不得看到以下信息：

```text
problem/control label
Gate 2B sufficiency review
manual garbled label
Problem item ID
```

Annotator 必须仅从 Evidence 和允许的普通 Metadata 自行判断是否需要 retry，否则无法
验证 annotation-side retry contract。

### 9.2 Retry 验证目标

至少统计：

```text
triggered_by_A
triggered_by_B
triggered_by_either
```

针对原 4 个 Problem Items，最低接受目标为：

```text
either-annotator retry recall >= 3 / 4
```

推荐目标为 `4 / 4`。如果无法识别这些真实问题项，必须重新评审
annotation-side retry contract，不得直接进入 Gate 2C-C。

### 9.3 Dry-run 验收检查

Gate 2C-B 至少检查：

- 20 个 Item 均有 A/B 首轮结果或明确的执行错误记录；
- 触发 retry 的 Item 最多执行一次 RapidOCR；
- A2/B2 使用同一份 Final Evidence；
- A1/B1 在 retry 后不进入最终 Agreement / Conflict metrics；
- A/B 看不到彼此输出及 Problem / Control 标签；
- `annotation_attempts.jsonl`、`annotation_final.parquet`、`evidence_retries.parquet`、agreements、conflicts、manifest 和
  statistics 可相互追溯；
- text_absent 和 source_quality_exception 不因 dry-run 被扩大处理；
- Source PDF 与 Gate 2B canonical Artifact 未被修改。

### 9.4 Dry-run 指标与判定

Gate 2C-B 还必须记录：

```text
retry_triggered_by_a
retry_triggered_by_b
retry_triggered_by_either
false_retry_count
false_retry_rate
valid_structured_output_rate
format_retry_count
```

其中 `false_retry_count` / `false_retry_rate` 以原 16 个 non-problem Items 为观察分母，
当前不冻结硬阈值；若 `false_retry_rate > 25%`，必须重点 Review Prompt。Structured
Output 在允许一次 format retry 后必须达到 100%；初始目标为 valid structured output
至少 95%，否则 Gate 2C-B 不通过。发生 Evidence retry 的 Item，A2/B2 对同一
`final_evidence_revision` 的引用必须为 100%。

Annotator independence 至少通过请求和 Artifact 检查：

```text
A request contains no B response
B request contains no A response
peer_annotation_visible = false
```

Gate 2C-B 不执行 `provisionally_agreed` 的 10% Human Audit；该人工审计在完整 Gate
2C-C 后按既有 Taxonomy Contract 执行。

### 9.5 Gate 2C-B Verdict

允许的 dry-run Verdict 为：

```text
PASS
PASS WITH PROMPT REVISION
FAIL
```

`PASS` 至少要求 20 / 20 processed、A/B independence、structured output、OCR retry
pipeline、Problem-item either-annotator retry recall `>= 3 / 4` 和 Artifact validation
全部通过。若 Pipeline 可用但出现 excessive false retry、边界处理问题或系统性 confidence
误用，则为 `PASS WITH PROMPT REVISION`，修改 Prompt 后使用新的 Dry-run Run。出现 A/B
污染、不同 Final Evidence、provenance 断裂、Schema 解析不可靠或 Provider integration
系统性失败，则为 `FAIL`。

### 9.6 Cost、Run Identity 与运行安全

每次 Run 的 `statistics.json` 至少统计：

```text
request_count
successful_request_count
retry_request_count
input_tokens
output_tokens
provider_reported_cost_if_available
estimated_cost
```

成本是 operational metric，不影响 taxonomy label。Run ID 采用：

```text
g2c-dryrun-YYYYMMDDTHHMMSSZ-<gitsha7>
g2c-full-YYYYMMDDTHHMMSSZ-<gitsha7>
```

正式运行沿用项目规则，要求 `dirty=false`。Gate 2C-A 只创建设计、配置和 code，不创建
Runtime Annotation Artifact。

## 10. Gate 2C-C 与 Gate 2C-D 的进入条件

只有 Gate 2C-A 配置冻结且 Gate 2C-B dry-run 达到验收标准后，才可另行授权：

```text
Gate 2C-C
Full 600-item Taxonomy Calibration
```

Gate 2C-C 仍不等于 Source Selection。完成双 Annotator、Agreement / Conflict、Human / Project
Owner Review 和 Parent Group × Domain 分析后，才进入 Gate 2C-D，决定 Taxonomy revision
和 Source Selection Policy freeze。

本文件不授权：

- Full 767-item Evidence v0.3 Precomputation；
- 对全部 767 条预先运行 OCR；
- 立即对 600 条执行双 Annotator Annotation；
- Source Selection；
- Benchmark Source Registry；
- MinerU、Full PDF Parsing、Question Generation 或 Ground Truth construction。

## 11. 当前停止边界与下一步

当前状态为：

```text
Gate 2B: PASSED
Evidence Contract: evidence-v0.3-adaptive-v0.1
Gate 2C-A: PASSED
Gate 2C-B Provider Preflight: BLOCKED BY PROVIDER PREFLIGHT
Gate 2C-B 20-item Dry-run: NOT AUTHORIZED
Full 767-item Evidence v0.3 Precomputation: CANCELLED / NOT REQUIRED
Benchmark Item LLM calls: NOT EXECUTED
```

下一步必须先处理 Grok Relay synthetic `json_schema` HTTP 400，并重新执行 capability
preflight；不得更换 `grok-4.6` 或 `glm-5.3`。只有 technical preflight 通过，且 Project
Owner 接受明文 HTTP 风险或切换到 HTTPS endpoint 后，才可另行授权 Gate 2C-B：

```text
Gate 2C annotator configuration,
prompt contract,
annotation artifacts,
and 20-item dry-run protocol
```

在上述条件满足且 Gate 2C-B 获得授权前，不发送任何真实 Benchmark Item。
