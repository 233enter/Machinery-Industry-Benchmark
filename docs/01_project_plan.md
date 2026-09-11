# 机械工业通用知识大模型 Benchmark 项目计划

## 文档信息

| 项目 | 内容 |
| --- | --- |
| Project | Mechanical Industry General Benchmark |
| 文档 | Project Plan |
| Version | 0.1 |
| Current Phase | Phase 0 - Benchmark Design |
| Current Milestone | Benchmark Design v0.1 |
| Current Task | Project Plan v0.1 |
| Status | Reviewed - Baseline |

## 1. 文档定位与管理方式

### 1.1 Project Plan 的定位

本文件用于定义 Mechanical Industry General Benchmark 的执行生命周期、阶段输入、工作包、交付物、验收标准、资源依赖和阶段门。它不是简单的 Todo List，也不是时间排期表。

本计划需要让项目成员能够回答：

- 当前处于哪个 Phase；
- 当前 Phase 的输入是什么；
- 当前 Phase 需要完成什么；
- 当前 Phase 产出什么；
- 当前 Phase 依赖哪些资源和前置条件；
- 达到什么标准才允许进入下一阶段；
- 哪些工作在当前阶段明确禁止提前进行。

### 1.2 生命周期管理模型

项目统一采用以下管理链路：

~~~text
Phase
  ↓
Work Package
  ↓
Deliverable
  ↓
Acceptance Criteria
  ↓
Exit Gate
~~~

每个 Phase 都必须有明确的 Objective、Inputs、Main Tasks / Work Packages、Deliverables、Acceptance Criteria、Required Resources、Dependencies、Risks 和 Exit Gate。

### 1.3 计划边界

- 本计划不填写具体完成日期、工期估算或排期承诺。
- 本计划只定义项目执行框架，不实现 PDF 解析、数据处理、模型调用、Benchmark 构建或评测代码。
- 本计划必须遵守 Project Charter v0.1，不自行改变 Benchmark 的目标、一级能力范围、Pilot / V1 初始规模或核心原则。
- 70,000 份 PDF 在进入筛选和验证前仍只称为 Candidate Source Corpus，不直接称为 Benchmark。
- 具体数据字段、评测指标、技术选型和实现接口由后续专项设计文档决定；本计划只规定其进入生命周期时必须满足的管理要求。

## 2. 项目总体阶段

### 2.1 生命周期总览

| Phase | 名称 | 阶段目标 |
| --- | --- | --- |
| Phase 0 | Benchmark Design | 冻结 Benchmark 的基本设计规则和跨文档约束 |
| Phase 1 | Corpus Inventory | 建立 70,000 份 Candidate Source Corpus 的数据画像 |
| Phase 2 | Taxonomy Calibration & Source Selection | 基于真实语料校准能力体系并选择 Benchmark Source Corpus |
| Phase 3 | Corpus Processing | 对已选择的 Benchmark Source Corpus 进行结构化处理 |
| Phase 4 | Question Construction & Ground Truth | 构建候选题目并建立 Ground Truth 验证记录 |
| Phase 5 | Quality Control & Pilot Benchmark | 从候选池中形成约 500 道高质量 Pilot Benchmark |
| Phase 6 | Model Validation & Calibration | 用多个能力层级模型验证并校准 Benchmark |
| Phase 7 | Benchmark V1 Expansion | 基于 Pilot 结果扩展至约 3,000～5,000 道 Benchmark V1 |
| Phase 8 | Evaluation & Reporting | 形成稳定、可重复运行的评测和报告能力 |

### 2.2 Phase 2 命名说明

Project Charter 中 Phase 2 的高层名称为 Taxonomy & Source Selection。本计划使用 Taxonomy Calibration & Source Selection，是为了明确区分两个连续但不同的动作：

1. Phase 0 建立理论层面的 Benchmark Taxonomy v0.1，不能把 Taxonomy 的第一次设计推迟到 Phase 2。
2. Phase 1 得到真实 Corpus Inventory 后，Phase 2 再基于数据分布、资料覆盖和可构题性对 Taxonomy 进行校准，形成用于 Pilot 的稳定版本。

因此，Phase 2 是对已有 Benchmark Taxonomy v0.1 的校准与来源选择，不是第一次设计 Taxonomy。

### 2.3 项目级顺序约束

项目按以下顺序推进：

~~~text
Benchmark Design
    → Corpus Inventory
    → Taxonomy Calibration & Source Selection
    → Corpus Processing
    → Question Construction & Ground Truth
    → Quality Control & Pilot Benchmark
    → Model Validation & Calibration
    → Benchmark V1 Expansion
    → Evaluation & Reporting
~~~

任何阶段 Gate 未通过时，应优先修复当前阶段的问题，而不是继续向后堆数据或扩大处理规模。

## 3. 项目级执行规则

### 3.1 与 Project Charter 的一致性

以下内容作为全生命周期的上位约束：

- Benchmark V1 的一级能力为 Mechanical Knowledge、Engineering Calculation 和 Multimodal Understanding。
- V0.1 初始比例为 Knowledge 40%、Calculation 30%、Multimodal 30%，后续可由 Pilot 结果驱动调整。
- 正式扩展 V1 前先建设约 500 道 Pilot Benchmark，之后再以约 3,000～5,000 道为 V1 初步规模目标。
- Ground Truth 的正确性、Source Provenance、可复现性、区分度、能力覆盖、可扩展性和抗数据污染是全流程要求。
- Candidate Source Corpus 与 Benchmark Source Corpus 必须保持概念和状态上的区分。

### 3.2 验收和 Gate 的通用要求

- 每个 Deliverable 都必须对应可检查的 Acceptance Criteria。
- 评审应记录输入版本、输出版本、未决问题、决策结果和附带条件。
- 未通过 Gate 时，问题必须进入当前阶段的修复队列或风险登记，不得静默忽略。
- 不应以处理文件数量、候选题数量或运行次数替代质量验收。
- 任何涉及 Schema、Source Provenance、Ground Truth 或评测可比性的变更，都必须进行跨文档影响检查。

### 3.3 当前明确禁止提前进行的工作

在相应设计和 Gate 完成前，不提前开展：

