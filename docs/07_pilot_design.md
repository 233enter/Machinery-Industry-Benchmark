# Mechanical Industry General Benchmark Pilot Design v0.1

Project: Mechanical Industry General Benchmark
Document: Pilot Design
Version: 0.1
Status: Draft - Pending Review
Phase: Phase 0 - Benchmark Design
Current Task: Pilot Design v0.1

## 1. Pilot 的定位

Pilot Benchmark 不是 Final Benchmark V1 的缩小复制品，而是一个 Benchmark Validation Experiment。

Pilot 的核心目标是验证：

1. Benchmark Taxonomy 是否可操作；
2. Data Specification 是否足以表示真实题目；
3. Knowledge、Calculation、Multimodal 三条构题路线是否可行；
4. Ground Truth 是否能够稳定验证；
5. Verification / QA 是否能发现坏题；
6. Evaluation Specification 是否能够稳定评分；
7. 题目是否具有合理难度；
8. 题目是否能区分不同能力层级模型；
9. Multimodal Item 是否真正依赖视觉输入；
10. Dataset 是否存在重复、来源集中和污染问题；
11. 是否具备从 Pilot 扩展到 Benchmark V1 的条件。

Pilot 的最终产物不仅是一份约 500 Item 的 Dataset，更包括：

- Quality Findings；
- Calibration Findings；
- Failure Patterns；
- Revised Construction Rules；
- Revised QA Rules；
- Expansion Recommendation。

Pilot Design v0.1 只定义实验问题、采样原则、进入条件、观察指标和决策边界，不创建真实 Pilot Item，也不提前给出实验结果。

## 2. Pilot Research Questions

### RQ1

当前 D01–D12 Domain Taxonomy 是否可以实际覆盖真实机械工业资料？

### RQ2

K1–K8、C1–C8、M1–M11 是否都能够构造出：

- 清晰；
- 有 Ground Truth；
- 有区分度；

的题目？

### RQ3

40 / 30 / 30 的 Track Sampling Target 是否合理？

### RQ4

当前 Easy / Medium / Hard Design Difficulty 是否与模型实际表现一致？

### RQ5

Knowledge Track 是否过度依赖事实记忆和单选题？

### RQ6

Calculation Track 是否过度集中于直接公式代入？

### RQ7

Multimodal Track 是否出现“有图但不需要看图”的伪多模态问题？

### RQ8

Current Answer Type / Evaluator 能否稳定覆盖真实机械工业任务？

### RQ9

不同模型是否呈现足够的 difficulty gradient / discrimination？

### RQ10

Pipeline 中最大的质量瓶颈到底出现在以下哪一层：

~~~text
Parsing
Evidence
Generation
Ground Truth
Verification
Evaluation
~~~

## 3. Pilot Target Size

采用 Project Charter 的 provisional target：

~~~text
≈500 accepted Pilot Items
~~~

初始 Track Target：

~~~text
T1 Mechanical Knowledge      ≈ 200
T2 Engineering Calculation   ≈ 150
T3 Multimodal Understanding  ≈ 150
~~~

即约：

~~~text
40 / 30 / 30
~~~

该比例是 Pilot Initial Sampling Target，不是最终 Benchmark V1 的永久比例。Phase 6 完成模型校准后，可以根据真实结果建议调整。

Pilot 不要求严格得到 200 / 150 / 150。合理的小范围偏差允许存在，但必须在 Pilot Dataset Card 和 Pilot Final Report 中说明原因及影响。

## 4. Candidate Pool 必须大于 Pilot

Pilot 不能只生成 500 道题然后全部纳入 Pilot。

逻辑关系必须满足：

~~~text
Candidate Pool
    >
Accepted Pilot Dataset
~~~

Candidate Pool 必须允许：

- reject；
- revise；
- deduplicate；
- rebalance；
- replace。

Pilot Design v0.1 不强制锁死 Candidate Pool 数量或固定生成倍率。候选池规模应在 Phase 4 / Phase 5 根据 rejection rate、Track、Source Quality 和 Human Review Cost 决定。

## 5. Pilot Dataset 是 Internal Calibration Dataset

Pilot Benchmark 默认定位为：

~~~text
internal calibration dataset
~~~

Pilot 不等于 Public Benchmark Release。因此：

- Pilot Evidence 可以保持 internal；
- Pilot Visual Asset 不要求公开；
- Pilot Result 不要求公开 Leaderboard；
- Pilot Item 可以根据 Calibration 产生 Revision；
- Pilot Dataset Version 必须被冻结和保存。

任何后续发布策略都必须经过独立的 visibility、rights_status 和 release policy 判断，不能因为 Pilot 已完成就自动发布。

## 6. Sampling Dimensions

Pilot 不能只按照 Track 采样，至少同时监控：

~~~text
Primary Track
Domain
Capability
Task
Design Difficulty
Answer Type
Modality / Visual Type
Source Type
Source Document
Document Family
Construction Method
~~~

Pilot Sampling 的目标是“足够覆盖”，而不是让所有 Cell 完全均匀。

采样记录应保留每个 Item 的所有适用维度，避免只保留用于配额的单一标签。未达到覆盖目标的 Cell、被排除的 Cell 和不适用的 Cell 都要有可解释记录。

## 7. Domain Coverage

目标是在存在合适来源和有效任务的前提下，尽量覆盖 D01–D12。不要要求 500 / 12 平均分配。

