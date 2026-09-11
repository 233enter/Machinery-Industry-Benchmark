# Mechanical Industry General Benchmark Data Specification v0.1

## 文档信息

| 项目 | 内容 |
| --- | --- |
| Project | Mechanical Industry General Benchmark |
| Document | Data Specification |
| Version | 0.1 |
| Status | Reviewed - Baseline |
| Phase | Phase 0 - Benchmark Design |
| Current Task | Data Specification v0.1 |

## 1. Data Specification 的定位

本文件定义一条 Benchmark 数据，以及它依赖的 Source Document、Source Evidence、Visual Asset、Ground Truth、Verification、Quality 和 Dataset Version 信息应该如何被机器稳定表示。

本文件回答的是：

> 一条 Benchmark 数据，以及它依赖的 Source / Evidence / Asset / Ground Truth / Verification 信息，应该如何被机器稳定表示？

本文件是一个 model-agnostic 的逻辑数据契约，不绑定 OpenAI、GLM、Qwen、Claude、Gemini 或其他任何模型的对话格式。后续 Evaluation Adapter 负责把 Canonical Benchmark Item 转换成具体模型所需的输入格式。

本文件不是：

- PDF Parser Specification；
- Database Design；
- Evaluation Framework Specification；
- SFT Data Format；
- ChatML Format；
- 某个模型 API 的 Request Format。

最终数据库是否拆表、是否使用 JSONL / Parquet / relational database，以及如何组织文件和服务接口，由 System Architecture 决定。本文件只定义跨实现的逻辑实体、字段语义、关联关系和验证边界。

## 2. Data Specification v0.1 的设计目标

Data Specification v0.1 应保证：

1. Benchmark Taxonomy v0.1 的 Domain、Track、Capability、Task、Modality、Difficulty 和 Answer Type 可以被表达；
2. Ground Truth 可以被验证，并能区分不同 Answer Type；
3. Source Provenance 可以从 Item 回溯到 Evidence、Page、原始文本/公式/表格/图片和必要的 bbox；
4. Mechanical Knowledge、Engineering Calculation、Multimodal Understanding 三类 Track 可以由同一套逻辑契约表示；
5. Candidate → Pilot Benchmark → Benchmark V1 的 Dataset Membership 可以被管理；
6. 数据修改具有 item revision、schema version 和 dataset version 记录；
7. 题目构建过程可审计，并能区分人工、模板、参数化和 LLM 辅助来源；
8. Verification 和 Quality 状态可以记录，而不是只保存一个 human_checked 布尔值；
9. 数据污染、完全重复、近重复和 document-family 关系可以记录；
10. 数据可以执行机器 Schema Validation 和 Cross-field Validation；
11. 内部证据与未来可能公开的数据可以通过可见性和导出控制分离；
12. 数据契约不依赖具体存储数据库、模型 API 或评测框架。

## 3. 数据范围与核心边界

### 3.1 逻辑数据范围

本规范覆盖以下逻辑对象及其关联：

- Candidate Source Corpus 中的 Source Document；
- Source Document 的 Source Evidence；
- 从 Evidence 构建或独立设计的 Benchmark Item；
- Item 的 Ground Truth；
- Verification Records；
- Quality、Contamination、Duplicate 和 Visibility Metadata；
- Candidate、Pilot Benchmark、Benchmark V1 的 Dataset Membership 和 Version 信息。

70k PDFs != Benchmark。Candidate Source Corpus 中的 PDF 不是默认的 Benchmark 数据；只有经过后续 Inventory、Deduplication、Classification、Quality Assessment 和 Source Selection 的资料，才可能进入 Benchmark Source Corpus 并被用于构题。

### 3.2 逻辑契约而非实现

本文件中的 Object、Array、Enum、Required、Conditional Required 和 Optional 都是逻辑层约束，不等同于 Python Class、Pydantic Model、JSON Schema、数据库表或某种序列化实现。

### 3.3 Required 状态定义

| Required 状态 | 含义 |
| --- | --- |
| Required | 所有符合该层级的 Item 都必须提供；缺失即不能通过对应 Schema Validation |
| Conditional Required | 满足指定条件时必须提供；不满足条件时可以不出现或为 null，具体规则见本文件 |
| Optional | 可以提供但不是当前版本的最低要求；若提供仍必须符合字段语义 |

## 4. Logical Entity Model

本项目不能把数据理解成只有 question 和 answer 的扁平 QA：

~~~text
Source Document
       ↓
Source Evidence
       ↓
Benchmark Item
       ↓
Ground Truth
       ↓
Verification
       ↓
Quality / Review
       ↓
Dataset Version / Release
~~~

视觉数据还需要：

~~~text
Source Document
       ↓
Visual Asset
       ↓
Source Evidence
       ↓
Benchmark Item
~~~

这些是 Logical Entities。它们最终是否拆成独立表、独立文件、对象存储对象或服务资源，由 System Architecture 决定。

### 4.1 Logical Entity 说明

| Logical Entity | 作用 | 关键关系 |
| --- | --- | --- |
| Source Document | 描述一个候选或已选择的源文档及其元数据 | 一个 Source Document 可以对应多个 Source Evidence |
| Source Evidence | 描述题目所依赖的原始文本、公式、表格、图片、页面或局部区域 | 一个 Benchmark Item 可以引用一个或多个 Source Evidence |
| Visual Asset | 描述供模型输入的图像、图纸、表格图、曲线或其他视觉资产引用 | Visual Asset 可以由 Source Document 产生，并被 Item 通过 Asset Reference 使用 |
| Benchmark Item | 可被评测的最小规范化题目单元 | 关联 Question、Taxonomy、Ground Truth、Provenance、Verification 和 Quality |
| Ground Truth | 描述该 Item 的规范答案及其类型化结构 | 由 answer_type 进行 discriminated structure 分派 |
| Verification Record | 记录一次 Schema、Source、Ground Truth、程序、视觉或人工核验 | 一个 Item 可以有多个 Verification Record |
| Quality Metadata | 记录歧义、来源质量、答案可信度、重复、污染和审核状态 | 不等同于模型 Score |
| Dataset Membership | 记录 Item 是否进入 Candidate、Pilot 或 Benchmark V1 及其版本 | 一个 Item 可以在不同 revision 或 dataset version 中具有不同成员关系 |
| Evaluation Result | 记录模型运行结果、分数和运行信息 | 不写回 Canonical Benchmark Item，通过 Item ID、Revision 和 Dataset Version 关联 |

## 5. Canonical Benchmark Item

### 5.1 概念结构

Canonical Benchmark Item 是与模型无关的规范化内部 Item。其概念结构至少包括：

~~~text
item_id
schema_version
item_revision
item_status
content_hash

taxonomy
question
inputs / assets
answer_type
ground_truth
answer_requirements
source_provenance
construction
calculation
multimodal
verification
quality
governance
dataset_memberships[]
timestamps
~~~

calculation 和 multimodal 是条件结构：不满足适用条件时可以不提供；若提供则必须满足本规范的专项约束。

### 5.2 Canonical Benchmark Item 顶层字段表

| Field | Type | Required | Description | Constraints |
| --- | --- | --- | --- | --- |
| item_id | string | Required | 稳定的 Item 标识 | 不得直接编码 Domain、Track 或 Capability；同一逻辑 Item 跨 revision 保持稳定 |
| schema_version | string | Required | Data Specification / Schema 版本 | 例如 0.1；必须能识别 Item 使用的 Schema |
| item_revision | integer | Required | 同一 Item 内容修订号 | 从 1 开始递增；关键内容修改不得复用旧 revision |
| item_status | enum | Required | Item 生命周期状态 | 使用第 7 节定义的状态；rejected 和 deprecated 有额外约束 |
| content_hash | string | Optional（recommended） | Item 规范内容的内容哈希 | 用于修改检测、一致性和审计；算法由 System Architecture 决定 |
| taxonomy | object | Required | Domain、Track、Capability、Task、Difficulty 等分类 | 必须符合第 8 节及 Taxonomy v0.1 的语义 |
| question | object | Required | 给模型看到的问题内容 | 不得混入 Ground Truth、Evidence 或 Verifier Notes |
| inputs | object | Required | 输入形式和 Asset Reference 容器 | 至少含 primary_modality；T3 需要 Visual Asset |
| answer_type | enum | Required | Ground Truth 的判别类型 | 必须是第 14 节定义的类型之一 |
| ground_truth | discriminated object | Required | 与 answer_type 对应的类型化答案 | 不允许把所有答案都保存为无类型的 answer 字符串 |
| answer_requirements | object | Conditional Required | 模型答案的表达要求 | numeric Item 至少提供 numeric_unit_policy；不改变 Canonical Ground Truth |
| source_provenance | object | Required | Item 的来源类型和 Evidence 引用 | Source-grounded Item 至少引用一个有效 Evidence |
| construction | object | Required | Item 如何构建、转换或生成 | 不保存 API Key、Token、Secret 或整份 Source PDF |
| calculation | object | Conditional Required | 公式、变量、约束和计算核验信息 | T2 以及 T3 中包含定量计算的 Item 应提供 |
| multimodal | object | Conditional Required | 视觉依赖和相关区域信息 | primary_benchmark_track = T3 时必须提供并满足第 18 节 |
| verification | array[object] | Required | Verification Records 集合 | 一个 Item 可以有多个不同类型的记录 |
| quality | object | Required | 质量、重复、污染和审核状态摘要 | 未执行的检查必须使用 not_checked 等明确状态 |
| governance | object | Required | 可见性、重复、污染、拒绝/替代和治理信息 | 不能因缺少版权信息而默认为可公开 |
| dataset_memberships | array[object] | Optional / Conditional Required | Candidate、Pilot、Benchmark V1 的成员关系历史 | Item 被分配到某 collection 时必须提供相应 Membership；历史 Membership 不覆盖 |
| timestamps | object | Required | 创建、更新、验证和发布时点 | 使用 ISO 8601；verified_at / released_at 可以为空 |

