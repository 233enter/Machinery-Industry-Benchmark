# Phase 2 Taxonomy Calibration & Source Selection

Project: Mechanical Industry General Benchmark
Document: Phase 2 Taxonomy Calibration & Source Selection Design
Version: 0.1
Status: Reviewed - Baseline
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2C Taxonomy Annotation Execution Design
Evidence Contract: `evidence-v0.3-adaptive-v0.1`

## 1. 文档定位与设计边界

本文档是 Phase 2 的主要设计 Contract，定义基于已完成 Corpus Inventory 进行 Taxonomy
Calibration 和 Source Selection 的工作流、抽样原则、轻量证据 Contract、标注 Contract、
Source Selection Framework、后续 Policy 冻结边界、Artifact Layout 和阶段 Gate。

本文档只进行设计，不创建 Calibration Sample，不读取批量真实 PDF，不创建 Phase 2 Runtime
Artifact，不调用 LLM，不运行 MinerU / OCR，不执行 Full PDF Parsing，也不生成 Benchmark
Question 或 Ground Truth。

Phase 2 不负责：

- Question Generation；
- Ground Truth construction or validation；
- Full Document Parsing；
- Benchmark Evaluation。

Phase 2 只解决两个问题：

1. **Taxonomy Calibration**：验证真实 Candidate Source Corpus 是否能被现有 D01–D12
   合理覆盖，识别 Domain 边界、跨 Domain 文档和 taxonomy gap，并为后续 Taxonomy 版本
   决策提供证据。
2. **Source Selection**：从 Candidate Source Corpus 中建立后续 Phase 3–7 可使用的
   Benchmark Source Corpus Registry。

必须保持以下边界：

```text
Candidate Source Corpus
        !=
Benchmark Source Corpus
        !=
Benchmark Items
```

## 2. 已有输入与范围基线

Phase 2 使用 Phase 1 已通过的 Full Corpus Inventory 作为输入基线，不修改其 Canonical
Artifact。

| Field | Value |
| --- | --- |
| Candidate Source Corpus | `cmes_journal` |
| Source Root | `/mnt/data_nfs/dataset/original/cmes/journal` |
| Physical File Instance count | `60454` |
| Top-level Source Groups | `20` |
| Full Inventory Run | `full-20260914T075902Z-faa4565` |
| Inventory Schema | `inventory-v0.2` |
| Full Artifact Root | `/data/suzhe/migb/inventory/runs/full-20260914T075902Z-faa4565` |
| Existing Taxonomy baseline | `Benchmark Taxonomy v0.1`，Domain `D01–D12` |

Phase 2 的输入主要包括：

- `files.parquet`；
- `duplicate_groups.parquet`；
- `manifest.json`；
- `statistics.json`；
- Full Inventory Report；
- Phase 0 的 `Benchmark Taxonomy v0.1`。

Full Inventory 是 immutable physical source inventory。Phase 2 产生的 selection 和
annotation 是 derived Artifact，不能通过修改 `files.parquet` 来表示入选或排除。

Phase 2 的设计决策按 Gate 分层冻结。Gate 2A 只冻结可执行的 Calibration Design 和
Source Selection Framework；最终 Source Selection Policy、Candidate Pool 规模和
Benchmark Source Corpus Registry 的内容，必须在后续 Calibration 证据基础上决定。

## 3. Phase 2 总体流程

Phase 2 的候选流程为：

```text
Full Corpus Inventory
        ↓
Non-semantic Eligibility / Hard Filtering
        ↓
Taxonomy Calibration Sampling
        ↓
Lightweight Evidence Extraction
        ↓
Taxonomy Annotation
        ↓
Taxonomy Calibration Analysis
        ↓
Taxonomy Revision Decision
        ↓
Source Selection Policy Freeze
        ↓
Source Selection Candidate Pool
        ↓
Semantic Review / Document-family Review
        ↓
Benchmark Source Corpus Registry
        ↓
Phase 2 Gate
```

不得把 `60454 PDFs → LLM classify everything` 作为 Phase 2 的初始路径。原因包括：

- Taxonomy 尚未经过真实 Corpus Calibration；
- 大规模分类会放大错误的 taxonomy boundary；
- 在 Evidence Contract 未验证前不应扩大成本；
- Calibration 可能导致 Domain Definition 调整。

执行顺序必须保持为：

```text
sample → calibrate → freeze taxonomy → scale source selection
```

## 4. Eligibility 与 Signal Stratification

### 4.1 Calibration Main Sample 的冻结 Eligibility

Taxonomy Calibration Main Sample 只从以下条件同时满足的 File Instance 中抽取：

```text
inventory_status = success
pdf_open_status = success
page_count > 0
text_layer_status in {text_present, mixed_or_uncertain}
```

`text_absent` 不进入 Main Sample，但不是 Benchmark Source Corpus 的 Hard Exclusion；
它进入独立的 `Text-absent Audit Pool`。因此本节的 text-layer 条件是 Main Sample 的
Calibration Eligibility，不是最终 Source Selection 的价值判断。

Full Inventory 中的 7 个 partial records 不混入 Main Sample：

