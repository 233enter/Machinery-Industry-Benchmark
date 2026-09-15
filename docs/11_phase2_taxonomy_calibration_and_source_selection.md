# Phase 2 Taxonomy Calibration & Source Selection

Project: Mechanical Industry General Benchmark
Document: Phase 2 Taxonomy Calibration & Source Selection Design
Version: 0.1
Status: Draft - Awaiting Review
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Phase 2 Taxonomy Calibration Design

## 1. 文档定位与设计边界

本文档是 Phase 2 的主要设计 Contract，定义基于已完成 Corpus Inventory 进行 Taxonomy
Calibration 和 Source Selection 的工作流、抽样原则、轻量证据 Contract、标注 Contract、
Source Selection Policy、Artifact Layout 和阶段 Gate。

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

## 3. Phase 2 总体流程

Phase 2 的候选流程为：

```text
Full Corpus Inventory
        ↓
Eligibility / Signal Stratification
        ↓
Taxonomy Calibration Sampling
        ↓
Lightweight Evidence Extraction
        ↓
Taxonomy Annotation
        ↓
Taxonomy Calibration Analysis
        ↓
Taxonomy v0.2 Decision
        ↓
Source Selection Policy
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

### 4.1 Calibration Main Sample 的基本 Eligibility

Taxonomy Calibration Main Sample 优先从以下条件同时满足的 File Instance 中抽取：

```text
inventory_status = success
pdf_open_status = success
page_count > 0
```

Full Inventory 中的 7 个 partial records 不混入 Main Sample：

- 6 个 zero-page PDF；
- 1 个 `FileDataError` / open failure 记录。

它们进入独立的 `Source Quality Exception Pool`，保留原始 provenance 和错误状态，但不
用于 Main Taxonomy Calibration。

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
rule、quota accounting、sample item order 和 `calibration_sample_id`。

## 5. Taxonomy Calibration Sample v0.1

### 5.1 目标

设计目标为：

```text
Taxonomy Calibration Main Sample target ≈ 600 PDFs
```

这是 Taxonomy Calibration Sample，不是最终 Benchmark Sample，也不是 Benchmark Source
Corpus 数量目标。

如果 eligible population 不足以满足目标，实际数量必须如实记录，不得通过混入不符合
eligibility 的 PDF 强行补齐。

### 5.2 Stage A — Group Base Coverage

当前有 20 个 Parent Groups。对每个 Parent Group 定义：

```text
base_quota = min(15, eligible_population)
```

在 eligible population 允许时，Stage A 提供：

```text
20 × 15 = 300
```

个基础覆盖名额，确保每个 Source Group 都有机会进入 Calibration。

### 5.3 Stage B — Proportional Allocation

Stage A 后的剩余目标为：

```text
600 - sum(base_quota)
```

对每个 Parent Group 的剩余 eligible population 做 proportional allocation，使用与 D3
一致的 Hamilton / Largest Remainder 思路：

1. 先按比例计算整数 base allocation；
2. 按 remainder 排序分配剩余名额；
3. 使用固定的 Parent Group canonical order 处理 tie；
4. 不超过各 Group 的剩余 eligible capacity；
5. 记录每个 Group 的 population、base quota、proportional allocation、remainder、
   final quota 和 actual selected count。

最终目标为 600，前提是 eligible population 足够。具体 quota、tie-break 和配置值在
Gate 2A 前冻结。

### 5.4 Sample Item Selection

在每个 Group 和 signal strata 内，使用稳定 canonical order（至少包含
`parent_group`、`relative_path`、`file_instance_id`）进行确定性选择。每一个 selected
item 必须保留：

- `file_instance_id`；
- `parent_group`；
- `relative_path`；
- source snapshot / inventory run 引用；
- selection stage、method 和 quota accounting；
- exact duplicate representative 信息；
- 参与的 signal strata。

### 5.5 不采用的抽样方法

当前不采用：

- 无分层的 random 600；
- 每个 Group 固定取前 30 个；
- 按文件名或目录名直接推断 Domain 后再抽样；
- 把 D1、D2、D3 历史样本或 7 个 partial records 当作必然的 Main Sample 输入。

## 6. Audit Pools

Audit Pools 与 600 个 Main Sample 分开设计，用于观察异常输入、证据路径和 Metadata
pattern。所有 Pool 都必须保留独立的 pool label、selection rule、target、actual count
和 provenance。

### 6.1 Source Quality Exception Pool

```text
target = all 7 partial records
```

包括 6 个 zero-page PDF 和 1 个 `FileDataError` / open failure。该 Pool 用于确认异常
状态如何影响后续 Source Selection，不用于 Main Domain Calibration。

### 6.2 Text-absent Audit Sample

```text
target ≈ 60 PDFs
```

在 Parent Group 间进行 deterministic stratified sampling，用于判断 text-absent 文档是否
可能成为 Multimodal / OCR 路径的 Source Candidate。

本阶段不执行 OCR，不因为 `text_absent` 自动排除文档。

### 6.3 Mixed Text Audit

Full Inventory 中当前 `mixed_or_uncertain=163`。如果 eligible population 允许，设计目标为：

```text
target ≈ 40 PDFs
```

用于观察 Mixed text-layer 的证据可用性与跨 Group 分布。

### 6.4 Filename-unmatched Audit

```text
target ≈ 60 PDFs
```

用于观察 filename metadata pattern，不用于修改 Filename Parser，不用于排除 Document。

### 6.5 Pool Boundary

Audit Pool 的目的分别是质量、文本层、混合状态和 filename pattern 观察。它们不能被解释
为最终 Benchmark Source Corpus 的入选名单，也不能替代后续 Source Selection Review。

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
- 进入独立 Text-absent Audit Sample；
- 可能成为 Multimodal Benchmark Source Candidate；
- 本阶段不执行 OCR。

`mixed_or_uncertain`：

- 进入 Mixed Text Audit；
- 作为 evidence quality / routing signal；
- 不自动排除。

## 9. Lightweight Evidence Extraction v0.1

### 9.1 工具和范围

Calibration Evidence 只针对 Calibration Sample 和 Audit Pools 使用 PyMuPDF lightweight
extraction，不使用 MinerU，不进行 Full Corpus Parsing，不在 Source Corpus 写回。

### 9.2 页面范围

每个 Calibration PDF 提取：

- filename；
- filename parsed title；
- PDF metadata title；
- page count；
- first page text；
- second page text；
- optional third page text。

当 `page_count >= 3` 时，提取前 3 页；当页数不足 3 页时，提取所有现有页面。页面顺序
必须被保留在 Evidence Record 中。

这一步是用于 Domain Calibration 的轻量 Evidence，不是完整解析，不代表全文语义已经
覆盖。

### 9.3 Evidence Character Cap

每个 Document 的 Evidence 设置：

```text
max_extracted_chars = 12000
```

按页面顺序截断，并记录：

- `extracted_page_indices`；
- `extracted_char_count`；
- `evidence_truncated`。

发生截断时，`evidence_truncated=true`；这不是 Parser Failure。

### 9.4 Calibration Evidence Schema

| Field | 说明 |
| --- | --- |
| `calibration_sample_id` | 本次 Calibration Sample 的稳定标识 |
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
| `evidence_keywords` | 支持判断的关键词或短语 |
| `evidence_rationale` | 基于 Evidence 的判断理由 |
| `review_status` | 至少包括独立标注、临时一致、冲突待审和人工复核状态 |

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

## 11. Annotation Method

### 11.1 LLM 的角色

后续实际 Calibration 可以使用 LLM 作为辅助 Annotator，但必须明确：

```text
LLM != Ground Truth Authority
```

Taxonomy Annotation 结果不是最终 Benchmark Ground Truth。单个 LLM 的输出不能单独决定
Taxonomy Definition 或 Source Selection Policy。

### 11.2 Independent Annotation

推荐两次相互独立的标注：

```text
Pass A: Model A / independent annotation
Pass B: Model B or independent prompt / independent annotation
```

Pass B 不接收 Pass A 的答案。两个 Pass 必须使用相同版本的 Evidence Contract、Taxonomy
Definition 和标注 Schema，但保持输出独立。

### 11.3 Agreement 与 Conflict

当以下条件同时成立时，可以标记为：

```text
provisionally_agreed
```

- `primary_domain` 一致；
- `taxonomy_fit` compatible；
- 没有必须升级的低置信度或 Evidence 缺失问题。

以下情况进入 Review Queue：

- primary domain disagreement；
- `taxonomy_gap`；
- `out_of_scope`；
- `low confidence`；
- `insufficient_evidence`；
- cross-domain disagreement。

### 11.4 Human Review

在当前没有完整机械领域专家团队的条件下，v0.1 采用风险优先的人工复核设计：

- Review 所有 conflict；
- Review 所有 `taxonomy_gap`；
- Review 所有 `out_of_scope`；
- Review 所有 `low confidence`；
- Review 所有 `insufficient_evidence`；
- 对 `provisionally_agreed` Sample 做约 10% 随机审计。

专家资源、最终复核人和复核覆盖率仍须在 Gate 2A 前确认；本设计不把人工复核能力假设为
无限。

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

## 14. Source Selection Policy v0.1

### 14.1 Source Selection 目标

Source Selection 的目标是决定哪些 Document 适合作为后续 Benchmark Item Construction 的
Source，而不是简单给 60454 个 PDF 打 Domain Label。

Source Selection 必须在 Taxonomy Calibration Review 和 Taxonomy 版本决策之后执行，并
记录：

- selection input Inventory Run；
- Taxonomy revision；
- selection policy revision；
- selection status；
- selection reason；
- provenance 和 duplicate relation。

### 14.2 Selection Status

初始设计允许以下状态：

```text
selected
eligible
review_required
excluded
```

所有非 `selected` 记录也要保留 reason，不得静默删除。

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

### 14.4 Source Group 与 Domain

必须保持：

```text
parent_group != D01–D12
```

Source Selection 应使用 `Parent Group × Domain Distribution` 理解 Source Composition，
不能根据目录名直接分类，也不能让 PDF 数量最多的 Group 自动成为 Benchmark 权重最高的
Domain。

## 15. Hard Exclusion 与 Non-exclusion Rules

### 15.1 Hard Exclusion Candidates

以下为 Source Selection 的 Hard Exclusion Candidates：

| Condition | Selection handling |
| --- | --- |
| `pdf_status = corrupted_or_invalid` | `excluded`，reason 记录为 invalid PDF |
| `pdf_open_status = failed` | `excluded`，reason 记录为 open failure |
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

建议一行对应一个 selected physical source document。具体一行粒度、是否包含 review_required
候选以及最终 Schema，在 Gate 2A 和 Source Selection Review 中冻结。

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

Registry 不覆盖或重写 `files.parquet`。如果需要同时保存 eligible / review_required /
excluded 的完整决策集，使用独立的 `source_selection.parquet`，并通过 revision 和
manifest 关联 Registry。

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

Git 中保存：

- docs；
- configs；
- code；
- small reports；
- schema definitions。

大规模 Calibration Runtime Artifact 不提交 Git。

## 18. Phase 2 Gates

### Gate 2A — Design Freeze

通过条件至少包括：

- Sampling strategy frozen；
- Evidence extraction frozen；
- Annotation Schema frozen；
- Annotation method frozen；
- Taxonomy Calibration metrics frozen；
- Source Selection Policy frozen；
- Artifact contracts frozen。

Gate 2A 未通过前，不运行 Calibration Sample。

### Gate 2B — Calibration Sample & Evidence

Gate 2A 通过后，才可以执行：

```text
600 Main Sample + Audit Pools
```

验证至少包括：

- sampling accounting；
- evidence quality；
- Source Safety；
- Artifact Schema；
- provenance completeness。

Gate 2B 不进行 60454 文档的大规模 Corpus Classification。

### Gate 2C — Taxonomy Calibration

完成：

- annotation；
- agreement analysis；
- conflict review；
- taxonomy gap review；
- Parent Group × Domain analysis。

形成 Taxonomy Calibration Report，然后决定：

- `Benchmark Taxonomy v0.2`；或
- 保留 v0.1 并记录 refined definitions。

### Gate 2D — Source Selection

基于已通过 Calibration Review 的 Taxonomy 和冻结的 Source Selection Policy：

```text
Source Selection Policy
        →
