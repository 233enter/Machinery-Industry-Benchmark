# Mechanical Industry General Benchmark Evaluation Specification v0.1

## 文档信息

| 项目 | 内容 |
| --- | --- |
| Project | Mechanical Industry General Benchmark |
| Document | Evaluation Specification |
| Version | 0.1 |
| Status | Draft - Pending Review |
| Phase | Phase 0 - Benchmark Design |
| Current Task | Evaluation Specification v0.1 |

## 1. 文档定位

本文件定义 Mechanical Industry General Benchmark 的评测语义、评分规则、运行规范和结果聚合方式。

它回答的问题是：

> 给定一个冻结的 Benchmark Dataset 和一个待测模型，如何以稳定、可复现、公平、可审计的方式产生模型输出、解析答案、计算 Item Score，并形成 Track、Domain、Capability 和 Overall Score？

本文件是 framework-independent 的 Evaluation Semantics 规范，不绑定具体 Runner、模型 API、商业服务或硬件环境：

~~~text
evaluation semantics
        ↓
framework-independent

OpenCompass / VLMEvalKit / custom runner
        ↓
implementation adapters
~~~

不同 Runner 可以有不同的工程实现，但不允许改变本文件定义的 Ground Truth 解释、Answer Parsing、Item Scoring 和 Score Aggregation 语义。

本文件不实现：

- Evaluation Runner；
- OpenCompass、VLMEvalKit 或其他框架配置；
- 模型调用或 API 集成；
- Pilot Benchmark；
- PDF Processing、Dataset Generation 或 Schema Code。

## 2. 上位约束与评测边界

本文件依赖以下已完成的上位设计：

- Project Charter v0.1；
- Project Plan v0.1；
- Benchmark Taxonomy v0.1；
- Data Specification v0.1。

其中 Data Specification v0.1 定义 Canonical Benchmark Item、item_id、item_revision、dataset_version、Answer Type 和 Canonical Ground Truth 的逻辑结构。本文件只规定这些字段如何参与评测，不重新定义它们。

Evaluation 的基本边界是：

1. 评测必须绑定一个明确的 Dataset Snapshot；
2. 评测必须绑定一个明确的 Evaluation Profile；
3. Ground Truth 必须来自 Data Specification 中的 Canonical Ground Truth；
4. Evaluation 不得根据模型输出、模型名称或当前得分重新解释 Ground Truth；
5. Raw Response、Parsed Answer 和 Score 必须分别保存并可追溯；
6. 运行错误与模型内容错误必须分离；
7. 评分规则必须能够被不同 Runner 一致实现。

## 3. 标准 Evaluation Pipeline

标准生命周期为：

~~~text
Frozen Dataset Snapshot
        ↓
Evaluation Profile
        ↓
Model Adapter
        ↓
Prompt / Input Construction
        ↓
Model Inference
        ↓
Raw Response
        ↓
Answer Parser
        ↓
Normalized Answer
        ↓
Item Evaluator
        ↓
Item Score
        ↓
Aggregation
        ↓
Evaluation Report
~~~

各阶段职责如下：

| 阶段 | 主要职责 | 不应承担的职责 |
| --- | --- | --- |
| Frozen Dataset Snapshot | 固定 dataset_version 及具体 Item Revision 集合 | 不在运行时替换历史 Item |
| Evaluation Profile | 固定评测模式、Prompt Policy 和运行约束 | 不根据单个模型结果临时改变规则 |
| Model Adapter | 将 Canonical Item 转换为模型可接受的输入并收集输出 | 不修改 Ground Truth 或为模型修正答案 |
| Prompt / Input Construction | 组织 Question、Instructions、Options 和允许的 Visual Assets | 不注入隐藏 Metadata、Evidence 或答案 |
| Model Inference | 调用待测模型并保留原始返回 | 不把错误答案重试到正确为止 |
| Answer Parser | 提取并规范化模型答案 | 不猜测模型未给出的答案 |
| Item Evaluator | 按 Answer Type 和版本化规则计算 Item Score | 不使用另一个未记录的评分标准 |
| Aggregation | 计算 Track、Slice 和 Overall 指标 | 不隐藏 item_count 或运行失败情况 |
| Evaluation Report | 输出分数、覆盖范围、版本和异常信息 | 不把不可比的结果伪装成官方成绩 |

## 4. Evaluation Run Entity

Evaluation Run 是一次具有明确数据、模型、规则和运行环境的逻辑评测实体。至少需要能够记录：

~~~text
evaluation_run:
  run_id
  dataset_version
  evaluation_spec_version
  evaluation_profile_id
  evaluation_profile_version

  model
  model_adapter
  prompt_policy
  generation_config
  runtime_environment

  started_at
  completed_at
  run_status
~~~

### 4.1 Model Metadata

model 至少能够记录：

~~~text
model:
  model_id
  model_name
  model_version
  provider
  model_type
  supports_vision
~~~

这些字段用于追踪和报告，不应把某个商业 API 的名称、参数格式或账户体系写死为 Canonical Schema。