- 6 个 zero-page PDF；
- 1 个 `FileDataError` / open failure 记录。

它们全部进入独立的 `Source Quality Exception Pool`，保留原始 provenance 和错误状态，
但不用于 Main Taxonomy Calibration。

### 4.2 Signal Stratification 维度

抽样必须同时满足 Source Group Coverage、Population Representation 和 Signal Diversity。
初始需要记录并用于分层或审计的信号包括：

| Signal | Phase 2 用途 | 是否直接作为 Hard Exclusion |
| --- | --- | --- |
| `parent_group` | 基础覆盖和 Parent Group × Domain 分析 | 否 |
| `text_layer_status` | 证据可提取性和 Text-absent / Mixed 审计 | 否 |
| `filename_parse_status` | Metadata pattern 观察 | 否 |
| `page_count` | 文档长度和证据覆盖观察 | 否 |
| `size_bytes` | 文档规模和运行风险观察 | 否 |
| exact SHA-256 duplicate relation | 控制重复 physical File Instance 进入 Sample | 非代表副本不进入 Main Sample |
| PDF health / inventory status | 排除明显不可用 Main Sample 输入并保留异常池 | 仅按本 Contract 处理 |

其中 `parent_group` 是 Source Group 维度，不等于 D01–D12 Domain。Signal stratification
用于构建可审计的 Calibration Sample，不意味着这些信号已经成为最终 Benchmark 的能力
权重。

### 4.3 Determinism

抽样必须能够由以下输入重新生成或审计：

- 固定的 Full Inventory Run；
- 固定的 config snapshot；
- 固定的 eligibility rules；
- 固定的 duplicate representative rule；
- 固定的 canonical ordering；
- 固定的 sample target 和 quota rule。

不得依赖不可复现的 runtime random state。每次抽样需要记录 input snapshot、selection
rule、quota accounting、sample item order、`phase2_run_id` 和 `calibration_sample_id`。

### 4.4 Eligible Population 与 Exact Duplicate Collapse

Quota allocation 前必须先构建 duplicate-collapsed eligible population，并明确区分：

```text
physical eligible population
        !=
duplicate-collapsed eligible population
```

`physical eligible population` 是满足本节 Eligibility 的全部 physical File Instance；
`duplicate-collapsed eligible population` 是对同一 exact SHA-256 group 只保留一个
deterministic representative 后用于 Main Sample quota 的 population。

对同一 exact SHA-256 group：

1. 只保留 deterministic representative 进入 duplicate-collapsed eligible population；
2. 非 representative 不进入 Main Sample population，也不参与 Main Sample quota；
3. 非 representative 的 provenance 和 duplicate relation 必须保留；
4. 不删除、rename 或 move 任何 Source PDF；
5. exact duplicate 不等于 document-family，也不等于 semantic duplicate。

因此 `eligible_population`、quota accounting 和 actual selected count 必须明确说明
采用的是 duplicate-collapsed eligible population，同时保留 physical eligible population
的统计值。

## 5. Taxonomy Calibration Sample v0.1

### 5.1 目标

设计目标为：

```text
Taxonomy Calibration Main Sample target = 600 PDFs
```

这是 Taxonomy Calibration Sample，不是最终 Benchmark Sample，也不是 Benchmark Source
Corpus 数量目标。

如果 duplicate-collapsed eligible population 不足以满足目标，实际数量必须如实记录，不得
通过混入不符合 eligibility 的 PDF 强行补齐。

### 5.2 Stage A — Group Base Coverage

当前有 20 个 Parent Groups。对每个 Parent Group 定义：

```text
base_quota = min(15, duplicate_collapsed_eligible_population)
```

在 duplicate-collapsed eligible population 允许时，Stage A 提供：

```text
20 × 15 = 300
```

个基础覆盖名额，确保每个 Source Group 都有机会进入 Calibration。

### 5.3 Stage B — Proportional Allocation

Stage A 后的剩余目标为：

```text
600 - sum(base_quota)
```

对每个 Parent Group 的剩余 duplicate-collapsed eligible population 做 proportional
allocation，使用 Hamilton / Largest Remainder 思路：

1. 先按比例计算整数 base allocation；
2. 按 remainder 排序分配剩余名额；
3. tie-break 固定为 `sorted(parent_group)`，不使用运行时顺序；
4. 不超过各 Group 的剩余 duplicate-collapsed eligible capacity；
5. 记录每个 Group 的 population、base quota、proportional allocation、remainder、
   final quota 和 actual selected count。

最终目标为 600，前提是 duplicate-collapsed eligible population 足够。base quota、
Hamilton / Largest Remainder、`sorted(parent_group)` tie-break 和 quota accounting 在
Gate 2A 冻结。

### 5.4 Sample Item Selection

在每个 Parent Group 内，先按以下固定顺序排序：

```text
relative_path (POSIX lexical order), then file_instance_id
```

然后采用 deterministic evenly-spaced selection，使选中的 File Instance 分布于该 Group
的有序 population。不得采用 first N，也不得采用 runtime random sampling。Signal
strata 用于记录覆盖和审计；若后续需要 strata quota，必须在 Gate 2A 明确配置，不能
隐式改变本节 quota。