原因包括：

- 不同 Domain 适合的 Track 不同；
- 数据来源不同；
- 可构题性不同；
- Ground Truth 可验证性不同。

Pilot 必须输出 Domain Coverage Report，至少包括：

~~~text
domain
item_count
track_distribution
capability_distribution
source_count
document_family_count
~~~

如果某个 Domain 缺失或明显不足，必须记录原因，例如：

~~~text
insufficient_source
poor_parseability
no_reliable_ground_truth
out_of_scope
sampling_gap
~~~

Domain 不应静默消失，也不能把 PDF 数量自动当作该 Domain 的 Pilot 权重。

## 8. Capability Coverage

Pilot 的目标不是每个 Capability 数量完全相同，而是验证 Taxonomy 中各类任务是否能够实际构造、验证和评测。

### 8.1 T1 Mechanical Knowledge

需要检查 K1–K8 是否均能形成有效任务，特别防止 K1 Fact & Terminology 大量占据 Knowledge Track。

Knowledge Track 应尽量包含：

- understanding；
- comparison；
- selection；
- reasoning；
- diagnosis；
- compliance judgment。

Knowledge Track 不应退化为机械知识背诵题库，也不应全部采用 Single Choice。

### 8.2 T2 Engineering Calculation

需要尽量检查 C1–C8，特别防止 C1 Direct Formula Application 和 C2 Unit Conversion 占据大部分 Calculation Track。

Pilot 应重点验证以下类型是否可以稳定构造和验证：

~~~text
C3 Multi-step
C4 Formula Selection
C5 Table/Data + Calculation
C6 Sizing
C7 Constraint-aware
C8 Quantitative Comparison
~~~

### 8.3 T3 Multimodal Understanding

需要尽量检查 M1–M11，特别防止 Pilot Multimodal 主要由 OCR、dimension reading 和 simple identification 组成。

必须包含足够的：

~~~text
Structure Understanding
Projection / Multi-view
Assembly Relationship
Geometric Reasoning
Anomaly Detection
Consistency Judgment
~~~

以验证真正的机械视觉推理能力。这里仅引用已有 Taxonomy 维度，不在 Pilot Design 中重新定义 Capability。

## 9. Difficulty Coverage

Pilot 初始使用以下 Design Difficulty：

~~~text
easy
medium
hard
~~~

不强制三个难度各占三分之一，但必须避免绝大多数题都是 Easy。

Pilot 需要通过 Phase 6 Model Panel 计算或推导：

~~~text
empirical_difficulty
~~~

并比较：

~~~text
design_difficulty
vs
empirical_difficulty
~~~

输出 Difficulty Calibration Matrix，例如：

~~~text
Design Easy → Empirical Easy
Design Easy → Empirical Hard
Design Hard → Empirical Easy
...
~~~

目的在于为未来 V1 的 Difficulty Rule 提供实证依据。

## 10. Answer Type Coverage

Pilot 至少需要实际验证：

~~~text
single_choice
multiple_choice
true_false
numeric
short_answer
structured_answer
~~~

但不能为了覆盖 Answer Type 而强行构造不自然的题目。Question Type 应服从任务，不应为了凑 multiple choice 数量而把适合 numeric 的问题强行改成选择题。

具体原则：

- Knowledge Track 不应全部是 Single Choice；
- Calculation Track 应以 Numeric 为主，但允许其他合理形式；
- Multimodal 应覆盖 choice、numeric、short answer、structured answer 等自然任务。

## 11. True / False 使用原则

True / False 的随机正确率较高，因此 Pilot 可以包含用于验证 Evaluator 的 True / False Item，但不应让其成为主要题型。

Pilot Report 应单独报告：

~~~text
true_false_count
~~~

防止大量二分类题人为抬高模型得分。

## 12. Source Sampling

Pilot Source 应来自 Phase 2 选定的 Benchmark Source Corpus。

来源候选可以优先考虑：

~~~text
standard
authoritative handbook
high-quality textbook
industry specification
technical manual
technical report
paper
~~~

具体优先级仍需结合以下因素判断：

- authority；
- freshness；
- Ground Truth availability；
- parseability；
- copyright / usage constraints。

Pilot 不要求 Source Type 完全均衡。每个 Source 的进入、排除、限制和可见性应能回溯到 Source Provenance 与 Source Selection 结果。

## 13. Source Concentration

Pilot 必须监测：

~~~text
items_per_document
items_per_document_family
items_per_source_type
items_per_domain_source
~~~

避免 500 道题实际上主要来自极少数教材、标准或技术资料。

Pilot Design v0.1 不定义固定的 max X% per book 或其他硬阈值，因为真实 Corpus 分布尚未知。

Pilot Report 必须报告 Top Source Concentration，例如：

~~~text
Top 1 document family share
Top 5 document family share
Top 10 document family share
~~~

是否需要硬阈值在 Pilot 后结合真实分布和质量影响决定。

## 14. Document-family Isolation

Pilot Source Sampling 必须把 document-family_id 作为重要治理单位，而不只是把 PDF file 当作独立 Source。

同一本书的：

- 扫描版；
- OCR 版；
- 不同文件来源；
- 不同版次；

不能简单视作完全独立 Source。

document-family 隔离同时服务于：

- Duplicate Control；
- Contamination Control；
- Source Concentration Analysis。