model_type 可以区分文本 LLM、多模态 LLM 或其他待评测类型。supports_vision 必须与实际能够接受 Benchmark 指定视觉输入的能力相一致。

### 4.2 Model Adapter

Model Adapter 负责：

- 将 Canonical Question 转换为目标模型输入；
- 根据模型能力传递允许的 Text、Table 或 Visual Asset；
- 记录 Adapter ID 和 Version；
- 保留模型返回的 Raw Response；
- 不改变题目语义和 Ground Truth。

### 4.3 Runtime Environment

runtime_environment 只定义需要追踪的概念，例如：

~~~text
runner_version
adapter_version
dependency_snapshot
hardware_reference
endpoint_reference
~~~

具体存储、硬件、Endpoint 和依赖锁定方式留给 System Architecture。敏感凭证、API Key、Token 和 Secret 不得写入 Evaluation Run。

### 4.4 Run Status

Run Status 用于区分计划、运行完成、部分完成、无效和失败等运行结果。其最终 Controlled Vocabulary、Run Invalid / Partial 的正式判定规则仍为 TBD，不得用单一的模型平均分替代运行状态。

## 5. Dataset Snapshot 与 Revision 冻结

Evaluation Run 必须绑定：

~~~text
dataset_version
~~~

并最终解析到该 Snapshot 冻结的：

~~~text
item_id
+ item_revision
~~~

一个 Dataset Version 必须固定具体 Item Revision 集合。即使同一个 item_id 后续产生新 Revision，历史 Run 仍必须解析到原 Snapshot 中的 Revision。

Benchmark Score 必须能够回答：

> 这个分数到底是在 Benchmark 哪个版本、哪些 Item Revision 上得到的？

Evaluation Run 至少应保存或能够重建本次运行的 Item Manifest。历史 Run 不允许自动漂移到 Item 最新 Revision；发现题目问题时，应按照 Data Specification 的 Item Revision 和 Dataset Version 原则处理。

## 6. Official Evaluation Profile

### 6.1 定义

Official Evaluation Profile 用于产生正式可比较的 Benchmark 结果。它必须是可命名、可版本化、可复现的 Profile，而不是一组未记录的临时 Prompt 或参数。

### 6.2 V1 默认原则

V1 Official Profile 的初步原则为：

~~~text
single-turn
zero-shot
no external tools
no web search
no RAG
no code interpreter
no calculator tool
no retrieval augmentation
~~~

该 Profile 用于测试模型在 Benchmark 指定输入条件下的自身能力。工具增强、RAG、Web-enabled Model 或 Agent 任务如果未来评测，必须建立独立 Evaluation Profile，不得与标准模型成绩直接混合。

### 6.3 Profile 版本边界

如果改变 Prompt Policy、Generation Policy、Answer Parser、Evaluator、输入构造方式或评分聚合方式，应产生新的 Evaluation Profile Version 或 Evaluation Specification Version，并在结果中明确记录。

## 7. Prompt Policy

Official Profile 应使用最小、中性的 System / Instruction Template。

除非这些内容本身就是题目公开输入，否则不得向模型提供：

- Ground Truth；
- Source Evidence；
- Verification Notes；
- Hidden Metadata；
- Domain Label；
- Difficulty Label；
- Capability Label。

模型输入只应来自 Canonical Item 中允许公开给模型的：

- Question Stem；
- Instructions；
- Options；
- 允许的 Visual Assets。

默认使用 zero-shot。Few-shot、CoT prompting、special prompting 或针对某个模型的优化 Prompt，如未来研究，必须作为独立 Experiment Profile，不修改 Official Score 的语义。

## 8. Chain-of-Thought Policy

Benchmark 不要求模型输出完整 Chain-of-Thought，也不把隐藏推理过程作为评分输入。

对于 Calculation Item，可以要求模型输出：

- 最终答案；
- 在必要情况下的有限步骤、公式或结果。

Official Scoring 优先依据 Canonical Answer。只要最终答案满足题目和 Answer Type 的要求，不得因为模型没有展示完整内部推理链而判错。

如果题目明确要求有限的可审计步骤，Parser 可以检查这些公开字段是否存在；这不等同于要求模型披露完整内部推理过程。

## 9. Generation / Decoding Policy

Official Evaluation 优先使用模型所支持的最确定性配置：

~~~text
temperature = 0
~~~

如果模型 API 不支持完全确定性，应记录实际 Generation Config，而不是声称结果是 deterministic。至少记录：

~~~text
temperature
top_p
max_output_tokens
seed（如支持）
reasoning / thinking mode（如可配置）
其他影响生成结果的重要参数
~~~

不要为了获得正确答案而对同一道题反复采样后选择最佳结果。

允许在固定策略下对 Transport / API / Infrastructure Failure Retry。正常生成了错误答案、冲突答案或 Invalid Format 时，不允许为了提高成绩而重试。具体最大 Infrastructure Retry 次数和 Run Invalid 处理仍为 TBD。