每一个 selected item 必须保留：

- `file_instance_id`；
- `parent_group`；
- `relative_path`；
- source snapshot / inventory run 引用；
- selection stage、method 和 quota accounting；
- exact duplicate representative 信息；
- 参与的 signal strata；
- `phase2_run_id`、`calibration_sample_id` 和 `calibration_item_id`。

### 5.5 不采用的抽样方法

当前不采用：

- 无分层的 random 600；
- first N（包括每个 Group 固定取前 30 个）；
- 按文件名或目录名直接推断 Domain 后再抽样；
- 把 D1、D2、D3 历史样本或 7 个 partial records 当作必然的 Main Sample 输入。

## 6. Audit Pools

Audit Pools 与 600 个 Main Sample 分开设计，用于观察异常输入、证据路径和 Metadata
pattern。四个 Pool 必须在 physical File Instance 层面彼此互斥，也必须与 Main Sample
互斥：

```text
Main Sample ∩ Audit Pools = ∅
Audit Pool_i ∩ Audit Pool_j = ∅  (i != j)
```

固定的 Pool priority 为：

1. Source Quality Exception
2. Text-absent
3. Mixed Text
4. Filename-unmatched

构建每个后续 Pool 时，必须排除 Main Sample 和 priority 更高的已构建 Pool。所有 Pool
都必须保留独立的 `pool_name`、selection rule、target、actual count、provenance 和
`calibration_item_id`。

除 Exception Pool 外，其余 Pool 使用 Parent Group base coverage、proportional allocation
和 deterministic evenly-spaced selection。稀疏 Group 优先至少选择 1 条；如果可用数量
不足目标，则取全部可用项，不从其他 Pool 补齐。

理论最大 unique evidence target 为：

```text
600 + 7 + 60 + 40 + 60 = 767
```

这是 unique physical File Instance 的上限表达，不是必须达成的数量承诺。

### 6.1 Source Quality Exception Pool

```text
target = 7
```

包括 6 个 zero-page PDF 和 1 个 `FileDataError` / open failure。该 Pool 用于确认异常
状态如何影响后续 Source Selection，不用于 Main Domain Calibration。

### 6.2 Text-absent Audit Pool

```text
target = 60
```

在 Parent Group 间进行 deterministic stratified sampling，用于判断 text-absent 文档是否
可能成为 Multimodal / OCR 路径的 Source Candidate。

本阶段不执行 OCR，不因为 `text_absent` 自动排除文档。

### 6.3 Mixed Text Audit

Full Inventory 中当前 `mixed_or_uncertain=163`。如果 duplicate-collapsed eligible
population 允许，设计目标为：

```text
target = 40
```

用于观察 Mixed text-layer 的证据可用性与跨 Group 分布。

### 6.4 Filename-unmatched Audit

```text
target = 60
```

用于观察 filename metadata pattern，不用于修改 Filename Parser，不用于排除 Document。

### 6.5 Pool Boundary

Audit Pool 的目的分别是质量、文本层、混合状态和 filename pattern 观察。它们不能被解释
为最终 Benchmark Source Corpus 的入选名单，也不能替代后续 Source Selection Review。

Audit Pool 的实际 target 和 actual count 必须在 `statistics.json` 中分别记录；不足时
不能从其他 Pool 借用名额。

## 7. Exact Duplicate Handling

Full Inventory 已发现：

```text
exact duplicate groups = 207
exact duplicate files = 495
largest group size = 15
```

Taxonomy Calibration Sampling 对同一 exact SHA-256 group 最多抽取 1 个 physical File
Instance：

1. 优先使用 `duplicate_groups.parquet` 中的 deterministic representative；
2. 代表副本进入 eligible pool 后才参与抽样；
3. 同组其他 physical File Instance 不进入 Main Calibration Sample；
4. 其他副本继续保留 provenance，可在后续 Source Selection 中标记
   `excluded_exact_duplicate`；
5. 不删除任何 Source PDF；
6. exact duplicate 不等于 document-family，也不等于 semantic duplicate。

Quota allocation 之前完成 duplicate collapse。这里的 collapse 只改变用于抽样的
population 表示，不改变 physical inventory；`physical eligible population` 与
`duplicate-collapsed eligible population` 的数量必须同时出现在 sampling accounting 中。

### 7.1 Stable Identity

Phase 2 必须区分以下 identity：

```text
phase2_run_id
calibration_sample_id
calibration_item_id
```

建议 `calibration_item_id` 使用稳定 UUIDv5，不使用 runtime random UUID：

```python
uuid.uuid5(
    uuid.NAMESPACE_URL,
    f"migb://phase2/calibration-item/{calibration_sample_id}/{file_instance_id}"
)
```

Audit Pool item 使用相同的稳定 identity 原则，并额外记录 `pool_name`。同一 item 在
重跑时必须能够由固定 sample/config/input snapshot 重新得到相同 identity。

## 8. Text-layer Signal Handling

Main Taxonomy Calibration Sample 主要使用：

```text
text_present
mixed_or_uncertain
```

这是为了验证 Lightweight Text Evidence 路径，但不是对 `text_absent` 文档的最终价值
判断。