Pilot 的 Source Manifest 应保留 Document Family 关系，即使 Phase 1 只完成了部分 family resolution。

## 15. Knowledge Construction Pilot

Pilot Knowledge 构题链：

~~~text
Source Evidence
      ↓
Candidate Question
      ↓
Candidate Ground Truth
      ↓
Source Verification
      ↓
Ambiguity Check
      ↓
Distractor / Answer Check
      ↓
Human QA
~~~

LLM 可以：

- propose question；
- rewrite；
- create distractors；
- assist classification。

但 LLM 不能独立宣布 Ground Truth Verified。Candidate Question 必须保留 Source Provenance、Construction Method 和后续 Verification Records。

## 16. Knowledge Item Quality Checks

Knowledge Item 至少检查：

~~~text
source_support
answer_uniqueness
question_clarity
distractor_quality
taxonomy_fit
difficulty_fit
language_quality
ambiguity
~~~

对于选择题，Incorrect Option 应满足：

- plausible；
- non-overlapping；
- 在 intended interpretation 下 clearly incorrect。

不得使用明显荒谬的选项制造虚假难度。无法确认唯一答案、题意或来源支持时，应进入 revise、expert escalation 或 reject。

## 17. Calculation Construction Pilot

使用 System Architecture 已定义的 Calculation 流程：

~~~text
Formula Evidence
→ Formula Structuring
→ Variables / Constraints
→ Parameterized Problem
→ Deterministic Solver
→ Ground Truth
→ Unit / Tolerance Verification
~~~

Pilot 重点验证：

- formula extraction correctness；
- variable definition；
- valid value range；
- unit correctness；
- physical plausibility；
- deterministic reproducibility；
- rounding / tolerance；
- multiple-solution ambiguity；
- constraint validity。

LLM 可以辅助解释或构题，但不能成为 Numeric Ground Truth 的唯一来源。

## 18. Calculation Parameter Sampling

参数不能纯随机生成，必须满足：

~~~text
engineering-valid range
physical constraints
formula applicability
unit consistency
non-degenerate result
~~~

应避免：

- 负长度；
- 非物理效率；
- 不可能温度或压力；
- 除零；
- 公式适用范围之外；
- 数值极端导致的无意义问题。

Parameter Generator 必须记录：

~~~text
template_id
parameter_set_id
generation_version
seed（如适用）
~~~

具体参数范围、求解器和阈值不在 Pilot Design v0.1 中预先锁定。

## 19. Calculation Variant Leakage

同一个 Formula Template 生成多题时，不能让 Pilot 被大量近似题填满。

必须检查：

~~~text
template concentration
parameterized sibling count
semantic near-duplicate
~~~

Pilot Calibration Report 应能够按照 template_id 分析题目数量、模型表现、重复风险和题目质量。

## 20. Multimodal Construction Pilot

逻辑流程：

~~~text
Source Visual Asset
      ↓
Relevant Region / Evidence
      ↓
Visual Question
      ↓
Ground Truth
      ↓
Visual Dependency Verification
      ↓
Human QA
~~~

T3 Item 必须声明：

~~~text
visual_dependency_required = true
~~~

构题阶段声明视觉依赖，不等于真正通过 Visual Dependency Check。

## 21. Visual Dependency Test

Pilot 必须对 T3 Item 进行 Visual Dependency Validation，至少设计两种条件：

### Full Condition

~~~text
Question + Visual Input
~~~

### Text-only Ablation

~~~text
Question without Visual Input
~~~

目标是检查模型是否能够在没有图像的情况下依靠以下信息回答：

- Question wording；
- world knowledge；
- leakage；
- obvious option pattern。

如果 Text-only Condition 与 Full Condition 表现非常接近，Item 应进入 Review。

Pilot Design v0.1 不设死统一百分比阈值。Pilot 需要先收集真实分布，再决定后续 V1 的诊断阈值或淘汰规则。

## 22. Visual Asset Quality

T3 至少检查：

- image readable；
- crop complete；
- resolution sufficient；
- no missing annotation；
- bbox correct；
- image-question alignment；
- multi-image order；
- no accidental answer leakage。

例如，不应把文件名 answer_bearing_failure.png 等隐藏信息暴露给模型。Asset 的路径、元数据、文件名和预览内容都应纳入泄漏检查范围。

## 23. Pilot Verification Stack

Pilot Item 至少经过适用的：

~~~text
Schema Validation
Source Verification
Ground Truth Verification
Unit / Calculation Verification
Duplicate Check
Ambiguity Check
Visual Dependency Check
Contamination Check
Human Review
~~~

不是每个 Item 使用完全相同的 Verifier。例如：

- Calculation Verifier 对 T2 强制适用；
- Visual Dependency Checker 对 T3 强制适用；
- Unit / Tolerance Verification 对适用的 Numeric Item 强制适用。

每个检查都应产出可追溯的 Verification Record 或明确的 not_applicable / not_checked 状态。

## 24. 100% Automatic Validation Requirement

进入最终 Pilot Snapshot 前，所有 Item 必须完成所有适用的 machine-checkable mandatory validation，例如：

- Schema；
- Cross-field validation；
- Source reference existence；
- Asset existence；
- Numeric Ground Truth structure；
- unit consistency；
- duplicate scan。

不允许带有“之后再检查”的 critical machine-validatable error 进入 Pilot Snapshot。