### 5.3 字段命名边界

- answer_type 是顶层判别字段，ground_truth 必须与其一致；
- taxonomy.primary_benchmark_track 是一级评测分区，不使用 Modality 替代；
- question 只保存实际给模型的问题内容；
- Source Provenance、Verification、Quality 和内部审核说明不放进 question；
- Evaluation Result 不放进 Canonical Benchmark Item；
- source_provenance 与 construction 可以同时存在：前者回答“依据什么来源”，后者回答“如何构建”。

## 6. Item Identity & Versioning

### 6.1 item_id

item_id 是稳定 Item ID。例如：

~~~text
MIGB-000001
~~~

item_id 不应直接包含 Domain、Track、Capability、Task 或其他可能变化的 Taxonomy 信息。

错误示例：

~~~text
MIGB-D03-T2-C3-0001
~~~

原因是 Taxonomy 可能在 v0.2 或之后发生重命名、合并、拆分或映射变化，而 Item 的身份不应因此变化。

### 6.2 schema_version

schema_version 表示该 Item 遵循的 Data Specification / Schema 版本，例如 0.1。它不同于 taxonomy_version：前者描述数据契约，后者描述 Item 所使用的 Taxonomy。

### 6.3 taxonomy_version

taxonomy_version 位于 taxonomy 对象中，表示该 Item 使用哪个 Taxonomy，例如 0.1。Released Item 必须保留该值，以便解释历史标签。

### 6.4 item_revision

item_revision 表示同一个 item_id 的内容修订号：

~~~text
MIGB-000001 / revision 1
MIGB-000001 / revision 2
MIGB-000001 / revision 3
~~~

如果 Question、Ground Truth、Source Provenance、Answer Type、关键 Taxonomy、视觉依赖或验证结论发生实质性变化，必须产生新的 revision。Released Item 不允许静默覆盖历史内容。

### 6.5 content_hash

建议保留 content_hash，用于：

- 检测 Item 内容是否被修改；
- 检查导入、导出和复制过程中的一致性；
- 支持版本审计和重复检测。

具体哈希算法、规范化顺序和是否包含内部字段，由 System Architecture 决定。

## 7. Item Lifecycle Status

### 7.1 候选状态集合

初始状态集合如下：

~~~text
draft
candidate
accepted
rejected
deprecated
~~~

这里的 `item_status` 只表示 Item Lifecycle，不表示 Verification State，也不表示 Dataset Membership 或 Dataset / Release State：

~~~text
Item Lifecycle != Verification State != Dataset Membership
~~~

自动校验、来源核验、Ground Truth 核验和质量检查等状态分别记录在 Verification Records 与 Quality Metadata 中；Item 是否进入 Candidate、Pilot Benchmark 或 Benchmark V1 由 `dataset_memberships[]` 表达；Dataset 或 Release 的冻结、候选和发布状态由相应 Dataset / Release State 表达。

### 7.2 状态语义

| Status | 含义 |
| --- | --- |
| draft | 尚在编辑或构题阶段，尚未作为候选 Item 接收 |
| candidate | 已进入候选池，但尚未完成全部来源、答案或质量核验 |
| accepted | 满足当前 Quality Policy，可以参与 Dataset Assembly；不代表已经进入 Pilot Benchmark 或正式发布 |
| rejected | 当前 Item 不应进入后续数据集或发布流程 |
| deprecated | 历史 Item 不再推荐使用，但保留历史记录和替代关系 |

Item 不要求机械地经过每一个状态。实际状态跃迁取决于阶段、Quality Policy 和项目 Gate，但任何跃迁都应可审计。

rejected 必须带有 governance.rejection_reason。Deprecated Item 应保留历史记录，并在适用时保留 replacement relation：

~~~text
replacement_item_id
replacement_revision
~~~

## 8. Taxonomy Schema

Data Specification 将 Benchmark Taxonomy v0.1 映射为机器可表示字段，但不重新定义 Domain、Capability 或 Task 的专业语义。

~~~text
taxonomy:
  taxonomy_version
  primary_domain
  secondary_domains
  primary_benchmark_track
  primary_capability
  secondary_capabilities
  task
  cross_cutting_skill_tags
  design_difficulty
  empirical_difficulty
~~~

### 8.1 primary_domain

primary_domain 为 Required，至少包含：

~~~text
primary_domain:
  level1_id
  level1_name
  level2_id
  level2_name
~~~

Level 2 是否由独立 Taxonomy Registry 正式分配 stable ID，可在后续决定；但 Data Specification 不允许只保存 display name。level2_id 字段必须存在，Candidate 阶段可以暂时为 null 并进入待处理状态；在进入 Pilot 或 Released 范围前，应有可追踪的 stable identifier。

一个 Item 只能有一个 Primary Domain。Domain 应依据题目真正考查的机械专业知识对象确定，不能由输入形式、图片类型、PDF 章节或 Question wording 机械推导。

### 8.2 secondary_domains

secondary_domains 是 Optional list。本 v0.1 正式允许它表达确有跨领域知识依赖的问题，但：

- Primary Domain 仍只能有一个；
- Secondary Domain 默认不参与一级 Benchmark Score；
- 不能仅因为某个 Domain“可能相关”就滥用该字段；
- Secondary Domain 的最大数量是否限制，留在 Open Questions；
- 最终字段 ID 和名称必须与 Taxonomy Registry / Taxonomy Version 一致。

### 8.3 primary_benchmark_track

primary_benchmark_track 为 Required，只允许：

~~~text
T1
T2
T3
~~~

每个 Item 只能有一个 primary_benchmark_track，并遵循 Taxonomy v0.1 的 visual dependency 优先规则：需要视觉证据时进入 T3；不需要视觉证据且主要目标为定量工程计算时进入 T2；否则进入 T1。

### 8.4 primary_capability

primary_capability 为 Required，至少包含 capability ID 和 display name，并且必须与 Primary Track 对应：

~~~text
T1 → K1–K8
T2 → C1–C8
T3 → M1–M11
~~~

Schema Validation 必须能够检查这种一致性，不能出现 T3 + C3 作为 Primary Capability 的组合。

### 8.5 secondary_capabilities

secondary_capabilities 是 Optional list。本 v0.1 允许它表达复合任务，但：

- 不改变 primary_benchmark_track；
- 默认不参与一级 Benchmark Score；
- 不允许与 primary_capability 重复；
- 例如 T3 / M9 的图纸计算 Item 可以记录 M8；
- 最大数量和最终计分关系留给后续设计。

### 8.6 task

task 为 Required，引用可扩展 Controlled Vocabulary，至少包含：

~~~text
task:
  task_id
  task_name
~~~

正式 Task Registry 后续逐步扩展。Task 不应重复承担 Domain 的职责，Task ID 的重命名、废弃和兼容规则由 Taxonomy Governance 管理。

### 8.7 cross_cutting_skill_tags

cross_cutting_skill_tags 在 Data Specification v0.1 中作为 Optional / Non-scoring Metadata 正式提供。初始允许值为：

~~~text
calculation
reasoning
diagnosis
selection
compliance
spatial_reasoning
information_extraction
~~~

它们用于辅助分析和复合任务描述，不能代替 Track 或 Capability。Controlled Vocabulary 是否需要独立治理、如何扩展和是否允许更多标签，仍保留为 Open Question。

### 8.8 Difficulty fields

design_difficulty 为 Required，枚举为：

~~~text
easy
medium
hard
~~~

empirical_difficulty 在 Phase 0 / Candidate 阶段为 Optional / null；Phase 6 完成 Pilot 模型验证后可以填写。其计算规则不在本文件定义。

## 9. Question Schema

~~~text
question:
  language
  stem
  instructions
  options
~~~

### 9.1 language

Required。建议使用标准语言代码，例如：

~~~text
zh-CN
en
~~~

具体枚举可扩展。

### 9.2 stem

Required。只保存实际给模型的问题内容，不保存：

- Ground Truth；
- Source Evidence；
- Verifier Notes；
- 内部审核意见；
- 模型专属 system prompt。

### 9.3 instructions

Optional。只保存该题本身对回答格式或必要操作的要求，例如要求给出单位、选择一个选项或返回有限结构化字段。不得保存模型专属 system prompt。

### 9.4 options

当 answer_type 为 single_choice 或 multiple_choice 时 Conditional Required。每个 Option 使用稳定的：

~~~text
option_id
content
~~~

例如：

~~~json
{
  "option_id": "opt_1",
  "content": "..."
}
~~~

不要把 A / B / C / D 作为 Ground Truth 的唯一身份。未来可以 shuffle options 或改变展示顺序，Display label 应由 Evaluation Adapter 生成。