`text_absent`：

- 不能直接作为 Benchmark Source Corpus 的 Hard Exclusion；
- 进入独立 Text-absent Audit Pool；
- 可能成为 Multimodal Benchmark Source Candidate；
- 本阶段不执行 OCR。

`mixed_or_uncertain`：

- 可进入 Main Sample；Main Sample 未选中的剩余项按 Pool priority 进入 Mixed Text Audit；
- 作为 evidence quality / routing signal；
- 不自动排除。

## 9. Lightweight Evidence Extraction v0.1

### 9.1 工具和范围

Calibration Evidence 只针对 Calibration Sample 和 Audit Pools 使用 PyMuPDF lightweight
extraction，不使用 MinerU，不进行 Full Corpus Parsing，不在 Source Corpus 写回。

### 9.2 页面范围

每个 Calibration PDF 的 Evidence v0.1 固定提取 physical first 3 pages，即：

```text
page 0, page 1, page 2
```

当 `page_count < 3` 时，提取所有现有页面。页面顺序必须被保留在 Evidence Record 中。
Gate 2B 不实现 middle-page / last-page fallback，也不实现 semantic page selection。

每条 Evidence 同时记录：

- filename；
- filename parsed title；
- PDF metadata title；
- page count；
- page-level text。

这一步是用于 Domain Calibration 的轻量 Evidence，不是完整解析，不代表全文语义已经
覆盖。

### 9.3 Evidence Character Cap

每个 Document 的 Evidence 设置：

```text
max_extracted_chars = 12000
```

该 cap 标记为 `Provisional v0.1 for Gate 2B`，允许在 Gate 2B 后、Gate 2C 前根据
Evidence Quality Metrics 调整。

按页面顺序截断，并记录：

- `evidence_page_indices`；
- `evidence_char_count`；
- `evidence_truncated`。

发生截断时，`evidence_truncated=true`；这不是 Parser Failure。

### 9.4 Calibration Evidence Schema

| Field | 说明 |
| --- | --- |
| `phase2_run_id` | Phase 2 Run 标识 |
| `inventory_run_id` | Full Inventory Run 标识 |
| `calibration_sample_id` | 本次 Calibration Sample 的稳定标识 |
| `calibration_item_id` | 本条 Main Sample 或 Audit Pool item 的稳定标识 |
| `pool_name` | `main` 或具体 Audit Pool 名称 |
| `file_instance_id` | Physical File Instance 标识 |
| `source_root_id` | Source Root 标识 |
| `relative_path` | 相对于 Source Root 的路径 |
| `parent_group` | 原始 Source Group，不等于 Domain |
| `sha256` | Full Inventory 中的 binary identity |
| `page_count` | Inventory page count |
| `text_layer_status` | Inventory text-layer signal |
| `filename_title` | 已有 Filename Parser 结果 |
| `metadata_title` | PDF metadata title |
| `evidence_text` | 受 cap 限制的页面级轻量文本 |
| `evidence_page_indices` | 实际提取的页面索引 |
| `evidence_char_count` | 实际字符数 |
| `evidence_truncated` | 是否发生 cap 截断 |
| `evidence_status` | `success` / `partial` / `failed` / `not_applicable` |

Evidence Record 必须能回溯到原始 File Instance 和 Full Inventory Run。具体文件格式和
序列化方式在 Gate 2A 冻结。

### 9.5 Evidence Quality Metrics

Gate 2B 至少统计以下 Evidence Quality Metrics：

- `evidence_success_count`；
- `evidence_partial_count`；
- `evidence_failed_count`；
- `evidence_char_count`：`min` / `median` / `p10` / `p90` / `max`；
- `evidence_truncated_count`；
- `zero_text_evidence_count`；
- `metadata_title_present_rate`；
- `filename_title_present_rate`。

以上指标必须至少按 Main Sample、Audit Pool 和 Parent Group 分析。若 Evidence 过短、
只包含 front matter、出现乱码或无法支持稳定判断，应先修订 Evidence Contract，再决定
是否进入 Annotation；不得直接启动 Taxonomy Annotation。

## 10. Taxonomy Annotation Contract

### 10.1 Annotation Unit

Taxonomy Calibration 的 annotation unit 是：

```text
one document
```

不是 page，也不是 Benchmark Question。Annotation 使用 Calibration Evidence 和已有
Inventory Metadata，不等同于 Ground Truth。

### 10.2 Annotation Schema

每个文档至少设计以下字段：

| Field | 允许值 / 说明 |
| --- | --- |
| `primary_domain` | `D01`–`D12`、`OUT_OF_SCOPE`、`UNCERTAIN` |
| `secondary_domains` | 0–3 个 Domain；确有跨领域依赖时使用 |
| `taxonomy_fit` | `clear_fit` / `cross_domain` / `ambiguous` / `taxonomy_gap` / `out_of_scope` / `insufficient_evidence` |
| `confidence` | `high` / `medium` / `low` |
| `evidence_usability` | `usable` / `partially_usable` / `unreadable` / `insufficient`；独立于 `taxonomy_fit` |
| `requires_evidence_retry` | Item-level derived flag；任一独立 Annotator 触发 Evidence retry 时为 `true` |
| `evidence_keywords` | 支持判断的关键词或短语 |
| `evidence_rationale` | 基于 Evidence 的判断理由 |
| `review_status` | `annotated_a` / `annotated_b` / `provisionally_agreed` / `conflict` / `human_reviewed` / `deferred` |