100% 的含义是所有适用的强制机器检查都有明确结果，不是要求每个 Item 执行不适用的检查。

## 25. Human Review Strategy

Pilot 规模约 500，因此建议所有最终 Pilot Item 都进行至少一次人工 QA Review。

### 25.1 Human QA Review

Human QA Review 检查：

- question clarity；
- obvious ambiguity；
- source relation；
- answer consistency；
- formatting；
- visual readability。

该层可以由项目团队执行。

### 25.2 Domain Expert Review

以下情况需要较强领域判断，可能升级到 Domain Expert Review：

- difficult engineering judgment；
- standards；
- complex diagnosis；
- ambiguous technical interpretation；
- hard structured answer。

Domain Expert Resource 当前仍为 TBD。因此 Pilot 采用 risk-based escalation，而不是假设所有 500 题都由机械专家逐条审核。

Pilot 必须记录哪些 Item 被升级到 Expert Review、升级原因和处理结论。

## 26. Review Risk Level

可以设计逻辑 Review Risk：

~~~text
low
medium
high
~~~

High Risk 示例：

- Hard structured answer；
- complex standard interpretation；
- non-programmatic calculation Ground Truth；
- failure diagnosis with multiple plausible causes；
- unusual technical terminology；
- conflicting Source Evidence。

具体风险算法、权重和阈值留给后续实现。Pilot Design v0.1 只定义风险分层和升级原则。

## 27. Pilot Admission Criteria

进入 Pilot Dataset Snapshot 的 Item 至少满足：

~~~text
schema validation passed
required provenance available
ground truth verified
critical ambiguity resolved
exact duplicate removed
confirmed contamination resolved
required assets available
~~~

对于 T2，必须完成：

~~~text
programmatic / deterministic ground truth verification
~~~

或有明确、可审计的等价验证方法。

对于 T3，必须完成：

~~~text
visual dependency check
~~~

并通过最终 QA。

## 28. Critical Issue Zero-Tolerance

Pilot Snapshot 中不允许存在尚未解决的：

~~~text
wrong ground truth
missing source evidence
missing required visual asset
schema-invalid item
broken option mapping
known exact duplicate
confirmed answer leakage
~~~

这些属于 Critical Defect，不是“难题”。如果无法在 Snapshot 组装前解决，应将 Item 移出 Snapshot、产生新 Revision，或将其记录为拒绝 / 替代，而不能为凑数量保留。

## 29. Pilot Dataset Artifacts

Pilot 执行阶段至少产生：

~~~text
Candidate Pool Snapshot
QA Issue Registry
Verification Records
Accepted Item Set
Rejected / Revised Item Registry
Pilot Dataset Snapshot
Pilot Dataset Manifest
Pilot Dataset Card
~~~

Evaluation 后还产生：

~~~text
Evaluation Run Manifests
Item-level Results
Calibration Report
Error Analysis
Pilot Final Report
~~~

这些是后续实际执行阶段的 Artifact，不是本次 Phase 0 的真实输出。

## 30. Pilot Dataset Card

Pilot Dataset Card 至少说明：

~~~text
purpose
dataset_version
item_count
track distribution
domain distribution
capability distribution
difficulty distribution
answer type distribution
modality distribution
source distribution
construction methods
verification coverage
known limitations
rights / visibility
~~~

Pilot Dataset Card 不等于最终 Public Benchmark Card。它必须明确 Pilot 是 Internal Calibration Dataset，并说明哪些 Evidence、Asset、Source 和 Result 仅限内部使用。

## 31. Model Panel Purpose

Phase 6 Model Panel 的目标不是做排行榜。模型是：

~~~text
Benchmark Measurement Instruments
~~~

用于检测：

- item difficulty；
- item discrimination；
- scoring problems；
- broken items；
- ambiguous items；
- visual dependency；
- prompt / parser failure；
- ceiling / floor effect。

Pilot Model Panel 的结果首先用于 Calibration，而不是宣布模型排名或形成公开 Leaderboard。

## 32. Model Panel Size

保留此前规划：

~~~text
约 5–10 个 Representative Models
~~~

具体数量根据以下因素确定：

- compute；
- API budget；
- availability；
- model capability。

Pilot Design v0.1 不锁死具体模型名称。Baseline / Anchor Models 仍是 Project Decision Point。

## 33. Model Panel Selection Criteria

未来选择模型时至少考虑：

~~~text
capability level
model size / class
open-weight vs closed
reasoning vs standard
text-only vs multimodal
Chinese / technical language capability
API / local availability
evaluation reproducibility
~~~

目标是形成能力梯度，而不是选择 5–10 个能力完全接近的模型。

## 34. Text-only 与 Multimodal Models

Text-only Model 可以参与：

~~~text
T1
T2
~~~

用于 Calibration。

不支持视觉的模型：

~~~text
T3 = Unsupported
Overall = N/A
~~~

严格遵循 Evaluation Specification。Unsupported 不应被误记为 T3 得分为 0，也不能因为模型不支持视觉而改变 Dataset Snapshot。

T3 Calibration 需要足够数量真正支持视觉输入的模型。文本模型与多模态模型的结果应在报告中清楚区分。

## 35. Official Evaluation Profile

Pilot Model Run 应尽可能使用已经定义的 Official Evaluation Profile：

- single-turn；
- zero-shot；
- no web；
- no RAG；
- no external tools。