## 10. Input / Asset Schema

多模态输入不直接以 base64 塞进 Benchmark Item。Item 保存逻辑 Asset Reference，文件本身由数据资产层保存。

~~~text
inputs:
  primary_modality
  assets[]
~~~

### 10.1 primary_modality

Required。可使用 Taxonomy v0.1 的概念值，例如：

~~~text
text
text_formula
text_table
mechanical_drawing
part_drawing
assembly_drawing
schematic_diagram
process_diagram
table_image
chart_curve
technical_illustration
equipment_photo
cad_render_or_screenshot
multi_image
~~~

primary_modality 描述输入形式，不决定 Benchmark Track。一个 Item 可以有多个 modality，但必须指定一个 Primary Modality。

### 10.2 Asset Reference

每个 Asset 至少考虑：

~~~text
asset_id
asset_type
visual_type
role
storage_reference
checksum
source_evidence_id
~~~

asset_type 候选值：

~~~text
image
table
chart
drawing
other
~~~

visual_type 使用 Taxonomy v0.1 的视觉类型，例如 mechanical_drawing、assembly_drawing、table_image、chart_curve、multi_view_drawing 等。多个图像输入由 `primary_modality = multi_image` 表达；单一 Asset 的 `visual_type` 不承担多图输入语义。

对于 Source-derived Asset，source_evidence_id 为 Conditional Required；人工控制题或没有直接视觉来源的 Asset 可以不提供，但必须在 source_provenance 中说明来源类型。

### 10.3 二进制数据边界

- Canonical Benchmark Item 只保存 Asset Reference；
- 二进制文件、裁剪图、原始 PDF 页面和渲染结果由数据资产层管理；
- 不默认将原始 PDF 页面或图片公开；
- storage_reference 的实际格式、对象存储和访问权限由 System Architecture 决定。

## 11. Source Document Schema

Source Document 是 Candidate Source Corpus 或 Benchmark Source Corpus 中一个文档的最小元数据实体。

### 11.1 最小字段

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| document_id | string | Required | 稳定的 Source Document 标识 |
| document_family_id | string / null | Optional（strongly recommended） | 标记同一本书不同版本、扫描版/文本版、重印版或同资料不同来源 |
| source_type | enum | Required | Source Type 元数据，而非 Taxonomy |
| title | string / null | Optional | 文档标题 |
| authors | array[string] / null | Optional | 作者或编制者 |
| publisher | string / null | Optional | 出版者、发布机构或来源机构 |
| publication_year | integer / null | Optional | 出版或发布年份；未知时为空 |
| edition | string / null | Optional | 版本、版次或重印信息 |
| language | string / null | Optional | 文档语言 |
| standard_number | string / null | Optional | 标准号或规范编号 |
| isbn | string / null | Optional | ISBN（如适用） |
| file_hash | string / null | Optional（recommended） | 文件级哈希，用于重复和一致性检查 |
| source_locator | string / object | Conditional Required | 当前可访问的路径、URI 或外部来源引用 |
| rights_status | enum | Required | 当前已知的使用/发布状态，不作法律判断 |
| usage_constraints | string / object / null | Optional | 已知的内部使用、外发或版权限制说明 |

### 11.2 document_id

document_id 是稳定标识，既适用于 Candidate Source Document，也适用于进入 Benchmark Source Corpus 的 Source Document。它不应随着文件路径变化而变化。

### 11.3 document_family_id

document_family_id 用于 document-family 级别的去重和污染控制，尤其覆盖：

- 同一本书不同版本；
- 扫描版与文本版；
- 重印版；
- 同一资料不同来源；
- 高度重复但文件哈希不同的资料。

Phase 1 可能只能部分识别，因此允许 null / unknown。未知不等于不存在，也不能因此跳过后续 contamination review。

### 11.4 source_type

Source Type 属于 Metadata / Data Governance，不属于 Taxonomy。Controlled Vocabulary 候选值为：

~~~text
textbook
handbook
standard
specification
manual
paper
technical_report
training_material
exam_material
catalog
unknown
~~~

### 11.5 rights_status

不要在此字段中做法律结论，只记录当前已知状态：

~~~text
unknown
internal_use_only
redistribution_restricted
redistribution_allowed
needs_review
~~~

未来公开 Benchmark 时，必须重新审核 Source Document、Evidence 和 Asset 的实际使用约束。

## 12. Source Evidence Schema

Source Evidence 是本项目 Source Provenance 的核心实体。一条 Benchmark Item 可以引用一个或多个 Evidence。

### 12.1 字段

~~~text
evidence_id
document_id
page_index
printed_page_label
evidence_type
bbox
text_reference
asset_reference
content_hash
visibility
~~~

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| evidence_id | string | Required | 稳定的 Evidence 标识 |
| document_id | string | Required | 所属 Source Document |
| page_index | integer | Required | PDF 文件中的物理页序号，采用 1-based |
| printed_page_label | string / null | Optional | 原书印刷页码或页面标签，例如 328 |
| evidence_type | enum | Required | Evidence 的内容类型 |
| bbox | object / null | Conditional Required | Evidence 只来自页面局部区域时使用 |
| text_reference | string / object / null | Conditional Required | 原始文本、公式或文本区域的引用 |
| asset_reference | string / object / null | Conditional Required | 原始图片、表格、曲线或图纸的引用 |
| content_hash | string / null | Optional（recommended） | Evidence 内容哈希 |
| visibility | enum | Required | 内部审核与未来导出的可见性 |

### 12.2 page_index

统一定义为 PDF 文件中的物理页序号，建议采用 1-based：

~~~text
PDF 第一页 → page_index = 1
~~~

它不能与书籍的印刷页码混用。原书页码记录在 printed_page_label。

### 12.3 bbox

当 Evidence 来源于页面局部区域时，bbox 为 Conditional Required。至少包括：

~~~text
bbox:
  x0
  y0
  x1
  y1
  coordinate_system
  origin
  page_width
  page_height
~~~

允许的 coordinate_system 候选值：

~~~text
normalized_0_1
pixel
pdf_point
~~~

内部处理可以保留 parser-native 坐标，但所有坐标必须同时明确 coordinate_system、origin 和页面尺寸。不得只保存 [123, 45, 500, 600] 而不说明坐标含义。

### 12.4 evidence_type

候选值：

~~~text
text
formula
table
figure
drawing
chart
page
mixed
~~~

### 12.5 visibility

用于区分内部审核证据与未来可能公开的数据：

~~~text
internal
exportable
withheld
~~~

从 PDF 提取的 Evidence 不默认可公开。

## 13. Source Provenance

Benchmark Item 不复制整份 Source Document，而是通过引用建立：

~~~text
Benchmark Item
     ↓
Evidence ID
     ↓
Document ID
     ↓
Page
     ↓
BBox / Original Object
~~~

### 13.1 Item-level Provenance

~~~text
source_provenance:
  source_provenance_type
  evidence_refs[]
  primary_evidence_id
~~~

其中：

- source_provenance_type 为 Required；
- evidence_refs 支持一个 Item 引用多个 Evidence；
- primary_evidence_id 在存在主要依据时提供；
- Source-grounded Item 至少有一个 Evidence Reference；
- 非来源构题也必须记录 Provenance 类型，而不是留空。

### 13.2 source_provenance_type

初始候选值：

~~~text
source_grounded
parameterized_from_source
human_authored
synthetic_control
~~~

V1 应优先使用可验证来源。human_authored 或 synthetic_control 不代表质量更低或更高，但必须明确与 Source-grounded Item 的差异。

## 14. Ground Truth Schema

Ground Truth 必须采用 discriminated structure。不能所有答案都保存为：

~~~json
{
  "answer": "42"
}
~~~

Canonical discriminator 是顶层 answer_type，而 ground_truth 必须与其一致。

`Ground Truth = Canonical Scoring Truth`。每个 Item 对评分使用的规范真值只能有一份；解释、公式、变量、参数、约束、中间结果和验证方法可以作为审计与复现信息保存，但不能在其他字段中再定义一份相互独立的评分真值。

### 14.1 single_choice

~~~text
answer_type: single_choice

ground_truth:
  correct_option_id
~~~

不要把 A 作为唯一的 Canonical Ground Truth；正确身份应引用稳定的 option_id。

### 14.2 multiple_choice

~~~text
answer_type: multiple_choice

ground_truth:
  correct_option_ids[]
~~~

correct_option_ids 至少包含一个有效 Option ID，展示顺序不承担身份语义。

### 14.3 true_false

~~~text
answer_type: true_false

ground_truth:
  value: true / false
~~~

Canonical value 使用布尔值，不使用“对”“正确”“True”等混乱表示。展示语言由 Evaluation Adapter 处理。

### 14.4 numeric

至少包括：

~~~text
answer_type: numeric

ground_truth:
  value
  unit
  dimensionless
  absolute_tolerance
  relative_tolerance
  rounding_rule
  accepted_unit_conversions
~~~

规则：

- 有物理单位时必须有 unit；
- 无物理单位时必须显式 dimensionless = true；
- unit 和 dimensionless 必须能够明确区分；
- absolute_tolerance 和 relative_tolerance 可以同时存在；
- 二者如何组合以及实际评分优先级留给 Evaluation Specification；
- accepted_unit_conversions 用于记录允许的等价单位转换，不在本文件定义完整评分算法。

