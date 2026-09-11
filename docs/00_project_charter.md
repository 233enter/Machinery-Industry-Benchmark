# 机械工业通用知识大模型 Benchmark 项目章程

## 文档信息

| 项目 | 内容 |
| --- | --- |
| Project | Mechanical Industry General Benchmark |
| 文档 | Project Charter v0.1 |
| Current Phase | Phase 0 - Benchmark Design |
| Current Milestone | Benchmark Design v0.1 |
| Current Task | Project Charter v0.1 |
| 文档状态 | 首次评审通过，V0.1 小范围修订 |
| 日期 | 2026-09-11 |

> 本章程用于定义项目的背景、目标、范围、原则、阶段和初步成功标准。V0.1 中标注为“初步”“暂定”或“待后续确认”的内容，均可根据 Pilot Benchmark 结果和项目评审进行调整。

## 1. 项目定义

本项目计划构建一个“机械工业通用知识大模型 Benchmark”（Mechanical Industry General Benchmark），用于系统评估通用大语言模型（LLM）及多模态大语言模型（MLLM）在机械工业领域的能力。

Benchmark 的核心不是收集尽可能多的题目，而是稳定、可信、可复现地测量模型能力，并支持模型之间的对比、诊断和持续回归测试。

## 2. 项目背景

### 2.1 现有资源与不确定性

当前项目拥有约 70,000 本机械工业相关 PDF 文档，但这些文档的具体类别、质量、重复率、版本关系、可解析性和内容分布目前未知。因此，现阶段不能把这些 PDF 直接视为 Benchmark 数据。

这批 PDF 在项目中的正式定位是：

> **Candidate Source Corpus（候选知识源库）**

它们是未来进行知识源盘点、筛选和构建 Benchmark 的候选资料，不等同于 Benchmark 数据集，也不等同于最终的 Benchmark Source Corpus。

### 2.2 目标构建链路

Benchmark 后续需要经过以下过程逐步形成：

```text
知识源盘点
    → 文档筛选
    → 能力体系设计
    → 信息抽取
    → 题目构建
    → Ground Truth 验证
    → 质量控制
    → 模型验证
```

这条链路是项目的目标流程描述，不代表当前 Phase 0 要实现其中的工程代码。

### 2.3 当前阶段边界

当前处于 Benchmark Design 阶段，重点是完成项目定义和设计约束。当前任务不实现 PDF 解析、数据生成、模型调用或评测框架，也不在本章程中展开详细的 Benchmark Taxonomy。

## 3. Benchmark V1 初步目标

### 3.1 一级能力范围与初始比例

Benchmark V1 当前暂定评估以下三类一级能力：

| 一级能力 | 初始比例 | 能力定义 |
| --- | ---: | --- |
| Mechanical Knowledge | 40% | 机械工业专业知识与通识理解 |
| Engineering Calculation | 30% | 机械领域公式、数据和多步骤工程计算 |
| Multimodal Understanding | 30% | 对机械图纸、结构图、表格、曲线、示意图等工业视觉信息的理解和推理 |

以上比例属于 V0.1 初始设计，不是不可变的最终配额。正式 Pilot 后，可根据题目质量、能力覆盖、难度和模型区分度调整。

### 3.2 规模目标

- 在正式扩展 V1 前，优先建设约 500 道高质量 Pilot Benchmark。
- Pilot 通过质量检查和多模型验证后，再扩展为约 3,000～5,000 道高质量题目的 Benchmark V1。
- V1 不要求使用完全部 70,000 本 PDF，来源规模应服从质量、覆盖和可验证性要求。

## 4. Benchmark 核心目标

### 4.1 正确性

Ground Truth 必须具有较高可信度。Benchmark 不以题目数量为主要目标，而以答案正确、题意明确、评价稳定为首要目标。

### 4.2 可追溯性

每一道由资料构建的 Benchmark 题目，都应尽可能追溯到：

- source document；
- page；
- 原始文本、公式、表格或图片；
- 必要时的 bbox 或其他区域信息。

题目、答案和验证结论应能够回到原始资料进行复核。

### 4.3 可复现性

题目构建、验证和评测流程应能够重新运行。相关输入、版本、配置、验证记录和结果应以可复现的方式保存。

### 4.4 区分度

Benchmark 应能够有效区分不同模型的能力，而不是由大量过于简单、模型容易凭常识或模式猜测答对的问题组成。题目难度和区分度需要通过 Pilot 阶段的多模型测试进行验证。

### 4.5 能力覆盖

Benchmark 不仅测试模型是否记忆机械知识，也需要评估：

- 知识理解；
- 工程计算；
- 多步骤推理；
- 多模态工业理解。

### 4.6 可扩展性

V1 后续应能够继续增加新机械领域、新能力类型、新题型和新多模态任务，同时不破坏现有 Schema 和评测体系。