如果执行 prompt robustness、option permutation 或 text-only ablation，这些必须是 Diagnostic Profile / Quality Experiment，不能混入 Official Score。

Pilot 的 Profile、Prompt Policy、Adapter、Parser、Evaluator 和 Version 必须记录，具体语义直接遵循 Evaluation Specification。

## 36. Pilot Metrics

### 36.1 Dataset-level

至少记录：

~~~text
item_count
track distribution
domain coverage
capability coverage
difficulty distribution
source concentration
duplicate rate
verification coverage
rejection rate
revision rate
~~~

### 36.2 Item-level

至少记录：

~~~text
model pass rate
parse failure rate
judge usage
judge uncertainty
difficulty mismatch
visual dependency result
error pattern
~~~

### 36.3 Model-level

至少报告：

~~~text
T1
T2
T3
Overall（eligible models）
Domain slices
Capability slices
Difficulty slices
Answer Type slices
~~~

Model-level Score 仍按 Evaluation Specification 的 Track、Overall 和 Eligibility 语义计算，不在本文件重新定义评分算法。

## 37. Empirical Difficulty

Pilot 后每题形成：

~~~text
design_difficulty
empirical_difficulty
~~~

Empirical Difficulty 主要根据 Representative Model Panel 的表现观察。

不要现在定义固定的 accuracy 阈值，例如：

~~~text
>80% = easy
...
~~~

Pilot 的目的之一就是为这些阈值提供数据依据。但必须保留 Model Panel item pass rate 作为基础观察量。

## 38. Discrimination

Pilot 要检查一个 Item 是否能够区分不同能力模型。

v0.1 不强制采用复杂 Psychometric Model。Model Panel 只有约 5–10 个模型时，传统 psychometric discrimination 指标可能不稳定。

初期优先分析：

~~~text
item pass pattern
strong-vs-weak model separation
score spread
unexpected inversion
~~~

如果所有模型都正确，可能是 ceiling item。如果所有模型都失败，可能是：

- genuinely very hard；
- broken；
- underspecified；
- out-of-scope。

必须结合 Item QA、Ground Truth、Source Provenance 和模型响应进一步判断，不能把所有低通过率题都当作高质量难题。

## 39. Ceiling / Floor Analysis

Pilot Report 需要统计：

~~~text
all / almost all models correct
all / almost all models incorrect
~~~

但不能自动删除。需要分类：

~~~text
useful easy anchor
useful hard anchor
too trivial
too obscure
broken
ambiguous
ground_truth issue
~~~

分类结果应进入 Item Calibration Outcome 和 Pilot Expansion Recommendation。

## 40. Item Calibration Outcome

每个 Item 在 Pilot 后至少进入：

~~~text
keep
revise_and_retest
reject
~~~

必要时可以增加：

~~~text
keep_as_anchor
~~~

作为 Diagnostic Label。

如果修改以下任一内容：

- Question；
- Ground Truth；
- Source Provenance；
- 重要视觉信息；

应遵循 Data Specification，产生新的 item_revision，并重新执行适用的 Verification / QA。

## 41. Broken Item Taxonomy

Pilot QA / Issue 分类至少包括：

~~~text
wrong_ground_truth
ambiguous_question
insufficient_information
invalid_formula
invalid_parameter
unit_error
source_mismatch
broken_asset
visual_not_required
duplicate
answer_parser_issue
evaluator_issue
taxonomy_mismatch
difficulty_mismatch
~~~

该 Taxonomy 只用于 Pilot QA / Issue 分类，不是 Benchmark Capability Taxonomy，也不改变 D01–D12、K1–K8、C1–C8 或 M1–M11 的定义。

## 42. Parser / Evaluator Diagnostics

Pilot 需要单独统计：

~~~text
invalid_format rate
ambiguous_parse rate
LLM Judge usage rate
Judge uncertain rate
unit parse failure
structured answer evaluator failure
~~~

目的在于判断问题来自 Model Capability 还是 Evaluation Infrastructure。

如果大量强模型因 Parser 问题丢分，说明 Benchmark Evaluator 可能存在系统性缺陷，应进入 QA Issue、Evaluator Revision 或复核流程，而不能直接作为模型能力结论。

## 43. Calculation Calibration Metrics

T2 除模型分数外至少观察：

~~~text
solver reproducibility
unit conversion correctness
tolerance behavior
parameter validity
template concentration
numeric parser failure
~~~

参数化题必须可以回溯：

~~~text
template_id
parameter_set_id
~~~

并能连接到 Formula Evidence、Ground Truth 和 Calculation Verification Record。

## 44. Multimodal Calibration Metrics

T3 至少观察：

~~~text
full-condition accuracy
text-only ablation accuracy
visual dependency gap
asset failure rate
visual parse / input failure
capability-specific performance
~~~

visual dependency gap 可以作为重要诊断量，但 v0.1 不设统一淘汰阈值。Pilot 结果用于决定未来是否需要固定阈值、额外人工审查或重新构题。

## 45. Prompt Robustness Diagnostic

可以在一个小型 Diagnostic Subset 上测试：

- minor formatting changes；
- option label changes；
- equivalent instruction wording。

目的在于检查 Benchmark 是否过度依赖 Prompt Format。

不要对全部 500 Item 强制运行大量 Prompt Variant。具体 Diagnostic Subset size 为 TBD，该结果不进入 Official Score。