- 对全部 70,000 份 PDF 执行高成本全文解析或 OCR；
- 基于未经筛选的 Candidate Source Corpus 大规模自动出题；
- 把 LLM 输出直接当作最终 Ground Truth；
- 在未完成 Pilot 验证前直接扩大为 Benchmark V1；
- 在 Project Plan 中锁死唯一 PDF 解析工具或唯一评测框架；
- 将 Benchmark Source Corpus 未经污染审查地并入 CPT / SFT Corpus；
- 编写本阶段未授权的 PDF 解析、数据处理、模型调用、Benchmark 构建或评测实现代码。

## 4. Phase 0 - Benchmark Design

### Objective

在接触大规模数据处理之前，冻结 Benchmark 的基本设计规则、能力边界、数据和评测约束，并形成可供后续阶段执行和评审的设计基线。

### Inputs

- Project Charter v0.1；
- 前期 Benchmark 方案草稿；
- 当前项目目标；
- 已记录的 Open Questions 和项目级约束。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP0.1 Project Definition Alignment | 对齐 Project Charter、术语、目标、范围、初始规模和核心原则 |
| WP0.2 Project Plan | 完成本 Project Plan v0.1，定义生命周期、阶段门和资源要求 |
| WP0.3 Benchmark Taxonomy | 完成 Benchmark Taxonomy v0.1 的理论设计，明确能力体系的设计边界 |
| WP0.4 Data Specification | 完成 Data Specification v0.1，定义后续数据规范和 Schema 的设计边界 |
| WP0.5 Evaluation Specification | 完成 Evaluation Specification v0.1，定义后续评测规范的设计边界 |
| WP0.6 System Architecture | 完成 System Architecture v0.1，定义后续系统设计的边界和依赖 |
| WP0.7 Pilot Design | 完成 Pilot Design v0.1，明确 Pilot 的构建、验收和多模型验证方法 |
| WP0.8 Cross-document Design Review | 检查 Taxonomy、Data Schema、Evaluation Specification、Source Provenance 和 Pilot 设计之间的一致性 |

### Deliverables

- Project Plan v0.1；
- Benchmark Taxonomy v0.1；
- Data Specification v0.1；
- Evaluation Specification v0.1；
- System Architecture v0.1；
- Pilot Design v0.1；
- Phase 0 Design Review Record；
- 跨文档依赖和冲突记录。

### Acceptance Criteria

- 所有核心设计文档存在并通过项目评审；
- Taxonomy、Data Schema、Evaluation Specification 之间不存在明显定义冲突；
- 能够明确描述一条 Benchmark 数据从 Source 到最终评测结果的完整生命周期；
- Pilot 的构建和验收方式已经可以执行；
- Open Questions 被显式记录，仍未决定的问题标记为 TBD，没有被 Codex 擅自假设为已经解决；
- 未引入与 Project Charter 冲突的目标、能力范围、规模或原则；
- 未提前提交本阶段之外的工程实现。

### Required Resources

- 项目设计和 Benchmark 方法分析能力；
- 能够评审机械工业 Benchmark 定义的项目成员；
- Project Charter、前期方案和相关设计文档；
- 用于记录决策、版本和 Open Questions 的文档管理能力。

### Dependencies

- Project Charter v0.1 已作为上位约束；
- 前期 Benchmark 方案草稿可供参考；
- 项目成员能够对设计文档进行评审；
- 尚未决定的事项可以被显式保留为 TBD。

### Risks

- 设计文档之间出现目标、Schema 或评测定义冲突；
- 在缺少 Corpus Inventory 的情况下对领域分布或题目规模作出过强假设；
- 将开放问题误写成已确定方案；
- 过早进入工程实现，导致后续返工。

### Exit Gate

**Gate 0 - Benchmark Design Review**：只有在 Phase 0 Design Review 通过后，才允许进入 Corpus Inventory；未通过时不得启动 Phase 1，也不得启动 70,000 份 PDF 的大规模全量解析、自动出题或其他后续处理。

## 5. Phase 1 - Corpus Inventory

### Objective

回答“这 70,000 本 PDF 到底是什么”，建立 Candidate Source Corpus 的基础数据画像。本阶段采用轻量级 Inventory，不进行对全部 PDF 的高成本全文解析。

### Inputs

- 约 70,000 本 Candidate Source Corpus PDF；
- 已通过 Gate 0 的项目定义和数据规范边界；
- 待确认的 PDF 访问方式、目录结构和运行环境信息。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP1.1 Access and Scope Check | 确认数据实际访问方式、服务器路径、权限、总量和扫描范围 |
| WP1.2 File-level Inventory | 扫描文件路径、文件大小、基础 PDF metadata、页数和文件完整性 |
| WP1.3 Technical Profile | 判断是否存在 text layer，区分扫描 PDF / 文本 PDF，并记录基础可解析性信号 |
| WP1.4 Hash and Duplicate Signals | 计算 hash，识别完全重复文件，并记录可能的重复关系 |
| WP1.5 Document-family Signals | 从文件名、目录结构、版本信息和元数据中建立初步 document-family 信息 |
| WP1.6 Preliminary Classification | 对文档类型和领域分布进行初步判断，不把初步分类当作最终 Taxonomy |
| WP1.7 Sample-based Quality Analysis | 对抽样文档进行质量、内容和可解析性分析 |
| WP1.8 Representative Sample | 从 70,000 份 Candidate Source Corpus 中形成约 100～300 本具有代表性的 Representative Sample |

Phase 1 不应默认对全部 PDF 执行 MinerU 或高成本 OCR。解析技术的深入验证留到 Representative Sample 和后续 Corpus Processing 阶段。

### Deliverables

- corpus_inventory；
- Corpus Statistics；
- Duplicate Report；
- Corrupted / Unreadable PDF Report；
- Representative Sample Manifest；
- Corpus Inventory Report。

具体文件格式不在本 Phase 的计划中强制指定，parquet、jsonl 或其他实现方式由后续 Data Specification / System Architecture 决定。

### Acceptance Criteria

- 绝大多数可访问 PDF 已进入 Inventory，且 Inventory 覆盖情况有统计记录；
- 无法读取、损坏或权限不足的 PDF 被明确记录，不得静默忽略；
- 每个可识别文档具有稳定的 document_id；
- 可以统计 Candidate Source Corpus 的主要文档类型和基本领域分布；
- 可以识别完全重复文件，并输出 Duplicate Report；
- 可以形成初版 document-family 和可能版本关系信号；
- Representative Sample 包含约 100～300 本文档，并记录抽样覆盖和选择理由；
- 能够形成第一版数据质量画像；
- 本阶段没有将 Candidate Source Corpus 直接定义为 Benchmark Source Corpus。