### 14.5 short_answer

至少考虑：

~~~text
answer_type: short_answer

ground_truth:
  canonical_answer
  accepted_aliases
  normalization
~~~

normalization 可记录：

~~~text
case_sensitive
trim_whitespace
unicode_normalization
punctuation_normalization
~~~

具体匹配算法留给 Evaluation Specification。

### 14.6 structured_answer

用于有限结构化工程回答，例如：

~~~text
fault_mode
cause
recommended_action
~~~

至少考虑：

~~~text
answer_type: structured_answer

ground_truth:
  expected_fields
  required_fields
  field_ground_truth
~~~

不得把任意长作文直接塞进 structured_answer。开放式长答案不作为 V1 的主要题型。

### 14.7 answer_requirements

answer_requirements 是 Conditional Field，用于描述模型必须如何表达答案，不改变 Canonical Ground Truth。对于 answer_type = numeric，至少支持：

~~~text
answer_requirements:
  numeric_unit_policy
~~~

numeric_unit_policy 初始允许：

~~~text
unit_specified_in_question
explicit_unit_required
dimensionless
~~~

语义如下：

| numeric_unit_policy | 含义 |
| --- | --- |
| unit_specified_in_question | 题目已指定 Canonical Unit，例如“结果以 N·m 表示”；模型只输出 955 时可以按该单位解释；Ground Truth 仍保存 unit = N·m |
| explicit_unit_required | 题目没有为模型固定唯一输出单位，或明确要求给出单位；模型必须显式提供可兼容单位，例如 955 N·m 或 0.955 kN·m；只输出 955 不能默认猜测单位 |
| dimensionless | 对应 ground_truth.dimensionless = true，不需要单位 |

该字段只定义答案表达要求。评分仍必须使用 Ground Truth 中唯一的 value、unit、dimensionless、absolute_tolerance、relative_tolerance、rounding_rule 和 accepted_unit_conversions。

## 15. Ground Truth Explanation 与内部说明

允许在内部保存：

~~~text
ground_truth_explanation
verification_notes
~~~

这些字段用于人工审计和验证记录，不属于给模型看的 Question 内容。

Benchmark 不要求保存模型式 Chain-of-Thought，也不把完整自然语言 CoT 作为必需字段。对于 Calculation，更推荐保存：

- formula；
- variables；
- constraints；
- deterministic result；
- verification record。

而不是要求保存一段自然语言“思维链”。

## 16. Calculation-specific Schema

对于 T2 Engineering Calculation，以及 T3 中包含定量计算的 Item，允许并通常需要增加：

~~~text
calculation:
  formula_refs
  variables
  constants
  constraints
  intermediate_values
  verification_method
~~~

`calculation` 只承担公式、变量、参数、约束、中间结果、验证方法以及 Audit / Reproducibility 信息。数值评分所需的唯一 `value`、`unit`、`dimensionless`、`absolute_tolerance`、`relative_tolerance`、`rounding_rule` 和 `accepted_unit_conversions` 必须保留在 `ground_truth` 中；`calculation` 不得再定义独立的评分 tolerance。

### 16.1 formula_refs

引用结构化公式，后续可以建立 Formula Registry：

~~~text
formula_ref:
  formula_id
  expression
  source_evidence_id
~~~

source_evidence_id 在公式来源于文档时提供。Formula Registry 是否独立维护属于 Open Question。

### 16.2 variables

每个变量至少考虑：

~~~text
variable:
  symbol
  value
  unit
  role
  source
~~~

role 候选值：

~~~text
given
derived
target
constant
~~~

source 可以指向 Question、Source Evidence、Formula Registry 或参数化生成记录。

### 16.3 constraints

用于记录：

- valid range；
- positivity；
- operating condition；
- standard constraint；
- safety factor；
- rounding constraint；
- measurement/admissibility constraint 或多约束可行性条件。

### 16.4 intermediate_values

Optional。用于程序验证和审计，不要求模型输出这些中间值。

## 17. Parameterized Calculation Items

Data Specification 必须支持从一个 Source Formula / Engineering Relation 生成多个参数化 Item。因此，如适用应记录：

~~~text
template_id
parameter_set_id
random_seed
parameter_generation_version
~~~

同时必须保留原始 Formula / Evidence 的 Source Provenance，避免不同参数生成的题目无法追溯到同一知识来源。

本节只定义需要保留的记录，不实现参数生成器、不规定随机分布、不决定参数取值范围的最终工程策略。

## 18. Multimodal-specific Schema

### 18.1 T3 基本约束

T3 Item 至少满足：

~~~text
taxonomy.primary_benchmark_track = T3
~~~

并且：

- 至少有一个 Visual Asset；
- multimodal.visual_dependency_required = true；
- 视觉信息必须是回答正确不可缺少的 evidence；
- Item 不得仅因“输入中有一张图”就归入 T3；
- 如果视觉信息不是必要证据，应按 Track Assignment Principle 评估是否应归入 T1 或 T2。

### 18.2 Multimodal fields

~~~text
multimodal:
  visual_dependency_required
  visual_dependency_check
  referenced_regions
~~~

### 18.3 visual_dependency_check

Candidate 阶段可以为：

~~~text
not_checked
~~~

进入 Pilot 前必须有明确状态，例如：

~~~text
passed
failed
needs_review
~~~

以后可以加入 text-only ablation result，但具体实验方法属于 Pilot Design / Evaluation Specification。

### 18.4 referenced_regions

可以记录题目真正依赖的视觉区域，引用对应 Evidence 和 bbox，例如：

~~~text
referenced_regions[]:
  evidence_id
  bbox
  purpose
~~~

如果题目依赖整页，可以引用 evidence_type = page 的 Evidence；如果依赖局部区域，应保留 bbox 或等价区域引用。

## 19. Construction / Generation Metadata

所有 Benchmark Item 都需要知道“它是怎么来的”。

~~~text
construction:
  method
  generator
  template_id
  prompt_template_id
  prompt_template_version
  source_evidence_refs
  random_seed
  created_by
~~~

### 19.1 method

候选值：

~~~text
human_authored
llm_assisted
template_generated
parameterized_generated
transformed_from_source
~~~

### 19.2 generator

如使用生成器或 LLM，可以记录：

~~~text
generator:
  type
  model_name
  model_version
  provider
~~~

如果 Item 完全不是 LLM 生成，generator 可以为空。不得保存 API Key、Token 或 Secret。

### 19.3 复现边界

为了复现，优先记录：

- prompt_template_id + prompt_template_version；
- template_id；
- parameter_set_id；
- random_seed（如适用）；
- 相关 Source Evidence References。

不要求每条 Item 重复保存巨大 Prompt，也不把整段 Source PDF 复制到 generation metadata。

## 20. Verification Schema

Verification 不能简化为：

~~~text
human_checked: true
~~~

而应设计为 Verification Records。一个 Item 可以有多个 record：

~~~text
verification_record:
  verification_id
  verification_type
  method
  verifier_type
  status
  timestamp
  notes
  artifact_refs
~~~

### 20.1 verification_type

候选值：

~~~text
schema_validation
source_verification
ground_truth_verification
programmatic_calculation
unit_check
duplicate_check
ambiguity_check
visual_dependency_check
expert_review
~~~

### 20.2 verifier_type

候选值：

~~~text
rule
program
llm
human
hybrid
~~~

如果 verifier_type = llm，应记录：

~~~text
model_name
model_version
prompt_template_version
~~~

LLM Verification 只能作为审核证据之一，不能因为 llm status = passed 就默认 Ground Truth 可靠。

### 20.3 Verification status

建议使用统一状态：

~~~text
not_checked
passed
failed
needs_review
not_applicable
~~~

Verification Record 的 notes 和 artifact_refs 可以指向程序输出、人工审核单、公式计算记录或其他可审计材料。

## 21. Human Expert Review

Human Expert Review 资源当前仍为 TBD。因此 Schema 不能要求所有 Item 都具有：

~~~text
human_checked: true
~~~

而应支持：

~~~text
human_review:
  review_status
  reviewer_role
  reviewer_ref
  review_timestamp
  decision
  notes
~~~

`reviewer_ref` 不要求存真实姓名，可以使用项目内部稳定的匿名或伪名引用。具体哪些 Item 必须专家审核、审核轮次和抽样比例，留给 Pilot Design / Quality Policy。

## 22. Quality Metadata

Canonical Item 应保留质量摘要：

~~~text
quality:
  summary_status
  ambiguity_status
  source_quality_status
  ground_truth_confidence
  duplicate_status
  contamination_status
  visual_dependency_status
  review_status
~~~

### 22.1 Quality status

`summary_status` 是当前 Item Revision 的总体 Materialized Quality Summary 状态；它以及除 ground_truth_confidence 的最终表达形式外的质量检查字段可以采用：

~~~text
not_checked
passed
failed
needs_review
not_applicable
~~~

`summary_status` 应作为 Quality Summary 的明确状态字段提供；具体如何由 Verification Records 与 Governance 事实聚合，仍留给后续 Quality Policy / Implementation。

ground_truth_confidence 字段在 v0.1 预留，但采用等级、数值还是由 verification chain 推导，留在 Open Questions；不得把未经定义的数值当作可比较的最终分数。