## 46. Option Position Diagnostic

对于部分选择题可以测试：

~~~text
option permutation
~~~

用于观察 Position Bias。

Pilot Official Snapshot 的 Option Order 固定。Permutation 只作为 Diagnostic Experiment，不能覆盖或改变 Official Snapshot 中的选项顺序，也不进入默认 Official Score。

## 47. Cross-track Comparison

不要只看 Overall。Pilot 重点观察：

~~~text
T1 vs T2 vs T3
~~~

是否存在：

- 过度失衡；
- 某 Track 全部过简单；
- 某 Track 全部过难；
- 某 Track 评分不稳定。

40 / 30 / 30 Sampling 和三个 Track 等权 Overall 是两个不同概念，继续遵守 Evaluation Specification。

## 48. Domain × Track Coverage Analysis

Pilot Report 必须生成 Domain × Track Matrix，至少显示：

~~~text
item_count
mean_score
model spread
~~~

某些 Taxonomy 定义为 Optional / Not Typical 的 Cell 不应被强行填题。缺失 Cell 应说明是 Not Applicable、Source 不足、Ground Truth 不可靠、构题失败还是采样决策。

## 49. Source × Quality Analysis

分析某类来源是否系统性更容易产生：

- ambiguous items；
- parse failures；
- poor multimodal crops；
- unverifiable Ground Truth；
- duplicate questions。

来源类型示例：

~~~text
standard
manual
textbook
paper
~~~

不同 Source Type 的差异用于指导 Phase 7 Source Selection 和 Construction Strategy，不在 Pilot Design v0.1 中预设哪个类型一定更优。

## 50. Construction Method Analysis

比较以下方法：

~~~text
human_authored
llm_assisted
template_generated
parameterized_generated
transformed_from_source
~~~

比较维度包括：

- rejection rate；
- revision rate；
- ambiguity；
- Ground Truth error；
- model discrimination。

目的在于确定后续 V1 哪类构题方式值得扩大，而不是预先假设某种方法一定优于其他方法。

## 51. Human Review Metrics

记录：

~~~text
reviewed_item_count
expert_escalation_count
review_disagreement_count
revision_after_review
rejection_after_review
~~~

如果存在多个 Reviewer，可以记录一致性。但 Pilot v0.1 不要求引入复杂 Inter-rater Reliability 指标，是否需要以及采用哪种方法保持 TBD。

## 52. Pilot Execution Stages

Pilot 内部正式设计为：

~~~text
Stage P0
Pilot Planning Freeze

Stage P1
Pilot Source Sampling

Stage P2
Candidate Construction

Stage P3
Automatic Verification

Stage P4
Human QA / Expert Escalation

Stage P5
Pilot Snapshot Assembly

Stage P6
Evaluation Runner Conformance

Stage P7
Model Panel Evaluation

Stage P8
Calibration Analysis

Stage P9
Pilot Review / Expansion Decision
~~~

这些是 Pilot 内部 Stage，不要与 Project Phase 0–8 混淆。

## 53. Pilot Entry Criteria

真正开始 Pilot Construction 前，至少需要：

~~~text
Taxonomy baseline available
Data Specification baseline available
Evaluation Specification baseline available
System Architecture baseline available

Corpus Inventory completed
Benchmark Source Corpus selected
Document Processing validated
Evidence / Asset Pipeline available
Candidate Construction Pipeline available
Verification Pipeline minimally available
~~~

因此，Pilot Design 虽然在 Phase 0 完成，但 Pilot 实际执行发生在后续 Phase 4–6。

## 54. Pilot Snapshot Entry Gate

组装约 500 Item 的 Pilot Snapshot 前，至少要求：

- Applicable Schema Validation completed；
- Source / Evidence refs valid；
- Ground Truth Verification completed；
- Calculation Verification completed for T2；
- Asset available for T3；
- Visual Dependency Check completed for T3；
- Exact Duplicate resolved；
- Critical Ambiguity resolved；
- Critical QA Issues resolved；
- Required Human QA completed。

不能为凑够 500 道题降低 Critical Quality Gate。

如果最终只有 470 个真正满足条件的 Item，应优先使用 470 个高质量 Pilot，而不是硬凑 500 个。

## 55. Evaluation Runner Conformance Gate

在运行完整 Model Panel 前，必须先用：

~~~text
Golden Evaluation Cases
~~~

验证：

- single choice；
- multiple choice；
- boolean；
- numeric；
- unit conversion；
- tolerance boundary；
- short answer；
- structured answer；
- invalid output；
- multimodal asset；
- runtime error。

Runner / Adapter Conformance 不通过，不能进行正式 Pilot Model Panel Evaluation。

具体 Runner 选择仍遵循 Evaluation Specification 和 System Architecture 的 Adapter-based 边界，不在 Pilot Design v0.1 选择 OpenCompass、VLMEvalKit 或 Custom Runner 的最终组合。

## 56. Pilot Quality Review

Model Panel 前先做 Pilot Quality Review，回答：

~~~text
题目本身是否已经足够可信？
~~~

而不是先回答模型表现怎么样。

这是 Project Plan Gate 5 对应的重要输入。Quality Review 应检查 Admission Criteria、Critical Defect、Ground Truth、Source Provenance、Visual Dependency 和人工 Review 是否满足要求。

## 57. Pilot Validation Review