### Required Resources

进入 Phase 1 前需要用户或项目方提供、确认或授权以下资源；本计划不假设这些信息目前已经提供：

- 70,000 份 PDF 的实际访问方式或服务器路径；
- 数据总大小；
- 目录结构；
- 服务器 OS；
- CPU；
- RAM；
- GPU（如有）；
- 可用磁盘空间；
- Docker 是否可用；
- 数据是否存在版权、内部保密或外发限制；
- 这些 PDF 是否还计划用于 CPT / SFT。

### Dependencies

- Gate 0 - Benchmark Design Review 通过；
- 获得 Candidate Source Corpus 的访问权限；
- 获得足够的文件扫描、元数据读取和结果保存能力；
- 对版权、保密和 CPT / SFT 使用边界有初步记录。

### Risks

- 无法获得完整数据访问权限或实际路径；
- 文件损坏、权限限制或目录结构不稳定；
- 仅凭文件名和元数据进行错误分类；
- 未能识别同一资料的不同版本或 document-family；
- 对全量 PDF 过早执行高成本处理，造成资源浪费；
- 数据使用限制未知，影响后续来源选择。

### Exit Gate

**Gate 1 - Corpus Inventory Review**：只有在 Inventory 覆盖、失败记录、重复识别、基本分布和 Representative Sample 达到评审要求后，才认为具备设计 Source Selection 的数据基础。

## 6. Phase 2 - Taxonomy Calibration & Source Selection

### Objective

解决两个问题：

1. Benchmark 最终测哪些机械领域与能力；
2. 70,000 份 Candidate Source Corpus 中哪些资料值得成为 Benchmark Source Corpus。

本阶段不是第一次设计 Taxonomy，而是利用 Phase 1 的真实 Corpus Inventory 对 Phase 0 的 Benchmark Taxonomy v0.1 进行校准，形成用于 Pilot 的稳定版本。

### Inputs

- Benchmark Taxonomy v0.1；
- Corpus Inventory；
- Representative Sample；
- Project Charter v0.1；
- Corpus Statistics、Duplicate Report 和质量画像；
- Data Governance 与 Contamination Control 的初步约束。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP2.1 Taxonomy Calibration | 根据真实 Corpus 分布、内容覆盖和可构题性校准 Domain Taxonomy |
| WP2.2 Coverage Analysis | 分析机械领域、能力范围和候选来源之间的覆盖关系 |
| WP2.3 Source Quality Assessment | 评估内容权威性、文档类型、年代、可解析性和 Ground Truth 可验证性 |
| WP2.4 Duplicate and Family Review | 评估重复关系、版本关系、扫描版 / 文本版关系和 document-family 风险 |
| WP2.5 Source Selection Strategy | 建立从 Candidate Source Corpus 到 Benchmark Source Corpus 的筛选规则 |
| WP2.6 Training Isolation Design | 设计 Benchmark Source Corpus 与潜在 CPT / SFT Corpus 的隔离和追踪策略 |
| WP2.7 Registry and Risk Review | 建立入选、排除和风险登记，并记录每项选择理由 |

评估维度至少包括：

- 内容覆盖；
- 权威性；
- 文档类型；
- 年代；
- 重复关系；
- 可解析性；
- Ground Truth 可验证性；
- 训练数据污染风险。

### Deliverables

- Benchmark Taxonomy v0.2；
- Source Selection Rules；
- Benchmark Source Corpus Registry；
- Exclusion / Risk Registry；
- Corpus Coverage Report；
- Training Corpus Isolation Design Record。

### Acceptance Criteria

- Benchmark Taxonomy v0.2 能覆盖 Pilot 的主要领域和能力目标；
- Taxonomy 的校准依据可以回到 Corpus Inventory 和 Representative Sample；
- 入选资料具有明确的选择理由；
- 被排除资料可以说明主要原因或风险；
- Benchmark Source Corpus 与潜在 Training Corpus 的关系可追踪；
- document-family 级别的版本、重复和污染风险被纳入审查；
- Source Selection 不以追求资料数量最大化为目标；
- Benchmark Source Corpus 的范围和状态经过评审确认。

### Required Resources

- Benchmark 方法和 Domain Taxonomy 设计能力；
- 机械工业领域专家或顾问；
- Corpus Inventory 统计和 Representative Sample；
- Source Provenance、Data Governance 和 Contamination Control 评审能力；
- 版权、保密和数据使用约束的确认资源。

### Dependencies

- Gate 1 - Corpus Inventory Review 通过；
- Benchmark Taxonomy v0.1 已完成；
- Corpus Inventory、Representative Sample 和重复分析可用；
- 项目方能够对 Candidate Source Corpus 的使用边界作出评审。

### Risks

- Corpus 分布不均导致 Taxonomy 偏向现有资料而不是目标能力；
- 资料权威性、年代或版权状态无法确认；
- document-family 关系识别不完整；
- Source Selection 规则过度追求覆盖或数量；
- Benchmark Source Corpus 与 CPT / SFT Corpus 的隔离无法落地。

### Exit Gate

**Gate 2 - Taxonomy & Source Corpus Review**：只有在 Taxonomy 校准、Source Selection 规则、Benchmark Source Corpus Registry 和污染隔离设计通过评审后，才允许对选定来源进行大规模结构化解析。

## 7. Phase 3 - Corpus Processing

### Objective

只对已经选择的高价值 Benchmark Source Corpus 做结构化处理，为 Knowledge、Engineering Calculation 和 Multimodal Understanding 三类题目构建提供可追溯的内容对象。

### Inputs

- Benchmark Source Corpus Registry；
- 已选定的 Benchmark Source Corpus 文档；
- Benchmark Taxonomy v0.2；
- Data Specification；
- Source Provenance 规则；
- Representative Sample 的解析验证结论。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP3.1 Processing Plan | 确定选定来源的处理范围、记录方式、失败处理和质量检查方法 |
| WP3.2 Parsing Option Evaluation | 在 Representative Sample 上评估 MinerU 或其他候选解析技术，不提前锁死唯一工具 |
| WP3.3 Layout Objects | 处理 text blocks、formulas、tables、figures 和 page images |
| WP3.4 Location and Relation | 保存 page number、coordinates / bbox 以及 source document relation |
| WP3.5 Provenance Preservation | 保持 document_id → page → region / bbox → original content 的追溯链路 |
| WP3.6 Processing Quality Review | 检查文本、公式、表格、图像、坐标和页面关系的完整性 |
| WP3.7 Failure Registry | 记录解析失败、低质量结果和需要人工处理的对象 |