`primary_domain` 只能有一个；`secondary_domains` 允许 0–3 个。不能强制所有 Document
都落入 D01–D12。

### 10.3 taxonomy_fit 语义

- `clear_fit`：现有 Domain 有清晰合理的归属；
- `cross_domain`：文档确实依赖多个 Domain，单一 Primary 仍可解释；
- `ambiguous`：Evidence 不足以稳定区分已有边界；
- `taxonomy_gap`：文档明显属于 MIGB 机械工业范围，但 D01–D12 没有合理位置；
- `out_of_scope`：不属于当前 MIGB 范围；
- `insufficient_evidence`：轻量 Evidence 不足，不能可靠判断。

`taxonomy_gap` 不能被当作标注失败而隐藏，也不能为了保持 D01–D12 不变而强行归类。

`evidence_usability` 不等于 `taxonomy_fit`。如果任一独立 Annotator 的
`evidence_usability` 为 `unreadable` 或 `insufficient`，该 Item 的
`requires_evidence_retry` 必须为 `true`；如果 `taxonomy_fit = insufficient_evidence`，
也必须触发相同的 Evidence retry。`partially_usable` 不单独触发 OCR；若仍能确定
`primary_domain` 且 `confidence != low`，可以继续进入 Agreement Logic。`confidence = low`
只进入 Review Queue，不单独触发 OCR。

## 11. Annotation Method

### 11.1 LLM 的角色

后续实际 Calibration 可以使用 LLM 作为辅助 Annotator，但必须明确：

```text
LLM != Ground Truth Authority
```

Taxonomy Annotation 结果不是最终 Benchmark Ground Truth。单个 LLM 的输出不能单独决定
Taxonomy Definition 或 Source Selection Policy。

### 11.2 Independent Annotation

每个 Annotator 的输出作为一行 Annotation Artifact，至少包含：

- `annotator_id`；
- `annotation_pass`；
- 本文档定义的 Annotation 字段；
- `model/provider/version`；
- prompt revision；
- temperature；
- 其他 inference parameters。

执行两次相互独立的标注：

```text
Pass A: Model A / independent annotation
Pass B: Model B or independent prompt / independent annotation
```

Pass A 不看 Pass B，Pass B 不看 Pass A。首轮两个 Pass 使用相同的 Primary Evidence、
Evidence Contract、Taxonomy Definition 和标注 Schema，但保持输出独立。如果任一 Pass
触发 Evidence retry，A1/B1 只保留 audit provenance，不进入最终 agreement、conflict 或
taxonomy metrics；RapidOCR 生成同一份 final Evidence 后，必须使用相同的 final Evidence、
Taxonomy revision、prompt revision 和 schema revision 重跑 A/B。实际 Annotator model ID
延后至 Gate 2C execution config 冻结，本设计不擅自指定具体模型。

### 11.3 Agreement 与 Conflict

当以下条件同时成立时，可以将合并结果标记为：

```text
provisionally_agreed
```

- `A.primary_domain == B.primary_domain`；
- `A.taxonomy_fit == B.taxonomy_fit`；
- `A.confidence != low` 且 `B.confidence != low`；
- `taxonomy_fit` 不属于 `ambiguous`、`taxonomy_gap`、`out_of_scope`、
  `insufficient_evidence`；
- 如果 `taxonomy_fit = cross_domain`，则
  `set(A.secondary_domains) == set(B.secondary_domains)`。

以下任一情况都必须标记为 `conflict` 并进入 Review Queue：

- primary domain disagreement；
- taxonomy_fit disagreement；
- cross-domain 的 secondary domain disagreement；
- 任一 `taxonomy_fit` 为 `taxonomy_gap`、`out_of_scope`、`ambiguous` 或
  `insufficient_evidence`；
- 任一 `confidence = low`。

冲突答案不得由系统自动覆盖或静默选择其中一个结果。

### 11.4 Human Review

在当前没有完整机械领域专家团队的条件下，v0.1 采用风险优先的人工复核设计：

- Review 所有 conflict；
- Review 所有 `taxonomy_gap`；
- Review 所有 `out_of_scope`；
- Review 所有 `low confidence`；
- Review 所有 `insufficient_evidence`；
- 对 `provisionally_agreed` Sample 做 10% deterministic audit。具体选择为：

  ```text
  sort by SHA-256(calibration_item_id + taxonomy_revision)
  take first ceil(10%)
  ```

所有 conflict、`taxonomy_gap`、`out_of_scope`、low confidence 和
`insufficient_evidence` 都必须 Review。

专家资源、最终复核人和复核覆盖率仍须在 Gate 2C execution config / human review plan
中确认；本设计不把人工复核能力假设为无限。影响 Taxonomy structure 的 gap、merge /
split / addition 或 persistent boundary conflict，必须由 Project Owner / domain review
明确决定，不能由两个 LLM 单独决定。