Benchmark Source Corpus Registry
```

Registry 经 Review 后，Phase 2 才可以关闭并进入：

```text
Phase 3 - Corpus Processing
```

## 19. Open Questions

以下问题保持 TBD，不在本设计中擅自解决：

1. Main Calibration Sample 是否最终冻结为 600？—— TBD
2. `base_quota=15/group` 是否冻结？—— TBD
3. `max_extracted_chars=12000` 是否合适？—— TBD
4. 只抽前 3 页是否足以判断 Domain？—— TBD
5. LLM Annotation 使用哪两个独立 Annotator？—— TBD
6. `provisionally_agreed` Sample 的人工抽检比例是否为 10%？—— TBD
7. Benchmark Source Corpus 是否需要数量目标？—— TBD
8. `text_absent` 文档何时进行 OCR / visual routing？—— TBD
9. document-family resolution 应在 Phase 2 后半段还是 Phase 3 前完成？—— TBD
10. temporal balancing 是否需要进入 Source Selection Policy？—— TBD
11. parent-group diversity 是否需要硬 quota？—— TBD
12. Benchmark Source Corpus 是否需要按 Track 预留 visual-source pool？—— TBD

## 20. 当前禁止事项

本设计完成后仍禁止：

- 创建 Calibration Sample；
- 读取 600 个真实 PDF；
- 调用 LLM；
- 执行 Taxonomy Annotation；
- 执行 Source Selection；
- 创建 Benchmark Source Corpus Registry；
- 运行 MinerU；
- 运行 OCR；
- 执行 Full PDF Parsing；
- 生成 Benchmark Questions；
- 生成 Ground Truth。

本次仅完成：

```text
DESIGN ONLY
```