### Deliverables

- Parsed Benchmark Source Corpus；
- Processing Manifest；
- Parsing Quality Report；
- Failed Parsing Registry；
- Source Provenance 完整性检查记录。

### Acceptance Criteria

- 解析结果能够支撑 Knowledge、Engineering Calculation 和 Multimodal Understanding 三类题目构建；
- 每个解析对象原则上能够通过 document_id → page → region / bbox → original content 追溯；
- 文本块、公式、表格、图像和页面信息之间的关系没有被静默丢失；
- 解析失败、低质量结果和未处理对象能够被发现并记录；
- 解析质量报告包含代表性样本和失败情况；
- 不以单一解析工具作为未经评审的强制前提；
- 不允许静默丢数据。

### Required Resources

- 已选择的 Benchmark Source Corpus 访问权限；
- 解析工具环境和技术评估能力；
- 足够的 CPU / GPU（按实际处理方案确定）；
- 用于保存页面图像、结构化对象和 Metadata 的磁盘空间；
- 能检查 PDF layout、公式、表格、图像和 bbox 的技术或领域审核资源。

### Dependencies

- Gate 2 - Taxonomy & Source Corpus Review 通过；
- Data Specification 和 Source Provenance 规则已具备可执行边界；
- Benchmark Source Corpus Registry 已建立；
- Representative Sample 可用于解析技术验证。

### Risks

- layout parsing 或 OCR 丢失原始结构；
- 公式、表格、图纸或图片区域识别质量不足；
- page number、coordinates / bbox 与原始内容关系错位；
- 解析结果过大导致存储或处理资源不足；
- 解析失败未被发现，造成后续题目无法追溯。

### Exit Gate

**Gate 3 - Corpus Processing Review**：只有在解析质量足以支持题目构建、Source Provenance 未丢失且失败对象有明确记录后，才允许进入 Question Construction & Ground Truth。

## 8. Phase 4 - Question Construction & Ground Truth

### Objective

建立候选 Benchmark 数据，而不是直接形成最终 Benchmark。候选题目必须绑定 Source Provenance，并为后续质量控制和 Pilot 筛选保留完整的构建与验证记录。

### Inputs

- Parsed Benchmark Source Corpus；
- Benchmark Taxonomy v0.2；
- Data Specification；
- Evaluation Specification；
- Source Provenance 规则；
- 解析质量和失败登记结果。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP4.1 Evidence and Provenance | 选择 evidence，绑定 source document、page、原始内容和必要的 region / bbox |
| WP4.2 Knowledge Construction | 按 Source → Evidence → Candidate Question → Candidate Answer → Evidence Verification 路径构建知识题 |
| WP4.3 Calculation Construction | 按 Source Formula / Engineering Relation → Structured Formula → Variables / Constraints → Parameterized Problem → Programmatic Ground Truth → Unit / Tolerance Verification 路径构建计算题 |
| WP4.4 Multimodal Construction | 按 Source Figure / Drawing / Table / Chart → Visual Region → Question → Ground Truth → Image Dependency Verification 路径构建多模态题 |
| WP4.5 Candidate Generation | 生成候选问题、答案、参数、Metadata 和构建记录 |
| WP4.6 Verification and Filtering | 执行自动规则检查、重复题检测、字段检查和初步 Ground Truth 验证 |
| WP4.7 Rejection Tracking | 记录被拒绝、被修改或待复核的候选题目及其原因 |

LLM 可以用于候选问题生成、改写、分类和辅助审核，但不能默认承担最终 Ground Truth。计算题应优先采用程序、公式或规则验证；知识题应尽量回到原始权威资料；多模态题必须验证其确实依赖视觉信息。

### Deliverables

- Candidate Benchmark Pool；
- Ground Truth Verification Records；
- Generation Records；
- Rejected Candidate Registry；
- Question-level Source Provenance Records；
- Candidate Pool Schema Validation Report。

Candidate Benchmark Pool 的规模不在本 Project Plan 中锁死，但应明显大于最终约 500 道 Pilot Benchmark，以便后续筛选、去重和质量控制。

### Acceptance Criteria

- Knowledge、Calculation 和 Multimodal 三条构建路径均有清晰的输入、输出和验证记录；
- Source-based 候选题目能够回溯 Source Provenance；
- Calculation 候选题目具有结构化公式、变量、约束、计算结果以及单位 / 容差验证记录；
- Multimodal 候选题目具有视觉区域和 Image Dependency Verification 记录；
- 候选题目通过 Schema Validation，并记录缺失字段；
- 重复、近重复、歧义和明显错误候选题目能够被标记或拒绝；
- Candidate Benchmark Pool 明显大于最终 Pilot 所需规模；
- LLM 的作用被记录为辅助生成或审核，不被默认视为最终 Ground Truth 来源。

### Required Resources

- Parsed Benchmark Source Corpus 及其 Source Provenance；
- 机械领域专家或领域审核资源；
- LLM API 或本地模型（可选，用于候选生成和辅助审核）；
- Python 计算环境或其他可执行的公式验证环境；
- 能够查看图纸、表格、图表和页面图像的视觉审核资源；
- 用于保存候选、拒绝和验证记录的存储与版本管理能力。

### Dependencies

- Gate 3 - Corpus Processing Review 通过；
- Data Specification、Benchmark Taxonomy v0.2 和 Source Provenance 规则可用；
- 解析对象和原始页面关系可被访问；
- 计算和多模态题目具有相应的验证资源。

### Risks

- LLM 生成幻觉、题意歧义或答案错误；
- 公式、单位、参数约束或容差处理不完整；
- 多模态题退化为不依赖图像的纯文本知识题；
- Candidate Benchmark Pool 领域覆盖不足；
- Source Provenance 绑定错误或构建记录不完整；
- 候选题目重复率过高。

### Exit Gate

**Gate 4 - Candidate Benchmark Review**：只有在候选池、Ground Truth Verification Records、Source Provenance 和拒绝记录达到评审要求后，才允许从候选池中筛选并进入 Pilot。

## 9. Phase 5 - Quality Control & Pilot Benchmark

### Objective