## 10. Raw Response Preservation

每个 Item Result 必须尽可能保留：

~~~text
raw_response
parsed_answer
parse_status
~~~

三个对象必须保持语义分离：

~~~text
Raw Response
!=
Parsed Answer
!=
Score
~~~

任何 Parser 都不得修改 Raw Response。若 Provider 返回结构化响应，应同时保存足以审计模型原始输出的内容和必要的 Transport Metadata；具体存储格式由 System Architecture 决定。

## 11. Parse Status

Parse Status 至少包括：

~~~text
parsed
invalid_format
no_answer
ambiguous_parse
runtime_error
~~~

runtime_error 必须能够进一步区分模型调用失败、传输失败、服务错误和正常模型输出错误。正常输出无法解析时，不得伪装成 Runtime Error。

当 Parser 无法可靠提取答案时，Official Item Score 默认不得通过猜测性解释获得正确分。该结果应保留 Parse Status 和 Error Category，供 Run Policy 与报告使用。

## 12. Model-agnostic Answer Parser

Answer Parser 只做格式提取和规范化，必须保持 model-agnostic / ground-truth-blind。

Parser 不得：

- “替模型修答案”；
- 根据 Ground Truth 选择模型同时给出的多个候选答案中的一个；
- 把不确定表述强行解释为唯一答案；
- 因为某个模型常用某种格式而放宽本题的解析规则。

例如模型输出：

~~~text
A，也可能是B
~~~

Parser 不能因为 Ground Truth 是 A 就只取 A，应标记为 ambiguous_parse 或其他适用的 Invalid 状态。

## 13. Single Choice Scoring

Canonical Ground Truth 为：

~~~text
correct_option_id
~~~

Model Adapter 可以向模型展示 A / B / C / D 等 Display Label，但 Parser 最终必须映射回稳定的 option_id。Display Label 不承担 Canonical Identity。

Official Item Score：

~~~text
correct → 1
incorrect → 0
invalid / ambiguous → 0
~~~

如果模型输出多个互相冲突的最终选择，不得任选一个最有利答案。若题目是 single_choice，Parser 只有在能够确定唯一 Option ID 时才能产生 Parsed Answer。

## 14. Multiple Choice Scoring

Canonical Ground Truth 为：

~~~text
correct_option_ids[]
~~~

Official Primary Metric 使用 Exact Set Match：

~~~text
predicted_set == ground_truth_set
→ 1

otherwise
→ 0
~~~

选项顺序不影响集合比较，但重复、冲突或无法归一化的选项应按 Invalid / Ambiguous Output 处理。

可以另外计算以下 Diagnostic Metrics：

- precision；
- recall；
- F1。

Partial F1 不作为默认 Official Item Score，避免通过选择所有选项获得不合理的部分分。

## 15. True / False Scoring

Parser 应将语言表达标准化为 Canonical Boolean：

~~~text
true
false
~~~

可以处理的表达包括：

- 正确 / 错误；
- True / False；
- 是 / 否。

Official Score 使用 Exact Match。无法确认唯一布尔值、同时出现互相冲突表达或无法解析时，Item Score 为 0，并保留相应 Parse Status。

## 16. Numeric Scoring

Numeric Scoring 使用 Data Specification 中的 Canonical Ground Truth 字段：

~~~text
value
unit
dimensionless
absolute_tolerance
relative_tolerance
rounding_rule
accepted_unit_conversions
~~~

Ground Truth 是唯一评分真值。Numeric Scoring Pipeline 为：

~~~text
Raw Response
→ Numeric Extraction
→ Unit Extraction
→ Unit Normalization
→ Numeric Comparison
→ Score
~~~

如果 Ground Truth 有物理单位，模型答案必须与该 Canonical Quantity Dimension 兼容。若题目明确要求“答案以 N·m 给出”，纯数值输出可以解释为指定的 Canonical Unit；否则必须按照 Unit Policy 判断缺少单位是否构成无法确认的答案。

## 17. Numeric Unit Policy

Unit Policy 必须明确区分以下两个概念：

~~~text
explicit_output_unit_in_question
unit_required_from_model
~~~

其语义为：

| 条件 | 处理原则 |
| --- | --- |
| explicit_output_unit_in_question = true | 题目已指定 Canonical Unit；模型输出纯数值时可解释为该单位 |
| unit_required_from_model = true 且模型未提供单位 | 默认不能直接假定单位正确；按 Invalid / Unit Missing 处理 |
| 提供可转换的兼容单位 | 先转换至 Ground Truth Canonical Unit，再比较 |
| Quantity Dimension 不兼容 | Official Score = 0 |
| 单位无法可靠提取或存在冲突 | 不猜测，进入 Invalid / Ambiguous 状态 |

若两个字段都未明确，具体默认策略需要在后续 Pilot / Quality Review 中确认，不得由某个 Runner 私自决定。

## 18. Numeric Tolerance Rule

令：

~~~text
y = ground truth
x = normalized model answer

absolute_error = |x - y|
~~~