完成 Model Panel 与 Calibration 后做 Pilot Validation Review，回答：

~~~text
这套 Benchmark 是否真正有测量价值？
~~~

至少检查：

- Coverage；
- Ground Truth Reliability；
- Difficulty Spread；
- Model Separation；
- Scoring Stability；
- Visual Dependency；
- Source Concentration；
- Duplicate / Contamination；
- Evaluation Infrastructure；
- Construction Efficiency。

这是 Project Plan Gate 6 的重要输入。

## 58. Pilot Expansion Decision

Pilot 最终必须给出：

~~~text
GO
GO WITH REVISION
NO-GO
~~~

### 58.1 GO

方法和 Pipeline 基本成立，可以进入 V1 Expansion。

### 58.2 GO WITH REVISION

可以扩展，但必须先解决明确问题，例如：

- Multimodal quality；
- source imbalance；
- calculation templates；
- evaluator instability。

### 58.3 NO-GO

存在系统性问题，不适合直接扩大到 3k–5k。例如：

- Ground Truth error widespread；
- scoring unstable；
- weak visual dependency；
- excessive ambiguity；
- poor discrimination；
- serious contamination。

Decision 必须引用 Calibration Findings、Quality Findings、Failure Patterns 和未决问题，不得只根据 Item 数量决定。

## 59. Pilot Exit Criteria

Pilot Exit Criteria 不应只写“500 道题完成”。

### 59.1 Dataset Quality

- 无 unresolved critical defect；
- required provenance complete；
- mandatory verification complete；
- Exact Duplicate 已处理；
- T3 Visual Dependency 完成；
- T2 deterministic verification 满足要求。

### 59.2 Evaluation Quality

- Evaluation Runner Conformance passed；
- Model Panel Run 可解释；
- Parser / Evaluator 无系统性故障；
- Judge usage 和 uncertainty 可分析。

### 59.3 Benchmark Measurement

- Difficulty 具有一定梯度；
- 没有明显全体 ceiling / floor；
- 至少部分题具有明显 model separation；
- 三个 Track 均能够产生有意义结果。

### 59.4 Process

- Construction / QA / Review workflow 可重复；
- 成本和资源可估算；
- 主要失败模式已经识别。

具体数值阈值由 Pilot 后根据真实结果确定。

## 60. Expansion Recommendations

Pilot Final Report 必须产生对 Phase 7 的建议：

~~~text
recommended_track_ratio
recommended_domain_adjustment
recommended_capability_adjustment
difficulty_target
source_strategy
construction_method_strategy
human_review_strategy
multimodal_strategy
evaluation_strategy
~~~

这些建议才决定 V1 3k–5k 如何扩展。Pilot Design v0.1 不预先假装已经知道答案，也不把 40 / 30 / 30 写成不可调整的 V1 规则。

## 61. Resource Tracking

Pilot 应记录：

~~~text
PDF processing cost
LLM generation tokens / cost
verification cost
evaluation cost
GPU time
human review time
expert review time
storage growth
~~~

如果某项数据无法获得，允许记录 unavailable，但不能将 unavailable 误记为零。

目的在于为 V1 Expansion 估算真实成本和资源需求。

## 62. Pilot Resource Preconditions

Pilot Design 不填写未知硬件配置。实际执行前需要结合 System Architecture 已列出的：

- CPU；
- RAM；
- GPU；
- storage；
- Docker；
- API availability；
- LLM endpoints。

制定 Pilot Resource Plan。执行前还需确认 Candidate Source Corpus、Benchmark Source Corpus 和 Source Asset 的访问及使用边界。

## 63. Pilot Versioning

至少区分：

~~~text
Pilot Candidate Pool Version
Pilot Dataset Snapshot Version
Evaluation Run Version
Calibration Report Version
~~~

修改 Item 后必须：

~~~text
item_revision++
~~~

Pilot-v0.1 永远指向被冻结的 Item Revision。不要因为 Calibration 改题后覆盖 Pilot-v0.1，应创建新的 Snapshot。

历史 Evaluation Run 必须继续关联原有 Dataset Snapshot 和 Item Revision，不因后续 Calibration 自动漂移。

## 64. Pilot Deliverables

最终至少包括：

~~~text
Pilot Design v0.1

Pilot Source Manifest
Pilot Candidate Pool
Verification Records
QA Issue Registry
Pilot Dataset Snapshot
Pilot Dataset Manifest
Pilot Dataset Card

Evaluation Run Manifests
Item-level Evaluation Results
Calibration Analysis
Pilot Final Report
Expansion Recommendation
~~~

其中，当前 Phase 0 只交付：

~~~text
Pilot Design v0.1
~~~

其他 Artifact 在后续 Phase 实际生成。本次不创建真实 Source Manifest、Candidate Pool、Dataset、Evaluation Result 或 Pilot Report。

## 65. Pilot Report Structure

预先定义 Pilot Final Report 至少包括：

1. Executive Summary；
2. Pilot Dataset Profile；
3. Track / Domain / Capability Coverage；
4. Source Coverage；
5. Quality / Rejection Analysis；
6. Model Panel Results；
7. Difficulty Calibration；
8. Discrimination Analysis；
9. Multimodal Visual Dependency；
10. Calculation Validation；
11. Parser / Evaluator Diagnostics；
12. Cost / Resource Analysis；
13. Known Limitations；
14. Required Revisions；
15. Expansion Recommendation；
16. GO / GO WITH REVISION / NO-GO。