从 Candidate Benchmark Pool 中选出约 500 道高质量 Pilot Benchmark，完成题目级质量控制、来源验证、答案验证、污染检查和必要的人工抽检。

### Inputs

- Candidate Benchmark Pool；
- Ground Truth Verification Records；
- Data Specification；
- Evaluation Specification；
- Source Provenance Records；
- Candidate Pool Schema Validation Report；
- Rejected Candidate Registry。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP5.1 Schema Validation | 检查每道题是否符合 Data Specification 和统一 Schema |
| WP5.2 Source and Answer Verification | 检查 Source Provenance、原始资料和 Ground Truth 验证记录 |
| WP5.3 Duplicate Detection | 进行重复题、近重复题和 document-family 级别污染检查 |
| WP5.4 Ambiguity and Difficulty Review | 检查题意、信息充分性、答案稳定性和初步难度 |
| WP5.5 Multimodal Dependency Check | 检查多模态题是否真正依赖图像、图纸、表格或图表信息 |
| WP5.6 Human Sampling | 进行必要的机械领域专家审核和人工抽检 |
| WP5.7 Pilot Assembly | 组装约 500 道 Pilot Benchmark，并检查初始能力比例 |
| WP5.8 Minimum Evaluation Runner | 为后续 Phase 6 模型验证准备最小可用 Evaluation Runner |
| WP5.9 Dataset Documentation | 形成 Pilot Dataset Card、修改记录和拒绝记录 |

Pilot 的初始比例参考 Knowledge 40%、Calculation 30%、Multimodal 30%，但该比例仍可根据数据质量、可验证性、覆盖和 Pilot 设计评审进行调整，调整必须留下记录。

### Deliverables

- Pilot Benchmark v0.1；
- Pilot QA Report；
- Rejected / Modified Items Registry；
- Pilot Dataset Card；
- Pilot Source Provenance Audit Record；
- Minimum Evaluation Runner Readiness Record。

### Acceptance Criteria

- Pilot 中每道题符合 Data Specification；
- 每道题具有明确的 Ground Truth 验证记录；
- Source-based 数据可以回溯 Source Provenance；
- 多模态题不能仅依赖文本猜测，且具有 Image Dependency Verification 结论；
- 不存在未处理的明显重复题、歧义题或错误题；
- 修改、拒绝和待复核项均有登记；
- Pilot 的 Knowledge / Calculation / Multimodal 分布与批准的初始设计一致，或已记录调整理由；
- Pilot 能够用于正式的多模型实验；
- 最小可用 Evaluation Runner 可以按既定输入运行并输出可保存的结果。

### Required Resources

- 质量审核流程和自动 Schema / 重复检查能力；
- 机械工业领域专家或人工审核资源；
- Source Provenance 和 Ground Truth 复核资源；
- 图像、图纸、表格和图表的视觉审核资源；
- 最小可用 Evaluation Runner；
- 用于后续多模型测试的模型访问权限或运行资源；
- 版权、保密和数据污染审核资源。

### Dependencies

- Gate 4 - Candidate Benchmark Review 通过；
- Candidate Benchmark Pool 和拒绝记录可用；
- Data Specification、Evaluation Specification 和 Pilot Design v0.1 已通过 Phase 0 设计评审；
- 至少具备可运行的最小评测路径。

### Risks

- 候选池中可通过审核的题目不足约 500 道；
- 人工审核资源不足，导致 Ground Truth 或歧义问题未被发现；
- 初始比例与真实可用数据不匹配；
- 多模态题视觉依赖不足；
- 污染检查遗漏同一 document-family 的版本或来源；
- 为满足数量目标而降低质量标准。

### Exit Gate

**Gate 5 - Pilot Quality Review**：只有在 Pilot 的 Schema、Ground Truth、Source Provenance、重复、歧义、多模态依赖和污染检查通过后，才允许进入正式多模型验证。

## 10. Phase 6 - Model Validation & Calibration

### Objective

利用多个不同能力水平的模型反向验证 Benchmark 本身，而不是单纯跑分。重点分析题目难度、区分度、答案稳定性、潜在错误和 Taxonomy / Difficulty 的校准建议。

### Inputs

- Pilot Benchmark v0.1；
- Pilot QA Report；
- Evaluation Specification；
- Minimum Evaluation Runner；
- 结果记录 Schema；
- 可用的模型访问方式；
- Baseline / Anchor Models：TBD。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP6.1 Multi-model Execution | 使用多个不同能力层级的模型运行 Pilot |
| WP6.2 Result Collection | 保存模型、题目、版本、运行配置和结果关系 |
| WP6.3 Item-level Analysis | 分析 Item Accuracy / Pass Rate、Difficulty 和 Answer Stability |
| WP6.4 Separation Analysis | 分析 Model Separation、模型间差异和能力分项表现 |
| WP6.5 Broken-item Review | 识别 Potential Ambiguity、Potential Broken Item 和异常结果 |
| WP6.6 Calibration Feedback | 形成 Taxonomy、Difficulty、题型和质量控制的校准建议 |
| WP6.7 Evaluation Review | 检查评测结果是否可复现、可解释并足以支持 V1 扩展决策 |

可以在 Evaluation Specification 中进一步讨论 item discrimination、模型间方差、难度分桶和错误模式分析，但本 Project Plan 不提前锁死统计方法。

Baseline / Anchor Models 当前仍为 TBD，不在本阶段擅自指定具体模型名单。

### Deliverables

- Model × Item Result Matrix；
- Pilot Evaluation Report；
- Item Quality Report；
- Broken / Suspicious Item List；
- Taxonomy / Difficulty Calibration Suggestions；
- Pilot Validation Decision Record。

### Acceptance Criteria

- Pilot 已在多个不同能力层级的模型上完成运行，模型范围和运行失败有记录；
- Model × Item Result Matrix 的输入版本、题目版本、模型标识和运行信息可追溯；
- 分析至少覆盖 Item Accuracy / Pass Rate、Difficulty、Model Separation、Answer Stability、Potential Ambiguity 和 Potential Broken Item；
- Knowledge、Calculation、Multimodal 的分项结果能够被单独分析；
- 发现的可疑题目、错误题目和 Ground Truth 问题进入修复或排除记录；
- 能够根据 Pilot 数据判断题目是否具有一定区分度；
- 统计方法和 Baseline / Anchor Models 的未决事项没有被擅自写成最终决定；
- 形成是否进入 Benchmark V1 Expansion 的明确评审依据。