当 absolute_tolerance 和 relative_tolerance 都存在时：

~~~text
allowed_error =
max(
  absolute_tolerance,
  relative_tolerance * |y|
)
~~~

通过条件为：

~~~text
absolute_error <= allowed_error
~~~

如果只定义其中一个 tolerance，使用已定义项。如果 Ground Truth 接近 0，relative tolerance 不能单独作为可靠判断，应使用 absolute tolerance。

如果两个 tolerance 均为空，默认使用单位归一化后的 exact numeric equality，除非未来版本的 Evaluation Policy 明确规定其他规则。

评分器只能读取 Ground Truth 中的评分容差。不得从 Calculation Object 读取另一套评分 tolerance。

## 19. Unit Normalization

模型答案应先转换至 Ground Truth Canonical Unit，再比较数值。例如：

~~~text
0.955 kN·m
=
955 N·m
~~~

只有 Data Specification 所允许的兼容单位转换才可以执行。当前 Evaluation Specification 定义“兼容单位可以转换、不兼容 Quantity Dimension 得分为 0”的语义，但不实现 Unit Registry。

Unit Registry、Quantity Dimension Registry 和完整单位转换表仍由 Data Specification Open Question 与后续 System Architecture 解决。

## 20. Rounding Policy

rounding_rule 只在题目或 Canonical Ground Truth 明确要求特定精度时使用。

处理顺序应为：

1. 提取数值和单位；
2. 执行合法单位转换；
3. 按题目和 Ground Truth 的 Rounding Policy 解释表示精度；
4. 使用 Tolerance Rule 判断。

不得先把错误答案过度四舍五入后变成正确答案。内部计算应尽可能保留原始数值，避免在 Item 聚合前过早舍入。

## 21. Short Answer Scoring

Short Answer 采用 Cascaded Evaluator，默认顺序为：

~~~text
Normalization
↓
Canonical Exact Match
↓
Accepted Alias Match
↓
Rule / Regex Match（如配置）
↓
Optional Semantic Judge
~~~

Normalization 可以使用 Data Specification 中的：

- case_sensitive；
- trim_whitespace；
- unicode_normalization；
- punctuation_normalization。

Official Evaluator 优先使用 deterministic methods。不能默认使用模糊字符串相似度把语义不同的答案判为正确。只有在规则无法可靠处理的有限 Short Answer 场景，才可以按版本化 Policy 使用 LLM Judge。

## 22. Structured Answer Scoring

Structured Answer 按 Field 评分。Canonical Ground Truth 为：

~~~text
expected_fields
required_fields
field_ground_truth
~~~

默认规则：

~~~text
每个 Required Field 单独得到 field_score ∈ [0,1]

Item Score = mean(required_field_scores)
~~~

Optional Field 不计入默认 Official Score，除非 Evaluation Policy 明确指定。后续 Evaluator Config 可以支持 weighted_mean 或 all_or_nothing，但必须版本化，并且不能由单个 Runner 临时决定。

输出额外的无害字段不得自动判错。如果额外内容与 Required Field 明确矛盾，应标记为 conflict，并按照版本化规则处理。

## 23. LLM Judge Policy

LLM Judge 只能用于确定性 Evaluator 无法可靠处理的 Short Answer 或有限 Structured Answer。

LLM Judge 不得作为默认 Evaluator 处理：

- single_choice；
- multiple_choice；
- true_false；
- numeric。

使用 LLM Judge 时必须记录：

~~~text
judge_model
judge_model_version
judge_prompt_version
rubric_version
~~~

并保存 Judge Result。Judge 不应看到：

- 被测模型名称；
- 被测模型厂商；
- Leaderboard 排名；
- 其他模型答案。

Judge 输入只包含完成判断所需的内容，例如 Question、Canonical Ground Truth / Rubric 和 Model Answer。

## 24. LLM Judge Output 与不确定性

Judge 应输出结构化结果，例如：

~~~text
decision:
  correct
  incorrect
  uncertain

score
reason_code
~~~

不要依赖 Judge 的长篇自然语言解释作为机器评分依据。

如果 Judge：

- 返回 invalid；
- 返回 uncertain；
- 多次 Judge 结果严重不一致；

则不得静默判为正确，应进入 needs_review。具体 Judge Retry、多 Judge 聚合和 Human Adjudication 策略保留 TBD。

## 25. Rule-first / Judge-last

Evaluation Specification 明确采用以下优先顺序：

~~~text
Deterministic Evaluator
        ↓
Rule-based Evaluator
        ↓
Structured Evaluator
        ↓
LLM Judge
~~~

越能确定性评估的题型，越不应使用 JudgeLLM。该原则用于提高：

- reproducibility；
- cost control；
- evaluation stability；
- auditability。

## 26. Multimodal Evaluation

T3 Item 使用 Data Specification 允许的 Visual Asset。Model Adapter 必须保证发送给模型的是：

- 正确 Asset；
- 正确顺序；
- 正确题目；
- 正确的图片与题目对应关系。