## 12. Taxonomy Calibration Metrics

Calibration Report 至少按总体和 Parent Group 汇总：

- primary domain distribution；
- secondary domain distribution；
- `clear_fit` rate；
- `cross_domain` rate；
- `ambiguous` rate；
- `taxonomy_gap` rate；
- `out_of_scope` rate；
- `insufficient_evidence` rate；
- annotation agreement rate；
- conflict rate。

每个 D01–D12 至少检查：

- sample count；
- representative source groups；
- typical titles；
- boundary-conflict examples。

不能只根据 Domain count 判断覆盖质量。Calibration 还应分析：

```text
Parent Group × Domain Distribution
```

并区分：

- annotation error；
- evidence insufficiency；
- natural cross-domain nature；
- taxonomy definition ambiguity；
- real taxonomy gap。

## 13. Taxonomy Change Gate

Taxonomy v0.1 不因几个异常样本自动修改。只有完成 Calibration Review，并对冲突、Gap、
Evidence 不足和跨 Domain 现象进行归因后，才允许形成 Taxonomy 版本决策。

可能的决策结果包括：

- No structural change；
- Definition refinement only；
- Boundary refinement；
- Domain merge / split / addition。

本设计不预先决定任何一种结果。只有在 Gate 2C 完成后，才决定采用：

```text
Benchmark Taxonomy v0.2
```

或保留 v0.1 并记录 refined definitions。

## 14. Source Selection Framework

### 14.1 Source Selection 目标

Source Selection 的目标是决定哪些 Document 适合作为后续 Benchmark Item Construction 的
Source，而不是简单给 60454 个 PDF 打 Domain Label。

Gate 2A 冻结的是 `Source Selection Framework`，不是最终的 `Source Selection Policy`。
Source Selection 必须在 Taxonomy Calibration Review 和 Taxonomy 版本决策之后执行，并记录：

- selection input Inventory Run；
- Taxonomy revision；
- selection policy revision；
- selection status；
- selection reason；
- provenance 和 duplicate relation。

当前工作流固定为：

```text
Full Inventory
→ non-semantic eligibility / hard filtering
→ Taxonomy Calibration
→ freeze Taxonomy
→ freeze Source Selection Policy
→ construct Source Selection Candidate Pool
→ semantic annotation / review of candidate pool
→ document-family / near-duplicate review
→ Benchmark Source Corpus Registry
```

`Source Selection Candidate Pool` 是 Taxonomy Calibration 后、最终 Registry 前的中间集合。
其规模为 `TBD until Gate 2C`，不要求默认对全部 60454 PDFs 做 semantic LLM classification；
只有 Gate 2C 证明必要时，才单独授权扩大 semantic review 范围。

Gate 2A 不冻结以下内容：

- final Source Selection quota；
- final Benchmark Source Corpus size；
- domain quota；
- temporal balancing；
- parent-group hard quota；
- visual-source pool；
- actual annotator model IDs；
- document-family algorithm。

### 14.2 Selection Status

Source Selection status 冻结为以下状态：

```text
eligible
candidate
review_required
selected
excluded
```

语义定义如下：

- `eligible`：通过非语义 hard filter；
- `candidate`：进入 semantic Review Pool；
- `review_required`：需要进一步 review；
- `selected`：最终进入 Benchmark Source Corpus；
- `excluded`：有明确 exclusion reason。

`not selected` 不作为状态；没有进入最终 Registry 不自动等于 low quality excluded。完整
决策集必须保留 selection reason，不得静默删除。

### 14.3 Source Eligibility Dimensions

Source Selection 至少考虑：

- domain relevance；
- content quality；
- evidence extractability；
- question construction potential；
- source diversity；
- temporal diversity；
- exact duplicate status；
- text / visual modality potential。

Phase 2 不使用最终 Benchmark Item Score，也不把题目数量最大化作为唯一目标。

Selection reason 至少预留以下 vocabulary：

```text
invalid_pdf
pdf_open_failure
excluded_exact_duplicate
domain_out_of_scope
insufficient_content
family_duplicate
selection_quota_not_selected
manual_review_exclusion
```

完整 vocabulary 在 Gate 2C 冻结 Source Selection Policy 时确定。

### 14.4 Source Group 与 Domain

必须保持：

```text
parent_group != D01–D12
```

Source Selection 应使用 `Parent Group × Domain Distribution` 理解 Source Composition，
不能根据目录名直接分类，也不能让 PDF 数量最多的 Group 自动成为 Benchmark 权重最高的
Domain。

## 15. Hard Exclusion 与 Non-exclusion Rules

### 15.1 Hard Exclusion Rules

以下为 Source Selection 的 Hard Exclusion：

| Condition | Selection handling |
| --- | --- |
| `pdf_status = corrupted_or_invalid` | `excluded`，reason=`invalid_pdf` |
| `pdf_open_status = failed` | `excluded`，reason=`pdf_open_failure` |
| exact duplicate non-representative | `excluded`，reason 记录为 `excluded_exact_duplicate` |