### Required Resources

- 多个不同能力层级模型的访问权限或运行环境；
- Minimum Evaluation Runner；
- 结果存储和 Model × Item 分析能力；
- 评测、统计和质量分析人员；
- 必要的机械领域专家复核资源；
- 模型运行成本、配额和失败重试管理能力。

### Dependencies

- Gate 5 - Pilot Quality Review 通过；
- Pilot Benchmark v0.1 和 Evaluation Specification 可用；
- Minimum Evaluation Runner 已具备；
- 模型访问权限、运行预算和结果存储能力已确认；
- Baseline / Anchor Models 的选择仍可作为 TBD 管理。

### Risks

- 模型访问、版本或运行条件不一致；
- 运行成本或配额不足；
- 评测 Runner、Judge 或答案格式导致结果不稳定；
- 模型差异无法区分题目质量问题与真实能力差异；
- Pilot 题目过于简单、过难或存在系统性歧义；
- 统计结果被过度解释为最终 Benchmark 结论。

### Exit Gate

**Gate 6 - Pilot Validation Review**：只有在 Pilot 被证明具有足够质量和一定模型区分度，且问题项已得到处理或明确登记后，才允许扩展 Benchmark V1。

## 11. Phase 7 - Benchmark V1 Expansion

### Objective

基于已经经过 Pilot 验证的流程、规则和设计，将 Benchmark 扩展到约 3,000～5,000 道 Benchmark V1。扩展不能只是把未经验证的自动生成结果按数量放大。

### Inputs

- Pilot Evaluation Report；
- Item Quality Report；
- Taxonomy / Difficulty Calibration Suggestions；
- 已校准的 Benchmark Taxonomy；
- 已验证的 Data Specification、Ground Truth、Quality Control 和 Evaluation Protocol；
- Benchmark Source Corpus Registry；
- 经过审核的候选题目和构建记录。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP7.1 Validated Pipeline Reuse | 沿用 Pilot 验证过的 Taxonomy、Schema、Ground Truth、Quality Control 和 Evaluation Protocol |
| WP7.2 Candidate Expansion | 在已选 Benchmark Source Corpus 范围内扩展候选题目和能力覆盖 |
| WP7.3 Balance Review | 检查 Domain Balance、Capability Balance 和 Difficulty Balance |
| WP7.4 Source Concentration Review | 检查题目是否过度集中于少数来源、文档或 document-family |
| WP7.5 Contamination and Duplicate Review | 重新检查 Duplicate / Near Duplicate 和 Benchmark contamination |
| WP7.6 V1 Quality Control | 执行与 Pilot 等价或更严格的质量、来源、答案和视觉依赖检查 |
| WP7.7 Release Candidate Assembly | 形成 Benchmark V1 Candidate、版本清单和数据说明 |

Public / Private Split 当前保持 TBD。是否采用完整公开 Test Set，或采用 Public Dev Set + Private Test Set，应由后续项目决策确定。

### Deliverables

- Benchmark V1 Candidate；
- Benchmark V1 QA Report；
- Dataset Card；
- Version Manifest；
- V1 Source Provenance Audit Record；
- Public / Private Split Decision Record（如作出决定）。

### Acceptance Criteria

- 候选 Benchmark V1 规模约为 3,000～5,000 道，或对偏离目标有明确评审记录；
- 所有扩展题目沿用经过 Pilot 验证的构建、Ground Truth 和质量控制流程；
- Knowledge、Calculation、Multimodal 的比例为批准后的版本，若不同于 40% / 30% / 30%，必须有 Pilot 依据；
- Domain Balance、Capability Balance、Difficulty Balance 和 Source Concentration 已被检查；
- Duplicate / Near Duplicate、document-family 和 Benchmark contamination 已被重新检查；
- 题目、Ground Truth、Source Provenance、版本和质量记录完整；
- Public / Private Split 的未决状态被明确记录，不被默认为已公开或已私有；
- Benchmark V1 Candidate 可以进入 Benchmark V1 Dataset Readiness Review。

### Required Resources

- 经过 Pilot 验证的题目构建和质量控制能力；
- 可扩展的 Benchmark Source Corpus 访问与处理资源；
- 机械领域专家、质量审核和多模态审核资源；
- 用于候选生成、计算验证和结果检查的模型及计算资源；
- 版本管理、存储、污染审查和发布准备能力。

### Dependencies

- Gate 6 - Pilot Validation Review 通过；
- Pilot 的修复项、校准建议和决策记录已处理；
- Benchmark Source Corpus Registry 和 Source Provenance 可持续使用；
- Data Specification、Evaluation Protocol 和 Quality Control 规则已稳定到可复用状态。

### Risks

- 扩展规模导致质量下降或审核能力不足；
- 新增题目与 Pilot 的难度、能力或领域分布不一致；
- 来源集中、近重复或 document-family 污染在扩展中重新出现；
- 题目数量压力导致 Ground Truth 或 Source Provenance 不完整；
- Public / Private Split 和版权限制影响发布方式。

### Exit Gate

**Gate 7 - Benchmark V1 Dataset Readiness Review**：确认 Benchmark V1 数据集本身已经满足 Schema、Ground Truth、Source Provenance、Quality、Domain / Capability / Difficulty Balance、Duplicate / Near Duplicate、contamination、Dataset Card 和 Version Manifest 等要求。Gate 7 通过表示“Benchmark V1 Dataset 已达到冻结候选状态，可以进入正式 Evaluation & Reporting 工程化”。Gate 7 不表示 Benchmark 已经正式公开发布。

## 12. Phase 8 - Evaluation & Reporting

### Objective

形成稳定、可重复运行的 Benchmark 评测和报告能力，使模型运行、自动评分、分项评分、结果存储、Leaderboard 数据、错误分析和 Benchmark Report 能够纳入统一的可追溯流程。

Phase 5 / Phase 6 为 Pilot 模型验证必须具备最小可用 Evaluation Runner；Phase 8 的任务是将其工程化、标准化并完善报告能力，而不是第一次实现评测。

### Inputs

- 通过 Gate 7 - Benchmark V1 Dataset Readiness Review 的 Benchmark V1 Dataset 或批准的内部版本；
- Evaluation Specification；
- Pilot 阶段和模型验证阶段的结果记录；
- 已验证的评分、分项分析和结果 Schema；
- 模型运行适配需求；
- Public / Private Split 决策（如已确定）。