不得漏图、换图或改变图片对应关系。

对于 multi-image Item，输入顺序必须固定并记录。primary_modality = multi_image 与具体 Visual Type 的语义应保持一致。

Official Scoring 仍根据 Answer Type 进行：

- Drawing Dimension Reading + numeric：使用 Numeric Evaluator；
- Mechanical Drawing + single choice：使用 Single Choice Evaluator；
- Table / Chart + structured answer：使用 Structured Answer Evaluator。

Multimodal 不是独立的 Ground Truth 类型。T3 是 Primary Evaluation Bucket，不是新的答案评分方法。

## 27. Visual Dependency Check 与 Model Score 分离

visual_dependency_check 是 Dataset Quality Check，不能成为被测模型的独立 Score。

例如 text-only ablation 可以用于判断题目是否真正依赖图像，但这属于 Benchmark Item Quality Validation，而不是“模型多模态得分”。

必须保持：

~~~text
Visual Dependency Quality Check
!=
Model Score
~~~

## 28. Unsupported Modality

Text-only Model 不支持 T3 时，不应把 T3 全部自动记为 0。结果应报告：

~~~text
T1 Score
T2 Score
T3 = Not Evaluated / Unsupported
Overall = N/A
~~~

只有真正支持并接受 Benchmark 指定视觉输入的模型，才有资格报告完整 MIGB Overall Score。文本模型和多模态模型可以比较 T1 / T2，但不能伪造完整 Overall 排名。

可以额外报告：

~~~text
Text Capability Average = (T1 + T2) / 2
~~~

该指标只能作为 Diagnostic，不能冒充 MIGB Overall。

## 29. Item Score

所有 Official Item Score 标准化到：

~~~text
0.0 – 1.0
~~~

Binary Items 使用 0 / 1。Structured Answer 等允许 Partial Credit 的题型可以使用区间值，但 Partial Credit 必须由版本化 Evaluator 产生。

Evaluation Result 必须保存：

~~~text
item_score
is_fully_correct（如适用）
~~~

item_score 描述该 Item 在指定 Evaluator Version 下的结果，不应写回 Canonical Benchmark Item。

## 30. Primary Track Score

T1、T2、T3 每个 Track 的默认分数为 Item-level Mean：

~~~text
Track Score = mean(Item Score within Track)
~~~

报告时可以乘以 100 展示为百分制，例如：

~~~text
T1 = 78.4
T2 = 65.2
T3 = 54.8
~~~

必须同时报告：

~~~text
item_count
~~~

不允许只报告分数而隐藏样本量、Unsupported Item 数量或有效评测覆盖范围。

## 31. Overall Score

Mechanical Industry General Benchmark 是 General Benchmark。因此 Evaluation Specification v0.1 的 Baseline Scoring Policy 正式采用三个 Primary Track 的等权 Macro Average：

~~~text
Overall = (T1 + T2 + T3) / 3
~~~

这与 Sampling Target 40% / 30% / 30% 是两件事：

- Sampling Target 决定每个 Track 计划抽取多少题；
- Overall Scoring Weight 决定每个一级能力对总分的贡献。

使用等权 Track Macro Average，可以避免 Knowledge 因题目数量较多而自动获得更高总分权重。

Pilot Phase 6 可以根据实证结果重新评估该策略，但任何修改必须产生新的 Evaluation Specification / Benchmark Version，不能静默调整历史 Official Score。

## 32. Overall Score Eligibility

只有三个 Track 都成功完成官方评测时，才报告：

~~~text
MIGB Overall Score
~~~

如果 T3 Unsupported，则 Overall = N/A。不能把 (T1 + T2) / 2 仍命名为 MIGB Overall。

如果某个 Track 因 Run Invalid、Infrastructure Failure 或 Coverage 不足而无法形成可解释的官方分数，应报告不完整状态和原因，而不是补算一个看似完整的 Overall。

## 33. Slice Metrics

除了 Overall 和 Track Score，至少支持以下 Slice：

~~~text
Domain
Capability
Task
Difficulty
Answer Type
Modality / Visual Type
~~~

所有 Slice 必须同时报告：

~~~text
score
item_count
~~~

Slice 主要用于：

- 错误分析；
- 能力画像；
- Benchmark QA；
- 模型版本比较。

不要求每个 Slice 都进入 Leaderboard 首页。

## 34. Macro / Micro Boundary

Official Overall 使用 Track Macro Average。Official Track Score 默认使用 Item-level Mean。

同时允许报告 Domain Macro 和 Capability Macro 作为 Diagnostic，但 v0.1 不同时定义过多 competing official scores。

官方主结果保持：

~~~text
Overall
T1
T2
T3
~~~

其余 Domain、Capability、Task、Difficulty、Answer Type 和 Modality / Visual Type 结果属于 Slice Metrics。

## 35. Confidence / Statistical Reporting

Evaluation Report 建议支持 95% confidence interval。候选方法包括：

~~~text
bootstrap over items
~~~

在 v0.1 中，CI 为 Recommended / TBD：