### 22.2 Quality 与 Score 的边界

Quality Metadata 描述 Item 是否存在歧义、来源风险、答案验证风险或污染风险，不等于模型运行后的自动评分，也不等于 Item 难度的最终经验估计。

### 22.3 Canonical Records vs Materialized Summary

本规范区分用于保存事实历史的 Canonical Records 与用于当前决策的 Materialized Summary：

- Verification Records 保存历史验证证据和 Audit Trail，允许同一 Item Revision 拥有多个 Record，并采用 append-oriented 的记录方式；
- Governance 保存详细治理事实和关系，例如 duplicate group IDs、contamination、replacement relation 以及 visibility；
- Quality 保存当前 Item Revision 的 Materialized Quality Summary，用于 filtering、reporting 和 QA decision；
- Quality Summary 不替代 Verification Records，也不能抹去历史验证记录。

如果 Quality Summary 与详细 Verification / Governance Records 冲突，不得静默选择其中一方；当前 Item Revision 必须进入 `needs_review`。

## 23. Duplicate / Near-duplicate

支持记录：

~~~text
duplicate:
  exact_duplicate_group_id
  near_duplicate_group_id
  semantic_duplicate_group_id
~~~

这些字段不是所有 Item 都必须有值。其目的是防止同一道题只经过轻微改写后重复进入 Test Set，也支持后续数据审计。

必须区分：

- Source Document 的 document_family_id：文档级关系，包括版本、扫描版/文本版和同资料不同来源；
- Item Duplicate Group：题目级关系，包括相同题目、近似改写和语义重复。

文档 family 相同不必然表示题目完全相同，但在污染审查和 Dataset Split 时应被共同考虑。

## 24. Contamination Metadata

支持：

~~~text
contamination:
  source_training_overlap_status
  benchmark_item_overlap_status
  document_family_overlap_status
  check_method
  check_version
~~~

初始状态允许：

~~~text
unknown
not_checked
clear
suspected
confirmed
~~~

只有执行过相应检查，才允许使用 clear。未发现重合但尚未执行检查时，必须保持 unknown 或 not_checked。

污染控制既要考虑题目级别，也要考虑 document-family 级别，包括同一本书不同版本、扫描版/文本版、同一资料不同来源和高度重复资料。

## 25. Data Visibility / Export Control

考虑到 Candidate Source Corpus 和 Benchmark Source Corpus 的版权及使用状态未知，逻辑 Schema 支持：

~~~text
governance:
  visibility:
    item_visibility
    evidence_visibility
    asset_visibility
~~~

候选枚举：

~~~text
internal_only
exportable
withheld
needs_review
~~~

未来可以公开 Question + Answer，但不公开原始书籍页面或完整 Evidence。不要假设 Benchmark Item 可发布，就意味着 Source PDF、Image Crop 或完整 Evidence 也可发布。

visibility 的最终导出策略仍需结合 Source Type、rights_status 和 Release Policy 决定。

## 26. Scoring-related Data Boundary

Data Specification 可以保存 Ground Truth 所需的数据，但不定义完整评分算法。

例如 Numeric 可以保存：

~~~text
value
unit
dimensionless
absolute_tolerance
relative_tolerance
rounding_rule
accepted_unit_conversions
~~~

但以下内容属于 Evaluation Specification：

- absolute tolerance 和 relative tolerance 如何组合；
- short answer 的 alias matching 算法；
- structured answer 的字段级评分方式；
- LLM Judge 的使用条件、提示和聚合方式；
- 不同 Track 的最终分数聚合。

## 27. Evaluation Result 不属于 Benchmark Item

不要把模型运行结果写回 Canonical Benchmark Item，例如：

~~~text
model_answer
score
latency
token_usage
~~~

这些属于独立的 Evaluation Result Entity。Evaluation Result 至少通过以下键引用 Item：

~~~text
item_id
item_revision
dataset_version
~~~

具体 Result Schema、存储方式和运行协议由 Evaluation Specification / System Architecture 进一步定义。

## 28. Dataset Membership

Item 与 Dataset 的关系使用多个 Membership 记录表达，而不是单一的、会被后续覆盖的对象：

~~~text
dataset_memberships[]:
  membership_id
  collection
  partition
  dataset_version
  item_revision
  membership_status
~~~

每个 Membership 至少包括：

| Field | Required | Description |
| --- | --- | --- |
| membership_id | Required | 该成员关系记录的稳定标识 |
| collection | Required | Candidate、Pilot Benchmark 或 Benchmark V1 所属集合 |
| partition | Required | 当前分区占位字段；Public / Private 设计仍为 TBD |
| dataset_version | Required | 该 Membership 所属的 Dataset Version |
| item_revision | Required | 被纳入该 Dataset Version 的具体 Item Revision |
| membership_status | Required | 当前 Membership 状态 |

`membership_status` 初始允许：

~~~text
included
removed
superseded
~~~

当前允许的 collection：

~~~text
candidate
pilot
benchmark_v1
~~~

当前阶段的 partition 只作为集合内分区的占位记录，可暂用：

~~~text
unassigned
pilot
~~~

Public / Private 的最终 partition 设计尚未决定。因此本 v0.1 不强行定义：

- public / private 的最终枚举及发布含义；
- train / dev / test；
- public_test / private_test；
- Full Public Test Set 或 Private Test Set 的最终发布策略。

未来可以扩展 Controlled Vocabulary，但已发布 Dataset Version 的成员关系必须可追溯。

同一 Item Revision 可以保留多个历史 Membership，例如先进入 Candidate、再进入 Pilot Benchmark，或在某个 Dataset Version 中被 removed / superseded。Membership 记录追加保存，不能通过更新一条记录来覆盖历史关系。

### 28.1 Dataset Snapshot / Revision Freeze

Benchmark 的可复现性依赖以下三元组：

~~~text
dataset_version
+ item_id
+ item_revision
~~~

每个 Dataset Version 必须冻结其包含的具体 Item Revision 集合。历史 Pilot Benchmark 或 Benchmark V1 Snapshot 不得自动漂移到同一 `item_id` 的最新 revision；如需更新，必须创建新的 Dataset Version 或新的显式 Membership 记录，并保留原 Snapshot。

## 29. Timestamps

建议至少：

~~~text
timestamps:
  created_at
  updated_at
  verified_at
  released_at
~~~

其中 `verified_at` 和 `released_at` 允许为空。`verified_at` 不表示最后一次任意 Verification 的时间，而表示当前 Item Revision 首次达到项目规定的 verification-complete / accepted verification policy 的时间；具体 verification-complete 条件留给后续 Pilot Design / Quality Policy。单次 Verification 的时间继续使用 `verification[].timestamp`。时间统一建议使用 ISO 8601，并明确时区或使用 UTC 表示。

## 30. Cross-field Validation Rules

以下规则是 Data Specification v0.1 的逻辑验证边界，不代表已经实现 Schema Validator。

### Rule 1：T1 与 Capability

~~~text
taxonomy.primary_benchmark_track = T1
~~~

则：

~~~text
taxonomy.primary_capability.capability_id ∈ K1–K8
~~~

### Rule 2：T2 与 Capability

~~~text
taxonomy.primary_benchmark_track = T2
~~~

则：

~~~text
taxonomy.primary_capability.capability_id ∈ C1–C8
~~~

### Rule 3：T3 与 Capability / Visual Asset

~~~text
taxonomy.primary_benchmark_track = T3
~~~

则：

- taxonomy.primary_capability.capability_id ∈ M1–M11；
- 至少存在一个 Visual Asset；
- multimodal 必须存在。

### Rule 4：T3 Visual Dependency

T3 Item 必须满足：

~~~text
multimodal.visual_dependency_required = true
~~~

### Rule 5：Choice 与 Options

当 answer_type = single_choice 或 multiple_choice 时，question.options 必须存在，且每个 Option 有稳定 option_id 和 content。

### Rule 6：Single Choice

当 answer_type = single_choice 时，只能有一个 ground_truth.correct_option_id，且它必须引用有效 Option ID。

### Rule 7：Multiple Choice

当 answer_type = multiple_choice 时，ground_truth.correct_option_ids 至少有一个元素，且每个元素必须引用有效 Option ID。

### Rule 8：Numeric Ground Truth

当 answer_type = numeric 时，`ground_truth` 必须提供 value、unit、dimensionless、absolute_tolerance、relative_tolerance、rounding_rule 和 accepted_unit_conversions 字段；单位与无量纲状态的互斥关系由 Rule 16 进一步约束。

### Rule 9：Source-grounded Evidence

当：

~~~text
source_provenance.source_provenance_type ∈ {
  source_grounded,
  parameterized_from_source
}
~~~

则至少存在一个 source_provenance.evidence_refs。

### Rule 10：Evidence Document

任何 Source Evidence 必须引用有效的 document_id，且该 document_id 必须能解析到 Source Document。

### Rule 11：BBox Context

如果 Evidence 有 bbox，必须同时有：

- coordinate_system；
- origin；
- page_index；
- page_width；
- page_height。

### Rule 12：Rejected Item

当：

~~~text
item_status = rejected
~~~

必须有：

~~~text
governance.rejection_reason
~~~

### Rule 13：Empirical Difficulty Timing

empirical_difficulty 在 Pilot 模型验证前允许为 null，不能把缺少经验难度误标为 easy 或 hard。