### Main Tasks / Work Packages

| Work Package | 主要工作 |
| --- | --- |
| WP8.1 Model Runtime Adaptation | 处理不同文本 LLM 和多模态 LLM 的运行适配 |
| WP8.2 Evaluation Runners | 形成 Text / Calculation Evaluation Runner 和 Multimodal Evaluation Runner 等逻辑组件 |
| WP8.3 Automatic Scoring | 实现批准的自动评分、规则验证和结果汇总流程 |
| WP8.4 Subscore Reporting | 输出 Knowledge、Calculation、Multimodal 分项评分及整体结果 |
| WP8.5 Result Storage | 保存模型、题目、Benchmark 版本、运行配置和评测结果关系 |
| WP8.6 Leaderboard Data | 生成可供内部或公开 Leaderboard 使用的结果数据 |
| WP8.7 Error Analysis | 支持按模型、能力、题目、难度、来源和错误类型进行分析 |
| WP8.8 Benchmark Reporting | 形成可重复生成的 Benchmark Report 和版本报告 |

OpenCompass、VLMEvalKit 等属于候选实现方案。本 Project Plan 不提前正式决定唯一评测框架；具体选择由 Evaluation Specification、System Architecture 和后续技术评审共同确定。

### Deliverables

- 工程化 Evaluation Runner；
- Text / Calculation Evaluation Runner；
- Multimodal Evaluation Runner；
- 自动评分和分项评分结果；
- Result Storage / Result Manifest；
- Leaderboard 数据输出；
- 错误分析结果；
- Benchmark Report；
- 评测运行和复现说明。

### Acceptance Criteria

- 评测可以按 Benchmark 版本、模型标识、运行配置和结果版本重新运行；
- 能够输出模型整体分数以及 Knowledge、Calculation、Multimodal 分项评分；
- 结果可追溯到具体 Benchmark、题目、模型和运行记录；
- 评测失败、不支持的模型或缺失输入被显式记录；
- Result Storage、Leaderboard 数据和 Benchmark Report 的来源关系清晰；
- 错误分析可以定位到题目、能力维度或质量问题；
- 评测和报告结果具备基本复现条件；
- 具体框架选择没有被本 Project Plan 擅自锁死。

### Required Resources

- 文本 LLM 和多模态 LLM 的运行适配资源；
- Evaluation Runner 工程化能力；
- 自动评分、分项评分和结果分析能力；
- 结果存储、版本管理和报告生成能力；
- 必要的模型运行预算、计算资源和维护人员；
- Benchmark、评测和机械领域质量审核资源。

### Dependencies

- Gate 7 - Benchmark V1 Dataset Readiness Review 通过；
- Benchmark V1、Evaluation Specification 和 Version Manifest 可用；
- Phase 5 / Phase 6 的最小评测路径和结果记录可供工程化；
- 模型运行条件、结果存储和报告发布边界已确认。

### Risks

- 不同模型接口、输入格式或多模态能力导致运行结果不可比；
- 自动评分或结果存储与 Benchmark 版本脱节；
- Leaderboard 或报告暴露 Test Set，增加 Benchmark contamination；
- 评测框架选型过早锁定，限制后续扩展；
- 维护和复现成本高于预期。

### Exit Gate

**Gate 8 - Benchmark V1 Release Readiness Review**：综合检查以下内容：

- Benchmark V1 Dataset；
- Evaluation Runner；
- Automatic Scoring；
- Result Storage；
- Reproducibility；
- Reporting；
- Leaderboard readiness（如适用）；
- Public / Private Split；
- Copyright / Data Usage Constraints；
- Release documentation。

Gate 8 才决定 Benchmark 是否满足正式内部使用或对外发布的完整条件。具体实现框架和公开发布方式仍以专项设计和项目决策为准。

## 13. Cross-cutting Workstreams

以下工作流贯穿所有 Phase，不属于某一个 Phase 的一次性交付：

| Workstream | 全生命周期要求 |
| --- | --- |
| Data Governance | 管理数据状态、访问边界、使用目的、责任和变更记录 |
| Source Provenance | 保持 source document、page、原始内容和必要 region / bbox 的追溯链路 |
| Contamination Control | 进行题目级、来源级和 document-family 级别的重复与训练污染控制 |
| Quality Assurance | 定义检查、审核、抽检、异常处理和质量报告机制 |
| Reproducibility | 保存输入、版本、配置、运行记录和结果，使关键流程能够重新运行 |
| Versioning | 管理 Charter、Taxonomy、Schema、题目、Ground Truth、评测和报告版本 |
| Cost / Resource Tracking | 记录访问、计算、模型调用、人工审核和存储等资源消耗 |
| Copyright / Data Usage Constraints | 持续记录版权、内部保密、外发限制和 CPT / SFT 使用边界，不假设 70,000 份 PDF 可以公开 |

横向工作流的验收证据应在对应 Phase 的 Deliverables 或 Gate Review Record 中体现。

## 14. Stage Gates

### 14.1 Gate 清单

| Gate | Review | 决策 |
| --- | --- | --- |
| Gate 0 | Benchmark Design Review | 决定是否进入 Corpus Inventory |
| Gate 1 | Corpus Inventory Review | 决定是否具备设计 Source Selection 的数据基础 |
| Gate 2 | Taxonomy & Source Corpus Review | 决定是否允许对选定来源进行大规模解析 |
| Gate 3 | Corpus Processing Review | 决定解析质量是否足够支持出题 |
| Gate 4 | Candidate Benchmark Review | 决定是否进入 Pilot |
| Gate 5 | Pilot Quality Review | 决定是否进行正式模型验证 |
| Gate 6 | Pilot Validation Review | 决定是否扩展 Benchmark V1 |
| Gate 7 | Benchmark V1 Dataset Readiness Review | 确认 Benchmark V1 Dataset 达到冻结候选状态，并可进入正式 Evaluation & Reporting 工程化；不表示正式公开发布 |
| Gate 8 | Benchmark V1 Release Readiness Review | 综合决定 Benchmark 是否满足正式内部使用或对外发布的完整条件 |

Gate 8 是为 Phase 8 的生命周期闭环增加的最终发布就绪检查，不改变 Gate 0 至 Gate 6 的项目决策含义。

### 14.2 Gate 通用规则