- 最终 CI 算法留待 Pilot Phase 确认；
- bootstrap 次数和抽样细节留待 Pilot Phase 确认；
- 缺少 CI 不视为 Item Scoring 失败；
- Report 必须说明是否提供 CI 以及其计算版本。

## 36. Invalid Output Policy

以下情况默认 Item Score = 0：

- 无法解析答案；
- 无最终答案；
- 输出多个互相冲突答案；
- 拒答；
- 答案明显不符合题目要求且无法可靠归一化。

但 API / Infrastructure Error 不能自动当成模型知识错误。此类情况应记录：

~~~text
runtime_error
~~~

并根据 Run Policy 决定 Infrastructure Retry、使 Run Invalid 或保留 Partial Run。系统故障不得被静默计入模型能力错误。

## 37. Retry Policy

必须区分：

~~~text
Infrastructure Retry
和
Answer Retry
~~~

Infrastructure Failure 例如 Timeout、Network Failure、HTTP 5xx，可以在固定策略下 Retry。

正常生成了错误答案，不允许因为错误而 Retry。正常生成 Invalid Format，Official Policy 默认视为模型输出错误，不为了提高成绩反复重试。

具体最大 Infrastructure Retry 次数、退避方式、Partial Run 和 Run Invalid 的正式规则保持 TBD，并必须进入 Evaluation Run 记录。

## 38. Model Answer Extraction

Answer Parser 只负责格式提取和规范化，不负责“替模型修答案”。

处理原则包括：

- 只使用 Model Adapter 实际收到的题目和实际收到的 Model Response；
- 不查看 Ground Truth 来选择解析路径；
- 对冲突答案保留冲突，不选择最有利候选；
- 对没有最终答案的长篇解释标记 no_answer 或适用状态；
- 对无法确定的格式标记 ambiguous_parse 或 invalid_format。

Parser 的行为必须由 Parser Version 追踪，以便历史 Result 可以重现。

## 39. Evaluation Result Entity

Evaluation Result 是独立于 Canonical Benchmark Item 的逻辑实体。至少包括：

~~~text
evaluation_result:
  run_id
  item_id
  item_revision
  dataset_version

  raw_response
  parsed_answer
  parse_status

  evaluator_id
  evaluator_version

  item_score
  is_fully_correct

  error_category
  judge_result

  latency
  usage

  timestamp
~~~

latency 和 usage 属于运行信息，不进入能力 Score。不同 Provider 无法提供 token usage 时可以为空，但必须避免把“未知”误记为零。

Result 应能够关联：

- Evaluation Run；
- Item Revision；
- Dataset Version；
- Parser / Evaluator Version；
- Judge Version（如有）。

## 40. Evaluator Registry

不同 Answer Type / Task 可以引用版本化 Evaluator，例如：

~~~text
choice_exact_v1
multi_choice_exact_set_v1
boolean_exact_v1
numeric_tolerance_v1
short_answer_alias_v1
structured_fields_v1
llm_judge_xxx_v1
~~~

Evaluator ID / Version 必须进入 Evaluation Result。评分算法更新后，历史结果仍应能够解释；不得用新 Evaluator 静默重算旧结果并覆盖原始 Result。

## 41. Prompt / Adapter / Evaluator Versioning

Evaluation Run 至少能够追踪：

~~~text
evaluation_profile_version
model_adapter_version
prompt_template_version
parser_version
evaluator_version
judge_version（如有）
~~~

同一 Dataset 使用不同 Prompt Policy、Adapter 或 Evaluator 跑出的成绩，不得默认视为严格可比。比较时必须同时报告版本差异。

## 42. Option Shuffle

Official Evaluation 默认使用 Frozen Dataset Snapshot 内固定的 Option Order。不要每次 Run 随机 Shuffle。

如果未来研究 Position Bias 或 Option Permutation，应建立独立 Robustness Experiment。Position Robustness 不直接进入默认 Official Score，且实验结果必须与官方结果分开报告。

## 43. Robustness Evaluation

MMLU-Pro 类 Prompt Robustness、Option Permutation 和其他稳定性测试可以作为后续 Diagnostic。

当前 V1 Official Score 不强制加入 Robustness Score。可以预留：

~~~text
robustness_profile
~~~

但不得在 v0.1 扩展主评分体系，也不得把 Robustness Experiment 的分数混入 Official Overall。

## 44. Language Policy

Item 的 Question Language 来自 Data Specification。模型应接受原始 Benchmark Language。

Official Run 不自动翻译题目。翻译版 Benchmark 必须作为独立 Dataset Version / Language Variant 管理，并记录对应的 Language Policy。

## 45. Safety / Refusal Boundary

Benchmark 原则上不应包含需要模型基于安全政策拒绝回答的危险操作题作为普通机械能力题。

如果某题触发模型政策拒答，需要区分：

- Benchmark Item 本身是否设计不当；
- 模型是否表现出能力问题；
- 该拒答是否属于题目期望的行为。