对于 exact duplicate group，Benchmark Source Corpus 最多保留一个 deterministic representative
physical File Instance。上述 exclusion 只作用于 Source Selection，不修改 Candidate Source
Inventory，也不删除文件。

7 个 partial records 仍保留在 Candidate Source Corpus Inventory，并通过 Source Quality
Exception Pool 记录；最终是否有特殊用途不能绕过 provenance 和 review。

### 15.2 不能单独作为 Hard Exclusion 的信号

不能仅因以下原因排除 Document：

- `filename_parse_status = unmatched`；
- `text_layer_status = text_absent`；
- `text_layer_status = mixed_or_uncertain`。

这些是 routing / review signals。特别是 `text_absent` 可能对应 Multimodal Benchmark
Source Candidate。

## 16. Benchmark Source Corpus Registry

### 16.1 核心 Artifact

Phase 2 的核心 derived Artifact 设计为：

```text
benchmark_source_registry.parquet
```

一行对应一个 selected physical source document。Registry 只收录最终
`selection_status=selected` 的记录；eligible / candidate / review_required / excluded
等完整决策不放入 Registry，而放入 `source_selection.parquet`。

### 16.2 Registry 字段

至少包含：

| Field | 说明 |
| --- | --- |
| `file_instance_id` | Physical File Instance 标识 |
| `sha256` | Binary identity |
| `source_root_id` | Source Root |
| `relative_path` | Source 相对路径 |
| `parent_group` | 原始 Source Group |
| `primary_domain` | Calibration 后的 Primary Domain |
| `secondary_domains` | 0–3 个 Secondary Domain |
| `selection_status` | Source Selection 状态 |
| `selection_reason` | 选择或排除原因 |
| `text_layer_status` | Text-layer signal |
| `exact_duplicate_group_id` | Exact duplicate relation |
| `exact_duplicate_representative` | 是否为 deterministic representative |
| `taxonomy_annotation_revision` | Annotation revision |
| `source_selection_revision` | Selection policy revision |
| `document_family_id` | document-family / near-duplicate review 结果，未完成时为 TBD |
| `family_review_status` | document-family review 状态 |

Registry 不覆盖或重写 `files.parquet`，且只包含：

```text
selection_status = selected
```

`source_selection.parquet` 保存 `eligible`、`candidate`、`review_required`、`selected`、
`excluded` 的完整决策集，并通过 revision 和 manifest 关联 Registry。

`source_selection.parquet` 和最终 Registry 都预留：

- `document_family_id`；
- `family_review_status`。

document-family / near-duplicate review 必须在 Gate 2D 最终 Registry 前完成；具体算法可
在 Gate 2C 后单独设计，不在 Gate 2A 擅自冻结。

## 17. Phase 2 Artifact Layout

建议的 Remote Runtime Layout：

```text
/data/suzhe/migb/
  phase2/
    runs/
      <phase2_run_id>/
        calibration_sample.parquet
        calibration_evidence.jsonl
        taxonomy_annotations.parquet
        taxonomy_conflicts.parquet
        source_selection.parquet
        benchmark_source_registry.parquet
        manifest.json
        statistics.json
```

本节只定义设计 Layout。本任务不创建 `/data/suzhe/migb/phase2`，不创建任何 Phase 2
Runtime Artifact。

Gate 2B 实际只需要产生以下 Artifact：

```text
calibration_sample.parquet
calibration_evidence.jsonl
manifest.json
statistics.json
```

Gate 2B 不创建空的 `taxonomy_annotations.parquet`、`taxonomy_conflicts.parquet`、
`source_selection.parquet` 或 `benchmark_source_registry.parquet` 来伪装后续阶段已执行。
每个已产生的 Artifact 的 `manifest.json` 至少记录：

- `stage`；
- `artifact_type`；
- `schema_version`；
- `status`。

Git 中保存：

- docs；
- configs；
- code；
- small reports；
- schema definitions。

大规模 Calibration Runtime Artifact 不提交 Git。

## 18. Phase 2 Gates

### Gate 2A — Design Freeze

Gate 2A 冻结：

- Main Sample sampling strategy；
- Audit Pools、priority 和互斥规则；
- duplicate handling；
- Evidence v0.1（含 Evidence Schema）；
- Annotation Schema；
- agreement / conflict logic；
- Taxonomy Calibration metrics；
- Source Selection Framework；
- Artifact contracts。

Gate 2A 不冻结：

- final Source Selection quota；
- final Benchmark Source Corpus size；
- actual annotator model IDs；
- document-family algorithm。

当前状态：`PASSED`。Gate 2A 通过只表示 Phase 2 Design Gate 已完成，不表示 Phase 2
已经完成，也不表示已经创建 Calibration Sample 或 Benchmark Source Corpus Registry。

Gate 2A 通过后才允许进入 Gate 2B；Gate 2B 通过前仍不得运行 Taxonomy Annotator。

### Gate 2B — Calibration Sample & Evidence

Gate 2A 通过后，才可以执行：

```text
600 Main Sample + Audit Pools + Lightweight Evidence
```

Gate 2B 只验证：

- sampling accounting；
- Evidence quality；
- Source Safety；
- Artifact Schema；
- Source Provenance completeness。