## 66. Open Questions

以下问题全部保持 TBD，不在 Pilot Design v0.1 中擅自填写数字答案：

1. Pilot 最终是否严格 500 Item？—— TBD
2. Candidate Pool 需要生成多少 Item？—— TBD
3. Domain Coverage 的最低数量要求？—— TBD
4. Capability Coverage 的最低数量要求？—— TBD
5. Easy / Medium / Hard 最终目标比例？—— TBD
6. 单一 Source / document-family 最大占比是否需要硬限制？—— TBD
7. Human QA Reviewer 资源？—— TBD
8. Domain Expert Review 资源？—— TBD
9. Expert Escalation 的具体触发规则？—— TBD
10. Pilot Anchor / Baseline Models 具体选择？—— TBD
11. Model Panel 数量最终是 5、10 或其他？—— TBD
12. Empirical Difficulty Threshold？—— TBD
13. Item Discrimination 最终采用哪些指标和阈值？—— TBD
14. Visual Dependency Gap 淘汰阈值？—— TBD
15. Prompt Robustness Diagnostic Subset 大小？—— TBD
16. Option Permutation Diagnostic 是否保留到 V1？—— TBD
17. Judge Uncertain 的最终 Adjudication 策略？—— TBD
18. Human Review 是否需要双人审核部分样本？—— TBD
19. Pilot Snapshot 是否允许少量 needs_review Item？—— 原则上不允许 Critical Issue，但具体非 Critical 状态 TBD
20. Pilot 最终 GO / NO-GO 数值门槛如何定义？—— TBD

## 67. Upstream Traceability

Pilot Design 不重复定义上位规范，而是使用以下文档提供的边界。

### 67.1 Project Charter

提供：

- three tracks；
- Pilot ≈500；
- V1 ≈3k–5k；
- Quality principles。

### 67.2 Project Plan

提供：

- Phase 5 Pilot Quality Review；
- Phase 6 Model Validation & Calibration；
- Gate 5 / Gate 6。

### 67.3 Benchmark Taxonomy

提供：

- Domain；
- Track；
- Capability；
- Task；
- Difficulty；
- Modality；
- Answer Type。

### 67.4 Data Specification

提供：

- Item Revision；
- Ground Truth；
- Verification；
- Dataset Membership；
- Dataset Snapshot。

### 67.5 Evaluation Specification

提供：

- Official Profile；
- Item Scoring；
- Track / Overall；
- Run Completeness；
- Result Contract。

### 67.6 System Architecture

提供：

- Pipeline components；
- Verification Pipeline；
- Dataset Assembly；
- Evaluation architecture；
- Job / Artifact versioning。

Pilot Design 只定义如何使用这些规范进行 Pilot Validation，不修改其语义。

## 68. 文档状态

~~~text
Project: Mechanical Industry General Benchmark
Document: Pilot Design
Version: 0.1
Status: Draft - Pending Review
Phase: Phase 0 - Benchmark Design
Current Task: Pilot Design v0.1
~~~

Pilot Design v0.1 需要先经过人工评审。评审通过前，不应把当前文档解释为 Pilot 已经执行，也不应把 Pilot Design 中的目标、示例或 Planning Guidance 当作实验结果或最终 V1 决策。

## 69. 本次不要更新 Progress

本次完成 docs/07_pilot_design.md 后，不修改 docs/06_progress.md。当前 Progress 应继续保持：

~~~text
Current Phase: Phase 0 - Benchmark Design
Current Milestone: Benchmark Design v0.1
Current Task: Pilot Design v0.1
~~~

原因是 Pilot Design v0.1 还需要人工评审。只有在后续评审完成后，才根据评审结论更新进度。

## 70. 本次不要实现

本次不要：

- 开始 Phase 1；
- 扫描 70k PDF；
- 实现 Corpus Inventory；
- 创建真实 Pilot Item；
- 调用任何模型；
- 构建 Evaluation Runner；
- 修改上位设计；
- 选择具体 Anchor Models。

也不要创建真实 Pilot Dataset、Candidate Pool、Evaluation Result、数据库或新的 Pipeline 代码。

## 71. 最终检查

文档完成后执行：

~~~text
git diff --check
~~~

并检查：

- Pilot Objectives 已定义；
- Pilot Sampling Strategy 已定义；
- Track / Domain / Capability / Difficulty Coverage 已定义；
- Knowledge / Calculation / Multimodal Pilot Strategy 已定义；
- Verification / Human Review Strategy 已定义；
- Model Panel Strategy 已定义；
- Calibration Metrics 已定义；
- Visual Dependency Strategy 已定义；
- Pilot Gates / Exit Criteria 已定义；
- Expansion Decision 已定义；
- Open Questions 保持 TBD；
- 没有进入 Phase 1；
- 没有处理 70k PDF；
- 没有生成真实 Benchmark Item；
- 没有调用模型；
- 没有实现 Evaluation Runner。

## 72. 变更记录

| 版本 | 日期 | 变更说明 |
| --- | --- | --- |
| v0.1 | 2026-09-11 | 创建 Pilot Design v0.1，定义 Pilot Validation Experiment、采样、Track 覆盖、Verification / Human Review、Model Panel、Calibration、Pilot Gate、退出标准和 Open Questions；保持 Draft - Pending Review |