此类问题在 Pilot 时应进入 QA Review，不应简单用大量危险操作内容测试机械知识，也不应把所有 Refusal 机械地解释为相同的模型能力错误。

## 46. Evaluation Reproducibility

正式 Report 至少要能够追溯：

~~~text
Dataset Version
Item Revisions
Evaluation Specification Version
Evaluation Profile
Model / Version
Model Adapter Version
Prompt Template Version
Generation Config
Parser Version
Evaluator Version
Judge Version（如有）
Runtime Environment
~~~

目标是使第三方或未来项目成员能够解释该分数如何得到，并能够在允许的环境下重新运行同一评测语义。

复现不要求所有 Provider 提供完全相同的底层服务实现，但必须记录实际参数、输入顺序、版本和异常处理。

## 47. Evaluation Framework Boundary

当前只定义 framework-independent semantics。候选实现未来可能包括：

~~~text
Text / Calculation Runner
Multimodal Runner
Unified Result Layer
~~~

本文件不决定 OpenCompass、VLMEvalKit 或自研 Runner 谁是最终方案。System Architecture 可以决定由谁负责执行；Evaluation Specification 决定什么才算“评对了”。

任何框架接入都必须遵守本文件的：

- Dataset Snapshot 绑定；
- Prompt Policy；
- Raw Response Preservation；
- Answer Parser；
- Item Evaluator；
- Aggregation；
- Result Provenance。

## 48. Evaluation Framework Conformance

未来任何 Runner 接入时都必须通过 Evaluator Conformance Test。

至少使用一组 Golden Cases 检查：

- 正确答案；
- 错误答案；
- 边界 Tolerance；
- 单位转换；
- Invalid Output；
- Multiple Choice；
- Structured Answer；
- Multimodal Asset。

目标是验证不同 Runner 对同一 Item、同一 Dataset Version、同一 Evaluation Profile 得到相同的 Parse Status 和 Score。

本节只定义 Conformance 原则，不实现测试代码。

## 49. Pilot Evaluation Role

Phase 6 使用多个能力层级模型进行 Pilot Evaluation，不只是为了排行。

模型结果还用于反向检查：

~~~text
item difficulty
item discrimination
ambiguity
broken item
unexpected answer pattern
visual dependency
scoring instability
~~~

这些结果属于 Benchmark Calibration。Pilot 需要帮助识别错误题、歧义题、异常答案模式和评分不稳定问题，但本文件不提前定义最终 Difficulty / Discrimination 阈值；具体方法留给 Pilot Design。

## 50. Broken Item Policy

如果评测过程中发现以下问题：

- Ground Truth 错误；
- 题目歧义；
- Evidence 不充分；
- Image 缺失；
- Scoring Evaluator 错误；

不能为了当前 Run 直接修改历史 Dataset Snapshot。

应当：

1. 标记 Item QA Issue；
2. 产生新的 Item Revision；
3. 必要时产生新的 Dataset Version；
4. 保留历史 Run 与旧 Snapshot 的关联。

历史 Run 继续关联旧 Snapshot，不因新 Revision 自动重算或漂移。

## 51. Score Precision

内部保存原始 Float Score。展示时建议保留 1～2 位小数，但不得在 Item 聚合前过早四舍五入。

对于 Partial Credit，应同时保留足以复核的原始 Item Score、Evaluator Version 和必要的 Field Scores。展示精度不应改变 Canonical Score。

## 52. Open Questions

以下问题尚未正式决定，全部保持 TBD：

1. Official Evaluation 的 exact generation config 是否对所有模型统一？—— TBD
2. 不同 Provider 无法支持相同 decoding 参数时如何保证公平？—— TBD
3. Infrastructure Retry 最大次数是多少？—— TBD
4. Short Answer 哪些 Task 允许进入 LLM Judge fallback？—— TBD
5. Judge 使用单模型、多模型还是 Human Adjudication？—— TBD
6. Structured Answer 默认 weighted mean 是否需要按 Task 定制？—— TBD
7. Numeric Unit Registry 采用什么实现？—— TBD
8. 95% CI 的最终算法和参数是什么？—— TBD
9. 是否加入 Prompt Robustness Diagnostic？—— TBD
10. 是否加入 Option Permutation Diagnostic？—— TBD
11. Baseline / Anchor Models 具体选哪些？—— TBD
12. 模型 Reasoning / Thinking Mode 如何统一比较？—— TBD
13. 长输出被 max tokens 截断如何处理？—— TBD
14. 是否为 Model Self-consistency 建立独立 Experiment Profile？—— TBD
15. Official Leaderboard 是否允许 Closed API 与 Open-weight 模型同榜？—— TBD
16. Evaluation Run Invalid / Partial 的正式判定规则是什么？—— TBD

本节问题不能被本文件的 Baseline Scoring Policy 或示例默认解释为已经解决。

## 53. Scoring Examples

以下示例只用于说明 Evaluation Semantics，不是真实 Benchmark Item，也不构成新的题目、Taxonomy 或 Ground Truth 数据。