### Rule 14：Secondary Capability 不重复

secondary_capabilities 中不得出现与 primary_capability 相同的 capability ID。

### Rule 15：Released Revision

Released Item 的 Question、Ground Truth、Source Provenance、Answer Type、关键 Taxonomy、视觉依赖或验证结论发生关键内容修改时，必须增加 item_revision，不得静默覆盖。

### Rule 16：Numeric XOR

当 answer_type = numeric 时，单位状态必须满足严格 XOR 规则：

- 有单位：`ground_truth.unit != null` 且 `ground_truth.dimensionless = false`；
- 无单位：`ground_truth.unit = null` 且 `ground_truth.dimensionless = true`；
- 不允许 `ground_truth.unit != null` 且 `ground_truth.dimensionless = true`，也不允许单位和无量纲状态均未明确。

### Rule 17：Primary Evidence

当 `source_provenance.primary_evidence_id != null` 时，该 ID 必须存在于同一 Item 的 `source_provenance.evidence_refs[]` 中。

### Rule 18：Asset Evidence Reference

当 Asset 提供 `source_evidence_id` 时，该 ID 必须解析到有效的 Source Evidence；Source-derived Asset 不得引用不存在或不属于其 Source Document 的 Evidence。

### Rule 19：Dataset Membership Revision

每个 `dataset_memberships[].item_revision` 必须指向实际存在的同一 `item_id` 的 Item Revision。历史 Dataset Version 必须继续指向其冻结时的具体 revision，不得漂移到最新 revision。

### Rule 20：Accepted Item

`item_status = accepted` 只表示 Item 满足当前 Quality Policy，可以参与 Dataset Assembly；它不自动表示进入 Pilot Benchmark 或 Released 范围。Pilot / Benchmark V1 成员关系必须由独立的 Dataset Membership 记录表达。

### Rule 21：Quality Summary Consistency

当 Quality Summary 为 `passed` 时，必须存在与当前 Item Revision 对应的 Verification / Governance Evidence。Quality Summary 与详细记录冲突时，不能判定为通过，必须将 Item 置为 `needs_review`。

### Rule 22：Calculation Ground Truth Consistency

程序计算或公式验证的结果必须与 Ground Truth 对应；如果 Calculation Audit 结果与 Ground Truth 冲突，不得通过 Ground Truth Verification，且 Item 必须进入后续 review 流程。

### Rule 23：Numeric Unit Policy Consistency

当 answer_type = numeric 时，answer_requirements.numeric_unit_policy 必须与 Ground Truth 的单位状态一致：

- ground_truth.dimensionless = true 时，numeric_unit_policy 必须为 dimensionless；
- numeric_unit_policy = dimensionless 时，ground_truth.unit 必须为 null；
- Ground Truth 有物理单位时，numeric_unit_policy 不得为 dimensionless；
- numeric_unit_policy = unit_specified_in_question 或 explicit_unit_required 时，Ground Truth 必须提供对应的 Canonical Unit。

## 31. Canonical JSON Example

以下是三个可读的完整概念示例，用于展示不同 Track 的字段关系。它们不是已生成的 Benchmark 数据，也不是最终 JSON Schema；其中的 Document、Evidence 和 Asset ID 是示例占位标识。

### Example A：Mechanical Knowledge / Bearing Fault Diagnosis

~~~json
{
  "item_id": "MIGB-EXAMPLE-001",
  "schema_version": "0.1",
  "item_revision": 1,
  "item_status": "candidate",
  "content_hash": "hash:example-001",
  "taxonomy": {
    "taxonomy_version": "0.1",
    "primary_domain": {
      "level1_id": "D03",
      "level1_name": "Mechanical Design & Machine Elements",
      "level2_id": "D03.bearings",
      "level2_name": "Bearings"
    },
    "secondary_domains": [],
    "primary_benchmark_track": "T1",
    "primary_capability": {
      "capability_id": "K7",
      "capability_name": "Fault Diagnosis & Troubleshooting"
    },
    "secondary_capabilities": [],
    "task": {
      "task_id": "bearing_failure_diagnosis",
      "task_name": "Bearing Failure Diagnosis"
    },
    "cross_cutting_skill_tags": ["diagnosis", "reasoning"],
    "design_difficulty": "hard",
    "empirical_difficulty": null
  },
  "question": {
    "language": "zh-CN",
    "stem": "某轴承运行中出现温升、噪声和振动。请判断最可能的故障模式，并给出优先排查行动。",
    "instructions": "按 fault_mode、cause、recommended_action 三个字段回答。",
    "options": []
  },
  "inputs": {
    "primary_modality": "text",
    "assets": []
  },
  "answer_type": "structured_answer",
  "ground_truth": {
    "expected_fields": ["fault_mode", "cause", "recommended_action"],
    "required_fields": ["fault_mode", "recommended_action"],
    "field_ground_truth": {
      "fault_mode": {
        "canonical_answer": "润滑不足或污染导致的轴承异常磨损",
        "accepted_aliases": ["轴承润滑故障", "轴承异常磨损"]
      },
      "cause": {
        "canonical_answer": "润滑条件不满足或污染物进入滚道",
        "accepted_aliases": []
      },
      "recommended_action": {
        "canonical_answer": "先停机确认润滑状态、污染情况和装配条件",
        "accepted_aliases": []
      }
    },
    "ground_truth_explanation": "该示例的解释供内部审核使用，不作为模型输入。"
  },
  "source_provenance": {
    "source_provenance_type": "source_grounded",
    "evidence_refs": ["EVD-EXAMPLE-001"],
    "primary_evidence_id": "EVD-EXAMPLE-001"
  },
  "construction": {
    "method": "human_authored",
    "generator": null,
    "template_id": null,
    "prompt_template_id": null,
    "prompt_template_version": null,
    "source_evidence_refs": ["EVD-EXAMPLE-001"],
    "random_seed": null,
    "created_by": "author-example"
  },
  "verification": [
    {
      "verification_id": "VER-EXAMPLE-001",
      "verification_type": "source_verification",
      "method": "evidence_locator_check",
      "verifier_type": "rule",
      "status": "passed",
      "timestamp": "2026-09-11T00:00:00Z",
      "notes": "示例时间戳，不代表真实审核记录。",
      "artifact_refs": ["EVD-EXAMPLE-001"]
    }
  ],
  "quality": {
    "summary_status": "needs_review",
    "ambiguity_status": "needs_review",
    "source_quality_status": "not_checked",
    "ground_truth_confidence": null,
    "duplicate_status": "not_checked",
    "contamination_status": "not_checked",
    "visual_dependency_status": "not_applicable",
    "review_status": "not_checked"
  },
  "governance": {
    "visibility": {
      "item_visibility": "internal_only",
      "evidence_visibility": "withheld",
      "asset_visibility": "not_applicable"
    },
    "duplicate": {},
    "contamination": {
      "source_training_overlap_status": "unknown",
      "benchmark_item_overlap_status": "not_checked",
      "document_family_overlap_status": "not_checked",
      "check_method": null,
      "check_version": null
    },
    "rejection_reason": null,
    "replacement_item_id": null,
    "replacement_revision": null
  },
  "dataset_memberships": [
    {
      "membership_id": "MEM-EXAMPLE-001",
      "collection": "candidate",
      "partition": "unassigned",
      "dataset_version": "candidate-0.1",
      "item_revision": 1,
      "membership_status": "included"
    }
  ],
  "timestamps": {
    "created_at": "2026-09-11T00:00:00Z",
    "updated_at": "2026-09-11T00:00:00Z",
    "verified_at": null,
    "released_at": null
  }
}
~~~

### Example B：Engineering Calculation / Shaft Torque

