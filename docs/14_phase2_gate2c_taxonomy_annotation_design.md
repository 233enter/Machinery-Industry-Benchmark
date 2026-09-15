# Phase 2 Gate 2C Taxonomy Annotation Execution Design

Project: Mechanical Industry General Benchmark
Document: Phase 2 Gate 2C Taxonomy Annotation Execution Design
Version: 0.1
Status: Draft - Awaiting Annotator Configuration Review
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2C Taxonomy Annotation Execution Design
Evidence Contract: `evidence-v0.3-adaptive-v0.1`

## 1. 文档目的与边界

Gate 2B 已通过。Project Owner 接受 annotation-side Retry，并拒绝 automatic
pre-annotation OCR trigger。本文件只建立 Gate 2C 的执行设计骨架，用于在实际模型调用前
冻结 Annotator 配置、Annotation Artifact、Evidence retry semantics 和 20-item dry-run
协议。

本文件不选择实际 Annotator model，不调用 LLM，不执行 600-item Annotation，不执行
Source Selection，也不生成 Benchmark、Ground Truth 或新的 767-item OCR Runtime。
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
| Gate 2C-A | Annotation Execution Design Freeze | 冻结 Annotator 配置、prompt、Schema、retry、Artifact 和处理逻辑 | 待评审 |
| Gate 2C-B | 20-item Annotation Dry-run | 验证 A/B 独立标注、Evidence retry、重跑和 Artifact 写入 | 待 Gate 2C-A |
| Gate 2C-C | Full 600-item Taxonomy Calibration | 在 dry-run 通过后执行完整 Main Sample 双 Annotator Calibration | 未授权 |
| Gate 2C-D | Calibration Review + Taxonomy Decision + Source Selection Policy Freeze | 汇总 agreement/conflict、人工复核和 Source Selection Policy 决策 | 未授权 |

在 Gate 2C-A 和 Gate 2C-B 完成并通过前，不执行完整 600-item 双 Annotator Annotation。

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

## 6. Retry 与 A/B 一致性 Contract

### 6.1 First-pass 处理

Annotation A1 和 Annotation B1 都使用同一份 PyMuPDF Primary Evidence。A1 不看 B1，B1
不看 A1。每个 Annotator 仍独立记录 `annotator_id`、`annotation_pass`、model/provider/
version（待 Gate 2C-A 冻结）、prompt revision、schema revision、Taxonomy revision 和
inference parameters。

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

每次 Gate 2C Run 使用独立的 `<gate2c_run_id>`，Artifact Layout 设计为：

```text
/data/suzhe/migb/
  phase2/
    runs/
      <gate2c_run_id>/
        annotation_pass_a.jsonl
        annotation_pass_b.jsonl
        evidence_retries.jsonl
        annotation_final_a.jsonl
        annotation_final_b.jsonl
        taxonomy_agreements.parquet
        taxonomy_conflicts.parquet
        manifest.json
        statistics.json
```

| Artifact | 用途 |
| --- | --- |
| `annotation_pass_a.jsonl` | Annotator A 的首轮结果和配置 provenance |
| `annotation_pass_b.jsonl` | Annotator B 的首轮结果和配置 provenance |
| `evidence_retries.jsonl` | retry 请求、原因、fallback 参数、前后 Evidence revision 和结果 |
| `annotation_final_a.jsonl` | 使用最终 Evidence 的 A2 结果；无 retry 时可引用 A1 |
| `annotation_final_b.jsonl` | 使用最终 Evidence 的 B2 结果；无 retry 时可引用 B1 |
| `taxonomy_agreements.parquet` | 通过既定 Agreement Logic 的合并结果 |
| `taxonomy_conflicts.parquet` | 冲突、低置信度、taxonomy gap 或需人工 Review 的结果 |
| `manifest.json` | Run identity、输入 Artifact、版本、Schema、配置引用和 checksum |
| `statistics.json` | item accounting、retry、agreement、conflict、deferred 和错误统计 |

如果某 Item 没有 retry，`annotation_final_a` / `annotation_final_b` 可以通过
`first_pass_artifact_ref` 或等价 reference 表示 first pass 即 final，不要求复制大型
Evidence 文本。若发生 retry，Artifact 必须同时保留 A1/B1 audit provenance 与 A2/B2
最终结果。

具体字段、序列化方式、checksum convention 和 failure semantics 在 Gate 2C-A 冻结；
本文件当前不创建上述远程目录或 Runtime Artifact。

## 8. Annotator Configuration Freeze Boundary

以下配置必须在 Gate 2C-A 冻结，但当前不擅自给出具体模型或参数：

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

Actual Model A / Model B、provider、版本和 inference parameters 保持 `TBD`，不得在本
设计文档中替代为具体选择。Gate 2C-A 评审完成前不调用任何模型。

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
- `evidence_retries.jsonl`、final annotations、agreements、conflicts、manifest 和
  statistics 可相互追溯；
- text_absent 和 source_quality_exception 不因 dry-run 被扩大处理；
- Source PDF 与 Gate 2B canonical Artifact 未被修改。

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
Gate 2C: AUTHORIZED FOR DESIGN AND 20-ITEM DRY-RUN ONLY
Full 767-item Evidence v0.3 Precomputation: CANCELLED / NOT REQUIRED
LLM calls: NOT EXECUTED
```

下一步必须先评审并冻结：

```text
Gate 2C annotator configuration,
prompt contract,
annotation artifacts,
and 20-item dry-run protocol
```

在上述内容冻结前，不调用任何 LLM。