### Example 1：Single Choice 正确 / 错误

~~~text
Ground Truth: correct_option_id = opt_2

Model A Parsed Answer: opt_2
Item Score: 1

Model B Parsed Answer: opt_3
Item Score: 0
~~~

如果 Model C 输出“opt_2，也可能是 opt_3”，Parser 应标记 ambiguous_parse，Item Score = 0。

### Example 2：Multiple Choice Exact Set

~~~text
Ground Truth: {opt_1, opt_3}

Prediction A: {opt_3, opt_1}
Item Score: 1

Prediction B: {opt_1}
Item Score: 0

Prediction C: {opt_1, opt_2, opt_3}
Item Score: 0
~~~

Prediction A 仅因顺序不同仍为 Exact Set Match；Prediction C 不能通过“多选更多选项”获得默认 Partial Credit。

### Example 3：Numeric 单位等价

~~~text
Ground Truth:
  value = 955
  unit = N·m
  absolute_tolerance = 1
  relative_tolerance = 0.01

Prediction A: 955 N·m
Normalized Value: 955 N·m
Result: correct

Prediction B: 0.955 kN·m
Normalized Value: 955 N·m
Result: correct
~~~

Prediction B 通过合法兼容单位转换后与 Canonical Ground Truth 比较。

### Example 4：Numeric 超出 Tolerance

~~~text
Ground Truth: y = 100, absolute_tolerance = 1, relative_tolerance = 0.01
allowed_error = max(1, 0.01 × |100|) = 1

Prediction: x = 102
absolute_error = 2
Result: incorrect, Item Score = 0
~~~

不得从 Calculation Object 读取另一套 tolerance，也不得为了让 102 通过而改变 Ground Truth。

### Example 5：Short Answer Alias

~~~text
Canonical Answer: 滚动轴承
Accepted Alias: 滚动轴承类型

Prediction: 滚动轴承类型
Result: Alias Match, Item Score = 1

Prediction: 与题意无关的轴承答案
Result: no deterministic match; score depends on the versioned fallback policy
~~~

如果进入 LLM Judge fallback，必须记录 Judge Model、Prompt Version、Rubric Version 和 Judge Result。

### Example 6：Structured Answer Partial Credit

~~~text
Required Fields: fault_mode, recommended_action
Canonical:
  fault_mode = lubrication_failure
  recommended_action = inspect lubrication and contamination

Prediction:
  fault_mode = lubrication_failure
  recommended_action = unrelated action

field_scores = [1.0, 0.0]
Item Score = mean([1.0, 0.0]) = 0.5
~~~

Optional Field 不进入默认分数；若额外字段与 Required Field 矛盾，应记录 conflict 并按版本化规则处理。

### Example 7：Multimodal Numeric

~~~text
Input: assembly drawing + question
Task: read a dimension from the drawing and calculate clearance
Answer Type: numeric

Model Adapter: sends the correct Asset in the fixed order
Evaluator: numeric_tolerance_v1
Result: scored by Numeric Rule, not by a separate “multimodal score”
~~~

如果漏图、换图或改变图片顺序，应记录 Input Construction / Adapter Error，而不能把它静默解释为模型视觉能力为零。

### Example 8：Invalid / Conflicting Output

~~~text
Question: select one option
Model Response: A, but final answer is B
Parse Status: ambiguous_parse
Item Score: 0

Transport Failure: HTTP 5xx before a normal response
Parse Status: runtime_error
Handling: Infrastructure Retry or Run Policy decision
~~~

Transport Failure 不应被自动计入模型内容错误；正常返回的冲突答案则属于模型输出解析失败。

## 54. 文档状态与当前交付边界

本文件当前状态为 Draft - Pending Review，Version 保持 0.1。本文件只完成 Evaluation Specification v0.1 的语义设计，不表示 Evaluation Runner、框架 Adapter、Pilot Evaluation 或正式 Leaderboard 已经实现。

本阶段不开始：

- System Architecture 正文；
- Pilot Design；
- Evaluation Runner 实现；
- OpenCompass / VLMEvalKit 配置；
- 模型调用；
- 自动评测代码。

## 55. References to Upstream Documents

本文件的上位引用包括：

- Project Charter v0.1：定义 Benchmark 的目标、范围和成功标准；
- Project Plan v0.1：定义阶段、Gate 和交付顺序；
- Benchmark Taxonomy v0.1：定义 Domain、Track、Capability、Task、Modality、Difficulty 和 Answer Type；
- Data Specification v0.1：定义 Canonical Benchmark Item、Canonical Ground Truth、Source Provenance、Item Revision 和 Dataset Membership。

Evaluation Specification 只解释如何评测这些 Canonical 结构，不改变其字段语义。

## 56. 变更记录

| 版本 | 日期 | 变更说明 |
| --- | --- | --- |
| v0.1 | 2026-09-11 | 建立 framework-independent Evaluation Semantics、评分规则、运行规范、结果实体、聚合策略和 Open Questions；状态保持 Draft - Pending Review |