~~~json
{
  "item_id": "MIGB-EXAMPLE-002",
  "schema_version": "0.1",
  "item_revision": 1,
  "item_status": "candidate",
  "content_hash": "hash:example-002",
  "taxonomy": {
    "taxonomy_version": "0.1",
    "primary_domain": {
      "level1_id": "D03",
      "level1_name": "Mechanical Design & Machine Elements",
      "level2_id": "D03.shafts",
      "level2_name": "Shafts"
    },
    "secondary_domains": [],
    "primary_benchmark_track": "T2",
    "primary_capability": {
      "capability_id": "C1",
      "capability_name": "Direct Formula Application"
    },
    "secondary_capabilities": [],
    "task": {
      "task_id": "shaft_torque_calculation",
      "task_name": "Shaft Torque Calculation"
    },
    "cross_cutting_skill_tags": ["calculation"],
    "design_difficulty": "easy",
    "empirical_difficulty": null
  },
  "question": {
    "language": "zh-CN",
    "stem": "某轴传递功率 100 kW，转速为 1000 r/min。求轴的扭矩。",
    "instructions": "请给出数值和 N·m 单位。",
    "options": []
  },
  "inputs": {
    "primary_modality": "text_formula",
    "assets": []
  },
  "answer_type": "numeric",
  "answer_requirements": {
    "numeric_unit_policy": "unit_specified_in_question"
  },
  "ground_truth": {
    "value": 955.0,
    "unit": "N·m",
    "dimensionless": false,
    "absolute_tolerance": 1.0,
    "relative_tolerance": 0.01,
    "rounding_rule": "round to nearest 1 N·m",
    "accepted_unit_conversions": ["N·m", "kN·m"],
    "ground_truth_explanation": "T = 9550P/n；P 使用 kW，n 使用 r/min。"
  },
  "source_provenance": {
    "source_provenance_type": "parameterized_from_source",
    "evidence_refs": ["EVD-EXAMPLE-002"],
    "primary_evidence_id": "EVD-EXAMPLE-002"
  },
  "construction": {
    "method": "parameterized_generated",
    "generator": null,
    "template_id": "TPL-shaft-torque-v0.1",
    "prompt_template_id": null,
    "prompt_template_version": null,
    "source_evidence_refs": ["EVD-EXAMPLE-002"],
    "random_seed": 1002,
    "created_by": "template-example"
  },
  "calculation": {
    "formula_refs": [
      {
        "formula_id": "FORMULA-shaft-torque-001",
        "expression": "T = 9550 * P / n",
        "source_evidence_id": "EVD-EXAMPLE-002"
      }
    ],
    "variables": [
      {"symbol": "P", "value": 100, "unit": "kW", "role": "given", "source": "question"},
      {"symbol": "n", "value": 1000, "unit": "r/min", "role": "given", "source": "question"},
      {"symbol": "T", "value": 955.0, "unit": "N·m", "role": "target", "source": "ground_truth"}
    ],
    "constants": [],
    "constraints": ["n > 0"],
    "intermediate_values": [],
    "verification_method": "programmatic_calculation"
  },
  "verification": [
    {
      "verification_id": "VER-EXAMPLE-002",
      "verification_type": "programmatic_calculation",
      "method": "deterministic_formula_evaluation",
      "verifier_type": "program",
      "status": "passed",
      "timestamp": "2026-09-11T00:00:00Z",
      "notes": "示例记录。",
      "artifact_refs": ["FORMULA-shaft-torque-001"]
    }
  ],
  "quality": {
    "summary_status": "needs_review",
    "ambiguity_status": "passed",
    "source_quality_status": "not_checked",
    "ground_truth_confidence": null,
    "duplicate_status": "not_checked",
    "contamination_status": "not_checked",
    "visual_dependency_status": "not_applicable",
    "review_status": "needs_review"
  },
  "governance": {
    "visibility": {
      "item_visibility": "internal_only",
      "evidence_visibility": "withheld",
      "asset_visibility": "not_applicable"
    },
    "duplicate": {},
    "contamination": {
      "source_training_overlap_status": "not_checked",
      "benchmark_item_overlap_status": "not_checked",
      "document_family_overlap_status": "not_checked",
      "check_method": null,
      "check_version": null
    },
    "rejection_reason": null,
    "replacement_item_id": null,
    "replacement_revision": null
  },
  "dataset_memberships": [
    {
      "membership_id": "MEM-EXAMPLE-002",
      "collection": "candidate",
      "partition": "unassigned",
      "dataset_version": "candidate-0.1",
      "item_revision": 1,
      "membership_status": "included"
    }
  ],
  "timestamps": {
    "created_at": "2026-09-11T00:00:00Z",
    "updated_at": "2026-09-11T00:00:00Z",
    "verified_at": null,
    "released_at": null
  }
}
~~~

### Example C：Multimodal / Assembly Drawing Clearance

~~~json
{
  "item_id": "MIGB-EXAMPLE-003",
  "schema_version": "0.1",
  "item_revision": 1,
  "item_status": "candidate",
  "content_hash": "hash:example-003",
  "taxonomy": {
    "taxonomy_version": "0.1",
    "primary_domain": {
      "level1_id": "D03",
      "level1_name": "Mechanical Design & Machine Elements",
      "level2_id": "D03.structural_design_fundamentals",
      "level2_name": "Structural Design Fundamentals"
    },
    "secondary_domains": [],
    "primary_benchmark_track": "T3",
    "primary_capability": {
      "capability_id": "M9",
      "capability_name": "Geometric / Quantitative Visual Reasoning"
    },
    "secondary_capabilities": [
      {"capability_id": "M8", "capability_name": "Assembly & Spatial Relationship"}
    ],
    "task": {
      "task_id": "parameter_calculation_from_drawing",
      "task_name": "Parameter Calculation from Drawing"
    },
    "cross_cutting_skill_tags": ["calculation", "spatial_reasoning"],
    "design_difficulty": "hard",
    "empirical_difficulty": null
  },
  "question": {
    "language": "zh-CN",
    "stem": "请根据装配图读取指定尺寸，并计算指定装配间隙。",
    "instructions": "请给出数值和 mm 单位。",
    "options": []
  },
  "inputs": {
    "primary_modality": "assembly_drawing",
    "assets": [
      {
        "asset_id": "AST-EXAMPLE-003",
        "asset_type": "drawing",
        "visual_type": "assembly_drawing",
        "role": "required_visual_evidence",
        "storage_reference": "asset-reference://AST-EXAMPLE-003",
        "checksum": "hash:asset-example-003",
        "source_evidence_id": "EVD-EXAMPLE-003"
      }
    ]
  },
  "answer_type": "numeric",
  "answer_requirements": {
    "numeric_unit_policy": "unit_specified_in_question"
  },
  "ground_truth": {
    "value": 0.20,
    "unit": "mm",
    "dimensionless": false,
    "absolute_tolerance": 0.01,
    "relative_tolerance": 0.05,
    "rounding_rule": "round to nearest 0.01 mm",
    "accepted_unit_conversions": ["mm"],
    "ground_truth_explanation": "装配间隙由图纸中指定的视觉尺寸关系计算得到。"
  },
  "source_provenance": {
    "source_provenance_type": "source_grounded",
    "evidence_refs": ["EVD-EXAMPLE-003"],
    "primary_evidence_id": "EVD-EXAMPLE-003"
  },
  "construction": {
    "method": "transformed_from_source",
    "generator": null,
    "template_id": null,
    "prompt_template_id": null,
    "prompt_template_version": null,
    "source_evidence_refs": ["EVD-EXAMPLE-003"],
    "random_seed": null,
    "created_by": "author-example"
  },
  "calculation": {
    "formula_refs": [],
    "variables": [
      {"symbol": "d_1", "value": null, "unit": "mm", "role": "given", "source": "referenced_region:region-1"},
      {"symbol": "d_2", "value": null, "unit": "mm", "role": "given", "source": "referenced_region:region-2"},
      {"symbol": "c", "value": 0.20, "unit": "mm", "role": "target", "source": "ground_truth"}
    ],
    "constants": [],
    "constraints": ["c >= 0"],
    "intermediate_values": [],
    "verification_method": "programmatic_calculation"
  },
  "multimodal": {
    "visual_dependency_required": true,
    "visual_dependency_check": "needs_review",
    "referenced_regions": [
      {"evidence_id": "EVD-EXAMPLE-003", "bbox": {"x0": 0.10, "y0": 0.20, "x1": 0.40, "y1": 0.50, "coordinate_system": "normalized_0_1", "origin": "top_left", "page_width": 1.0, "page_height": 1.0}, "purpose": "读取第一尺寸"},
      {"evidence_id": "EVD-EXAMPLE-003", "bbox": {"x0": 0.50, "y0": 0.20, "x1": 0.80, "y1": 0.50, "coordinate_system": "normalized_0_1", "origin": "top_left", "page_width": 1.0, "page_height": 1.0}, "purpose": "读取第二尺寸"}
    ]
  },
  "verification": [
    {
      "verification_id": "VER-EXAMPLE-003-A",
      "verification_type": "visual_dependency_check",
      "method": "required_region_review",
      "verifier_type": "human",
      "status": "needs_review",
      "timestamp": "2026-09-11T00:00:00Z",
      "notes": "示例记录。",
      "artifact_refs": ["AST-EXAMPLE-003"]
    },
    {
      "verification_id": "VER-EXAMPLE-003-B",
      "verification_type": "programmatic_calculation",
      "method": "deterministic_clearance_calculation",
      "verifier_type": "program",
      "status": "passed",
      "timestamp": "2026-09-11T00:00:00Z",
      "notes": "示例记录。",
      "artifact_refs": []
    }
  ],
  "quality": {
    "summary_status": "needs_review",
    "ambiguity_status": "needs_review",
    "source_quality_status": "not_checked",
    "ground_truth_confidence": null,
    "duplicate_status": "not_checked",
    "contamination_status": "not_checked",
    "visual_dependency_status": "needs_review",
    "review_status": "needs_review"
  },
  "governance": {
    "visibility": {
      "item_visibility": "internal_only",
      "evidence_visibility": "withheld",
      "asset_visibility": "withheld"
    },
    "duplicate": {},
    "contamination": {
      "source_training_overlap_status": "unknown",
      "benchmark_item_overlap_status": "not_checked",
      "document_family_overlap_status": "not_checked",
      "check_method": null,
      "check_version": null
    },
    "rejection_reason": null,
    "replacement_item_id": null,
    "replacement_revision": null
  },
  "dataset_memberships": [
    {
      "membership_id": "MEM-EXAMPLE-003",
      "collection": "candidate",
      "partition": "unassigned",
      "dataset_version": "candidate-0.1",
      "item_revision": 1,
      "membership_status": "included"
    }
  ],
  "timestamps": {
    "created_at": "2026-09-11T00:00:00Z",
    "updated_at": "2026-09-11T00:00:00Z",
    "verified_at": null,
    "released_at": null
  }
}
~~~