Gate 2B 不执行 Taxonomy Annotation、semantic Source Selection 或 document-family review。
Gate 2B Evidence Verdict 冻结为：

```text
PASS
PASS WITH EVIDENCE REVISION
FAIL
```

Gate 2B 当前最终状态为 `PASSED`，采用的 Evidence Contract 为
`evidence-v0.3-adaptive-v0.1`。其含义是：Gate 2B 的 Sampling、Artifact Pipeline 和
Primary Evidence 已完成验证，并已验证 RapidOCR fallback 能覆盖固定 Problem / Control
诊断项；它不表示已经执行 Taxonomy Annotation。

Evidence 过短、只有 front matter、出现乱码或无法支持稳定 Domain 判断时，不得以
Annotation 静默绕过 Evidence 问题。进入 Gate 2C 后，按 annotation-side retry contract
由 `evidence_usability` 和 `taxonomy_fit = insufficient_evidence` 决定是否执行一次
Conditional RapidOCR fallback；A/B 必须使用相同的最终 Evidence。

Gate 2B 不进行 60454 文档的大规模 Corpus Classification。

### Gate 2C — Taxonomy Calibration & Policy Freeze

Gate 2C 已获授权，但必须按以下顺序进入，不能在 Gate 2B 通过后直接执行完整 Annotation：

```text
Gate 2C-A  Annotation Execution Design Freeze
Gate 2C-B  20-item Annotation Dry-run
Gate 2C-C  Full 600-item Taxonomy Calibration
Gate 2C-D  Calibration Review + Taxonomy Decision + Source Selection Policy Freeze
```

Gate 2C-A 和 Gate 2C-B 通过前，不执行完整 600-item 双 Annotator Annotation。Gate 2C
执行骨架见 `docs/14_phase2_gate2c_taxonomy_annotation_design.md`；实际 Annotator model
ID、provider、prompt 和 inference parameters 仍待 Gate 2C-A 冻结。

完成：

- dual independent annotation；
- agreement / conflict analysis；
- human / Project Owner review；
- taxonomy gap review；
- Parent Group × Domain analysis。

Gate 2C 结束时冻结：

- Taxonomy revision；
- Source Selection Policy v0.1；
- actual annotator configuration；
- domain / temporal / group / modality strategy；
- Source Selection Candidate Pool policy。

形成 Taxonomy Calibration Report，然后决定：

- `Benchmark Taxonomy v0.2`；或
- 保留 v0.1 并记录 refined definitions。

### Gate 2D — Source Selection

基于已通过 Calibration Review 的 Taxonomy 和冻结的 Source Selection Policy，执行：

```text
Source Selection Candidate Pool
        → semantic review
        → document-family / near-duplicate review
Benchmark Source Corpus Registry
```

document-family / near-duplicate review 必须在最终 Registry 生成前完成。Gate 2D PASS 后，
Phase 2 才可以关闭并进入：

```text
Phase 3 - Corpus Processing
```

## 19. Open Questions

以下问题的状态按 Gate 2A 设计冻结结果记录；未解决项仍不在本设计中擅自决定：

1. Main Calibration Sample 是否最终冻结为 600？—— `Resolved v0.1`
2. `base_quota=15/group` 是否冻结？—— `Resolved v0.1`
3. `max_extracted_chars=12000` 是否合适？—— `Provisional v0.1 for Gate 2B`
4. 只抽前 3 页是否足以判断 Domain？—— `Provisional v0.1 for Gate 2B`
5. LLM Annotation 使用哪两个独立 Annotator？—— `Deferred; freeze before Gate 2C execution`
6. `provisionally_agreed` Sample 的人工抽检比例是否为 10%？—— `Resolved v0.1; deterministic`
7. Benchmark Source Corpus 是否需要数量目标？—— `Deferred to Gate 2C Source Selection Policy`
8. `text_absent` 文档何时进行 OCR / visual routing？—— `Deferred; remains an independent Audit Pool and is not bulk-OCR'd in Gate 2C dry-run`
9. document-family resolution 应在 Phase 2 后半段还是 Phase 3 前完成？——
   `Resolved at workflow level: before final Gate 2D Registry`
10. temporal balancing 是否需要进入 Source Selection Policy？—— `Deferred to Gate 2C`
11. parent-group diversity 是否需要硬 quota？—— `Deferred to Gate 2C`
12. Benchmark Source Corpus 是否需要按 Track 预留 visual-source pool？—— `Deferred to Gate 2C`

## 20. 当前禁止事项

当前文档更新后，本次仍只停留在 Gate 2C 执行设计边界，禁止：

- 创建 Calibration Sample；
- 读取 600 Main Sample 或 Audit Pools 中真实 PDF；
- 调用 LLM；
- 立即执行 Taxonomy Annotation；
- 执行 Source Selection；
- 创建 Benchmark Source Corpus Registry；
- 运行 MinerU；
- 在 Gate 2C-A 设计冻结和 Gate 2C-B dry-run 授权前运行 OCR；
- 执行 Full PDF Parsing；
- 生成 Benchmark Questions；
- 生成 Ground Truth。

本次仅完成：

```text
DESIGN ONLY
```