### 4.7 抗数据污染

Benchmark Source Corpus 与后续可能用于 CPT / SFT 的训练语料原则上应隔离。污染控制不能只停留在题目级别，还应考虑 document-family 级别的数据污染，包括：

- 同一本书的不同版本；
- 扫描版与文本版；
- 同一资料的不同来源；
- 高度重复的资料。

## 5. Benchmark V1 范围

### 5.1 In Scope

当前 V1 纳入以下范围：

- 机械工业通用知识；
- 工程公式和数值计算；
- 机械工业图像、图纸、表格和图表理解；
- 可客观评测的专业知识题；
- 部分需要工程推理的问题；
- 文本 LLM；
- 多模态 LLM。

### 5.2 Out of Scope / Not Priority for V1

以下内容不作为当前 V1 的重点：

- Agent 工具调用能力；
- 长周期任务执行；
- 大规模代码工程能力；
- CAD 文件直接生成质量评测；
- CAE 仿真结果质量评测；
- 机器人控制能力；
- 实际设备操作能力；
- 纯语言风格和主观写作质量。

上述内容不是永久排除，而是不属于当前 Benchmark V1 的核心范围，未来可在新的版本或专项 Benchmark 中单独评估。

## 6. 候选数据源定位与使用边界

### 6.1 语料库定义

```text
70k PDFs != Benchmark
```

70,000 份 PDF 当前只能定义为 **Candidate Source Corpus**。只有经过盘点、去重、分类、质量评估和来源选择后，其中一部分才可能进入：

> **Benchmark Source Corpus**

### 6.2 后续筛选路径

```text
Candidate Source Corpus
        ↓
Inventory
        ↓
Deduplication
        ↓
Classification
        ↓
Quality Assessment
        ↓
Source Selection
        ↓
Benchmark Source Corpus
```

V1 不要求使用完全部 7 万本 PDF。进入 Benchmark Source Corpus 的资料，应以来源可信度、内容质量、可追溯性、能力覆盖和污染控制等要求为依据。

## 7. Benchmark 构建原则

1. LLM 可以辅助生成题目，但不能默认作为最终 Ground Truth 来源。
2. 计算题优先采用程序、公式或规则进行 Ground Truth 验证。
3. 知识题应尽量能够回溯原始权威资料。
4. 多模态问题必须真正依赖视觉信息，不能退化成纯文本知识题。
5. Benchmark 数据应保留完整 Metadata。
6. 第一阶段优先质量，而不是数量。
7. 在大规模构建之前必须先完成 Pilot Benchmark。
8. Pilot 需要通过多个不同能力水平的模型进行测试，以分析：
   - 题目难度；
   - 区分度；
   - 歧义；
   - 错误题；
   - Ground Truth 问题。

## 8. 预期使用场景

Benchmark 预期支持以下使用场景：

- 不同通用 LLM 之间的机械工业能力对比；
- 不同多模态模型之间的机械视觉能力对比；
- 领域模型训练前后能力变化分析；
- CPT / SFT 前后效果评估；
- 模型版本迭代回归测试；
- 后续形成内部或公开 Leaderboard 的基础。

## 9. 项目不应被定义成

本项目不是：

- 机械题库的简单集合；
- PDF 自动出题系统；
- RAG 问答数据集；
- SFT 训练数据集；
- 单纯追求数据规模的 QA 数据集。

Benchmark 的核心定义是：

> **稳定、可信、可复现地测量模型能力。**

## 10. V0.1 初步成功标准

以下标准属于 V0.1 的初步目标，可在后续阶段根据 Pilot 结果调整：

1. 建立稳定的 Benchmark 能力体系。
2. 建立统一 Benchmark 数据 Schema。
3. 建立 Source Provenance 机制。
4. 完成约 500 道 Pilot Benchmark。
5. 至少使用多个不同能力层级的模型进行 Pilot 测试。
6. 根据 Pilot 数据验证题目具有一定区分度。
7. 建立基础自动评测能力。
8. 最终形成约 3,000～5,000 道 Benchmark V1。
9. 支持 Knowledge / Calculation / Multimodal 分项评分。
10. 可以输出模型整体分数和主要能力维度分析。

“基础自动评测能力”是后续实现阶段的交付目标，不代表当前 Phase 0 要编写评测代码。

## 11. 项目阶段

项目阶段在本章程中仅作高层划分，具体任务、交付物和进入/退出条件由后续项目计划及专项规范确定：