## 32. Minimal Valid Benchmark Item

以下是一个最简单的 Source-grounded、Text-only Knowledge Item 的最低参照。它用于未来 Schema Validator 的最小互操作检查，不代表 Pilot 或 Release-ready Item 的全部要求。

~~~json
{
  "item_id": "MIGB-000001",
  "schema_version": "0.1",
  "item_revision": 1,
  "item_status": "candidate",
  "taxonomy": {
    "taxonomy_version": "0.1",
    "primary_domain": {
      "level1_id": "D03",
      "level1_name": "Mechanical Design & Machine Elements",
      "level2_id": "D03.bearings",
      "level2_name": "Bearings"
    },
    "secondary_domains": [],
    "primary_benchmark_track": "T1",
    "primary_capability": {"capability_id": "K1", "capability_name": "Fact & Terminology"},
    "secondary_capabilities": [],
    "task": {"task_id": "term_definition", "task_name": "Term Definition"},
    "cross_cutting_skill_tags": [],
    "design_difficulty": "easy",
    "empirical_difficulty": null
  },
  "question": {
    "language": "zh-CN",
    "stem": "什么是滚动轴承？",
    "instructions": null,
    "options": []
  },
  "inputs": {"primary_modality": "text", "assets": []},
  "answer_type": "short_answer",
  "ground_truth": {
    "canonical_answer": "利用滚动体在滚道间滚动来承受载荷并实现相对运动的轴承。",
    "accepted_aliases": [],
    "normalization": {
      "case_sensitive": false,
      "trim_whitespace": true,
      "unicode_normalization": true,
      "punctuation_normalization": true
    }
  },
  "source_provenance": {
    "source_provenance_type": "source_grounded",
    "evidence_refs": ["EVD-000001"],
    "primary_evidence_id": "EVD-000001"
  },
  "construction": {"method": "human_authored", "created_by": "author-example"},
  "verification": [
    {"verification_id": "VER-000001", "verification_type": "schema_validation", "method": "logical_rules", "verifier_type": "rule", "status": "passed", "timestamp": "2026-09-11T00:00:00Z", "notes": null, "artifact_refs": []}
  ],
  "quality": {
    "summary_status": "not_checked",
    "ambiguity_status": "not_checked",
    "source_quality_status": "not_checked",
    "ground_truth_confidence": null,
    "duplicate_status": "not_checked",
    "contamination_status": "not_checked",
    "visual_dependency_status": "not_applicable",
    "review_status": "not_checked"
  },
  "governance": {
    "visibility": {"item_visibility": "internal_only", "evidence_visibility": "withheld", "asset_visibility": "not_applicable"},
    "duplicate": {},
    "contamination": {"source_training_overlap_status": "unknown", "benchmark_item_overlap_status": "not_checked", "document_family_overlap_status": "not_checked", "check_method": null, "check_version": null},
    "rejection_reason": null,
    "replacement_item_id": null,
    "replacement_revision": null
  },
  "dataset_memberships": [
    {
      "membership_id": "MEM-000001",
      "collection": "candidate",
      "partition": "unassigned",
      "dataset_version": "candidate-0.1",
      "item_revision": 1,
      "membership_status": "included"
    }
  ],
  "timestamps": {"created_at": "2026-09-11T00:00:00Z", "updated_at": "2026-09-11T00:00:00Z", "verified_at": null, "released_at": null}
}
~~~

Minimum required concepts are therefore at least：

~~~text
item_id
schema_version
item_revision
item_status
taxonomy.taxonomy_version
taxonomy
question
inputs
answer_type
ground_truth
source_provenance
construction
verification
quality
governance
timestamps
~~~

完整 Canonical Item 仍应按照第 5 节提供 construction、quality、governance 和 timestamps 等字段。

## 33. Internal vs Export Representation

### 33.1 Canonical Internal Item

Canonical Internal Item 可以包含：

- internal Evidence；
- Review Notes；
- Generator Metadata；
- Verification Details；
- Contamination Results；
- Source Document 关联；
- 不适合公开的原始页面、Asset Reference 或版权状态。

### 33.2 Export View

未来公开导出时，应生成独立的 Export View，而不是直接把 Canonical Internal Item 原样发布。Export View 可以根据 Release Policy 选择性保留：

- Question；
- Answer 或有限 Ground Truth；
- source title；
- Evidence；
- Asset；
- Explanation；
- Verification 摘要。

是否保留这些字段，以及如何遵守 item_visibility、evidence_visibility、asset_visibility 和 rights_status，由未来 Release Policy 决定。

## 34. Schema Evolution

### 34.1 Evolution 原则

- 新增字段优先保持 backward compatible；
- 新字段在旧数据中可以有默认值、null 或明确的 not_checked，但不得改变旧字段的既有语义；
- 重命名或删除字段必须记录 migration rule；
- Released Benchmark 必须能够知道自己使用的 Schema Version；
- Schema 变更与 Taxonomy 变更分别管理，不能用一次变更同时掩盖两者的语义变化。

### 34.2 变更记录要求

涉及字段重命名、删除或替代时，至少记录：

~~~text
schema_version
migration_rule
deprecated_field
replacement_field
~~~

历史 Item 的 schema_version 不得被静默改写。必要时通过显式迁移生成新的数据快照，并保留迁移前后的审计关系。

## 35. Open Questions

以下问题尚未正式决定，全部保持 TBD：

1. 最终物理存储主要采用 JSONL / Parquet / DB 中哪一种？—— TBD
2. Domain Level 2 是否正式分配 stable ID？—— TBD
3. Secondary Domain 最大数量是否限制？—— TBD
4. Secondary Capability 最大数量是否限制？—— TBD
5. cross_cutting_skill_tags 最终 Controlled Vocabulary 如何维护？—— TBD
6. Evidence 是否允许公开，以及不同 Source Type 的导出策略？—— TBD
7. BBox 是否统一转换为 normalized coordinates？—— TBD
8. Formula Registry 是否独立维护？—— TBD
9. Human Expert Review 哪些 Item 必须执行？—— TBD
10. Ground Truth Confidence 是否采用等级、数值还是 verification chain 推导？—— TBD
11. Public / Private Benchmark Partition 如何表示？—— TBD
12. Structured Answer 最终允许哪些结构？—— TBD
13. Dataset Version 与 Git Release / Data Snapshot 如何绑定？—— TBD
14. Item Lifecycle 的状态迁移图是否需要独立 State Machine Specification？—— TBD
15. Quality Summary 最终由 Verification Records 自动聚合还是由 QA Pipeline 显式写入？—— TBD
16. Dataset Membership 是否需要记录 included_at / removed_at / decision_record_ref？—— TBD
17. 单位体系是否建立统一 Unit Registry / Quantity Dimension Registry？—— TBD

本节的问题不能被当前 Data Specification v0.1 的概念字段默认解释为已经解决。

## 36. References to Upstream Documents

本文件的上位约束为：

- Project Charter v0.1；
- Project Plan v0.1；
- Benchmark Taxonomy v0.1。

其中 Benchmark Taxonomy v0.1 已定义：

- Primary Domain；
- Primary Benchmark Track；
- Fine-grained Capability；
- Task；
- Modality；
- Difficulty；
- Answer Type。

Data Specification 负责将这些概念映射成机器可表示字段，不在本文件重新定义它们的专业语义。特别是：

- taxonomy.primary_domain 映射 Taxonomy 的 Domain；
- taxonomy.primary_benchmark_track 映射 Primary Evaluation Bucket；
- taxonomy.primary_capability、secondary_capabilities 和 task 映射 Capability / Task；
- inputs.primary_modality 和 Asset 的 visual_type 映射 Modality / Visual Type；
- taxonomy.design_difficulty 和 empirical_difficulty 映射 Difficulty；
- 顶层 answer_type 与 ground_truth 映射 Answer Type 及其 discriminated structure。

## 37. 当前阶段边界与禁止事项

Data Specification v0.1 只设计 Benchmark 数据契约，不开始以下工作：

- 编写 Python、Pydantic 或 JSON Schema 实现；
- 处理 70k PDF 或执行 PDF Inventory；
- 编写 MinerU Pipeline、OCR 或其他 PDF Processing；
- 生成 Benchmark 数据或大规模自动出题；
- 调用模型或实现 Evaluation Runner；
- 选择 OpenCompass、VLMEvalKit 或其他最终评测框架；
- 修改 Benchmark Taxonomy 的 D01–D12、K、C、M 定义；
- 把 Canonical Item 改造成 SFT、ChatML 或模型 API Request Format；
- 把本文件的逻辑字段直接当成数据库表设计。

本文件定义的是 Phase 0 的 Data Specification 设计基线，后续可由人工评审、System Architecture、Evaluation Specification 和 Pilot Design 继续校准。

## 38. 变更记录

| 版本 | 日期 | 变更说明 |
| --- | --- | --- |
| v0.1 | 2026-09-11 | 将原占位结构扩展为 Data Specification v0.1 初始逻辑数据契约；保留所有尚未决定事项为 TBD |
| v0.1 | 2026-09-11 | 补充 backward-compatible 的 answer_requirements.numeric_unit_policy 及对应 Cross-field Validation；版本保持 0.1 |