- Gate 评审必须有明确输入、评审证据、结论、未决问题和责任记录。
- Gate 通过可以附带受控条件，但条件必须有后续跟踪记录。
- Gate 未通过时，优先修复当前阶段问题，不继续向后堆数据。
- 未通过 Gate 不得以“先做一部分下一阶段工作”替代当前阶段的修复，除非项目评审明确批准并记录例外。
- Gate 结论不得把 TBD 问题自动解释为已解决。

## 15. Resource Requirements Matrix

本矩阵只说明各阶段需要的资源类型，不填写具体机器配置、型号、数量、日期或工期估算。具体资源可用性和限制应在进入对应 Phase 前确认。

| Phase | 主要资源类型 | 资源说明 |
| --- | --- | --- |
| Phase 0 - Benchmark Design | 项目设计、Benchmark 方法分析、文档评审 | 需要项目成员、领域方法分析和跨文档一致性评审能力 |
| Phase 1 - Corpus Inventory | Candidate Source Corpus 访问权限、文件扫描环境、CPU、RAM、磁盘、服务器信息 | 需要 70,000 份 PDF 的实际访问方式、目录结构、服务器 OS、可用空间及数据使用限制；GPU 和 Docker 按实际情况确认 |
| Phase 2 - Taxonomy Calibration & Source Selection | Domain Taxonomy 设计、机械领域专家、Corpus Statistics、Data Governance、版权审查 | 需要依据真实 Inventory 校准 Taxonomy，并对 Benchmark Source Corpus、document-family 和训练隔离进行评审 |
| Phase 3 - Corpus Processing | 解析工具环境、CPU / GPU、较大存储、技术评估和质量审核 | 需要对 Representative Sample 和 Benchmark Source Corpus 进行结构化处理，并保持 Source Provenance |
| Phase 4 - Question Construction & Ground Truth | LLM API 或本地模型、Python 计算环境、源资料访问、视觉审核、机械领域专家 | LLM 可作为候选生成和辅助审核资源；计算题和多模态题需要对应的验证资源 |
| Phase 5 - Quality Control & Pilot Benchmark | 自动质量检查、人工审核、机械专家、视觉审核、最小 Evaluation Runner、模型访问 | 需要完成约 500 道 Pilot Benchmark 的筛选、审核、污染检查和可运行性准备 |
| Phase 6 - Model Validation & Calibration | 多个不同能力层级模型、Evaluation Runner、结果存储、分析人员、运行预算、专家复核 | 需要支持 Model × Item 分析；Baseline / Anchor Models 仍为 TBD |
| Phase 7 - Benchmark V1 Expansion | 可扩展的来源处理、候选构建、Ground Truth 验证、质量控制、版本和存储资源 | 需要沿用 Pilot 验证过的流程，支持约 3,000～5,000 道 Benchmark V1 的质量扩展 |
| Phase 8 - Evaluation & Reporting | Runner 工程化、模型适配、自动评分、结果存储、报告和 Leaderboard 能力 | 需要把 Pilot 的最小评测路径标准化；OpenCompass、VLMEvalKit 等具体框架仍由后续设计决定 |

全项目还需要持续的 Data Governance、Source Provenance、Contamination Control、Quality Assurance、Reproducibility、Versioning、Cost / Resource Tracking 和 Copyright / Data Usage Constraints 资源。

## Decision Points / Unresolved Decisions

以下决策当前仍未正式确定。除明确写明的初始设计外，本表不构成最终方案：

| Decision | Current Status | Initial Design Stage | Resolution / Validation Stage | Must Be Resolved Before | Notes |
| --- | --- | --- | --- | --- | --- |
| Domain Taxonomy | TBD | Phase 0 - Benchmark Taxonomy v0.1 | Phase 2 - Taxonomy Calibration | Gate 2 | Phase 0 建立理论设计，Phase 2 根据 Corpus Inventory 校准。 |
| Knowledge / Calculation / Multimodal 比例 | 40% / 30% / 30% 为初始设计，非最终决定。 | Phase 0 | Phase 5 / Phase 6 | Benchmark V1 Expansion | 根据 Pilot 结果验证并决定是否调整。 |
| Pilot / V1 Dataset Size | Pilot ≈ 500，V1 ≈ 3,000–5,000 为初始目标。 | Phase 0 | Phase 6 | Phase 7 final assembly | 根据 Pilot 结果确认规模是否需要调整。 |
| Benchmark Source Corpus Selection | TBD | Phase 0（仅定义 Candidate Source Corpus 边界） | Phase 2 | Gate 2 | 根据 Inventory、质量、覆盖和污染风险完成选择。 |
| Benchmark Corpus / CPT-SFT Corpus Isolation Strategy | TBD | Phase 0 Data Specification / System Architecture | Phase 2 | Benchmark Source Corpus 正式确定 | 需要在来源正式确定前形成可执行的隔离策略。 |
| Public Dev / Private Test / Full Public | TBD | Phase 0（保留为未决） | Phase 7 | 最终 Benchmark Release | 公开范围和 Test Set 形态不在当前阶段假设。 |
| Evaluation Framework | TBD | Phase 0 Evaluation Specification | Minimum Implementation Decision: Phase 5 前；Engineering Finalization: Phase 8 | Phase 5 前（最小可用）；Phase 8（工程化） | Candidate: OpenCompass / VLMEvalKit / custom runner 等；不要现在选择具体框架。 |
| Human Expert Review Resources | TBD | — | Phase 4 前资源确认 | Phase 4 Question Construction | Ground Truth 和质量控制策略会依赖可用的专家资源。 |
| Ground Truth Strategy Under Limited Expert Availability | TBD | Phase 0 Data Specification / Pilot Design | Phase 4 前形成可执行方案 | Phase 4 | 在专家资源有限时仍需建立可靠验证链路。 |
| Baseline / Anchor Models | TBD | — | Phase 6 开始前 | Phase 6 开始前 | 不在当前阶段指定具体模型。 |
| Benchmark Public Release | TBD | — | Phase 7 / Phase 8 | Gate 8 - Benchmark V1 Release Readiness Review | 由 Gate 8 决定正式内部使用或对外发布的完整条件。 |
| Benchmark Version Refresh / Contamination Mitigation | TBD | Phase 8 或 V1 Release 前定义 | Phase 8 / V1 Release Readiness | Benchmark V1 Release | 不擅自给出最终更新频率，需结合 Benchmark contamination 风险确定。 |