1. **Phase 0 - Benchmark Design**：完成项目定义、范围和初步设计约束。
2. **Phase 1 - Corpus Inventory**：盘点候选知识源库并建立语料画像。
3. **Phase 2 - Taxonomy & Source Selection**：确定能力体系并选择 Benchmark Source Corpus。
4. **Phase 3 - Corpus Processing**：对选定来源进行后续结构化处理。
5. **Phase 4 - Question Construction & Ground Truth**：构建题目并验证 Ground Truth。
6. **Phase 5 - Quality Control & Pilot Benchmark**：完成质量控制并形成约 500 道 Pilot。
7. **Phase 6 - Model Validation**：使用多个能力层级模型进行验证和分析。
8. **Phase 7 - Benchmark V1 Expansion**：根据 Pilot 结果修订并扩展至 V1 目标规模。
9. **Phase 8 - Evaluation & Reporting**：完善评测、分析和报告交付能力。

## 12. 当前阶段交付边界

> 本节描述的是当前 Project Charter 文档本身的设计边界，不是 Phase 0 - Benchmark Design 的全部交付物清单。

本次 Project Charter 文档修订的边界是：

- 明确项目背景和 Benchmark 定义；
- 明确 V1 的初步目标、范围和非重点范围；
- 明确候选知识源库与 Benchmark Source Corpus 的区别；
- 明确质量、可追溯性、可复现性、区分度、可扩展性和抗污染原则；
- 记录初步成功标准和后续阶段边界。

Phase 0 后续仍需要完成以下文档和设计工作：

- Project Plan；
- Benchmark Taxonomy；
- Data Specification；
- Evaluation Specification；
- System Architecture；
- Pilot Design。

这里只列出后续交付项，不在本节展开这些文档的具体设计。

就本 Project Charter 文档而言，以下内容不属于本次交付：

- PDF 解析代码；
- 数据生成代码；
- 模型调用代码；
- 评测框架或评测运行代码。

详细的能力分类、数据字段与格式、评测协议、系统实现方案和 Pilot Design，分别在后续文档和设计工作中讨论、设计与评审。

## 13. 调整与治理原则

- V0.1 的能力比例、题目规模和成功标准均为初步设计，允许由 Pilot 结果驱动调整。
- 任何影响能力定义、数据 Schema、Source Provenance 或评测可比性的变更，都应记录版本、原因和影响范围。
- 扩展新领域、新能力、新题型或新多模态任务时，应优先保持现有 Schema 和评测体系的兼容性。
- 具体角色、负责人、评审机制和发布审批流程待项目成员确认。

## 14. 主要风险与约束

| 风险/约束 | 项目影响 |
| --- | --- |
| 候选 PDF 的类别、质量、重复率和可解析性未知 | 可能影响来源选择、覆盖度和构题效率 |
| Ground Truth 可信度不足 | 直接影响 Benchmark 的正确性和公信力 |
| 同源资料进入训练语料和 Benchmark | 可能造成 document-family 级别数据污染 |
| 多模态题目对视觉信息依赖不足 | 可能把视觉评测退化为文本知识评测 |
| 题目过于简单、歧义或答案不稳定 | 影响区分度和模型排名解释性 |
| 过早追求规模 | 可能牺牲质量、可追溯性和可维护性 |

## 15. 变更记录

| 版本 | 日期 | 变更说明 |
| --- | --- | --- |
| v0.1 | 2026-09-11 | 完善项目背景、目标、范围、原则、成功标准和阶段定义 |
| v0.1 | 2026-09-11 | 首次评审通过后的范围澄清与 Open Questions 补充 |

## Open Questions

以下问题尚未正式决定，当前统一标记为 **TBD**：

| # | Open Question | Status |
| ---: | --- | --- |
| 1 | Mechanical Industry 的 Domain Taxonomy 最终如何划分？ | TBD |
| 2 | Mechanical Knowledge / Engineering Calculation / Multimodal Understanding 的 40% / 30% / 30% 比例是否合理？ | TBD |
| 3 | Pilot 约 500 道、V1 约 3,000～5,000 道的规模是否需要调整？ | TBD |
| 4 | 70k Candidate Source Corpus 中哪些类型 PDF 可以进入 Benchmark Source Corpus？ | TBD |
| 5 | Benchmark Source Corpus 与 CPT / SFT Corpus 的实际隔离策略如何实现？ | TBD |
| 6 | Benchmark 是否公开完整 Test Set，还是采用 Public Dev Set + Private Test Set？ | TBD |
| 7 | Knowledge、Calculation、Multimodal 分别采用什么主要评测方式和评测框架？ | TBD |
| 8 | Human Expert Review 可以投入多少资源？ | TBD |
| 9 | 如果缺少足够机械领域专家，Ground Truth 如何建立可靠验证链路？ | TBD |
| 10 | Benchmark 是否计划未来对外公开？ | TBD |
| 11 | Benchmark 最终采用哪些模型作为 Pilot 的 baseline / anchor models？ | TBD |
| 12 | 是否需要定期发布新版本以降低 Benchmark contamination？ | TBD |
