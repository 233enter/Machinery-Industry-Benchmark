# Mechanical Industry General Benchmark System Architecture v0.1

Project: Mechanical Industry General Benchmark
Document: System Architecture
Version: 0.1
Status: Reviewed - Baseline
Phase: Phase 0 - Benchmark Design
Current Task: System Architecture v0.1

## 1. 文档定位与设计边界

本文件说明已经在 Project Charter、Project Plan、Benchmark Taxonomy、Data Specification 和 Evaluation Specification 中定义的 Benchmark 方法、数据契约和评测语义，未来如何通过一套可扩展、可复现、可审计的工程系统落地。

本文件覆盖从 Candidate Source Corpus 到 Benchmark 报告的完整生命周期：

~~~text
70k Candidate PDFs
        ↓
Corpus Inventory
        ↓
Source Selection
        ↓
Document Processing
        ↓
Evidence / Asset Construction
        ↓
Question Construction
        ↓
Ground Truth
        ↓
Verification / QA
        ↓
Pilot Benchmark / Benchmark Dataset
        ↓
Model Evaluation
        ↓
Unified Results
        ↓
Reports
~~~

本文件的职责是定义系统边界、组件关系、Artifact Contract、运行和版本管理原则，不是提前完成后续阶段的实现设计。

当前明确不在本次工作中进行：

- 编写实际 Python Pipeline；
- 处理 70k PDF；
- 部署 MinerU 或其他 Parser；
- 调用 LLM 或生成题目；
- 创建数据库或 Review Web UI；
- 构建 Dataset；
- 实现 Evaluation Runner、OpenCompass Adapter 或 VLMEvalKit Adapter；
- 改写已经冻结的 Benchmark Taxonomy、Data Specification 或 Evaluation Specification 语义。

System Architecture 可以定义组件之间必须如何连接，但不改变上位文档对 Canonical Benchmark Item、Ground Truth、Score Semantics、Dataset Membership 或 Evaluation Result 的定义。

## 2. Architecture Baseline Decision

MIGB V1 采用以下基础架构：

~~~text
Offline Batch-first
+
Modular Pipeline
+
Contract-driven Artifacts
~~~

### 2.1 Offline Batch-first

项目的核心负载包括：

- PDF Inventory；
- Document Processing；
- Candidate Generation；
- Verification；
- Dataset Assembly；
- Model Evaluation；
- Reporting。

这些工作主要是可分批、可重启、可审计的离线 Batch Workload。V1 不需要首先构建在线高并发 API、长期运行的大量服务或实时数据处理系统。

### 2.2 Modular Pipeline

每一个 Stage 作为独立模块设计。初期允许全部模块运行在：

~~~text
一个 Python Project
+
CLI / Batch Jobs
+
External Data Root
~~~

中。模块之间通过明确的 Input Contract、Output Contract、Manifest 和版本化 Artifact 连接，而不是依赖隐式的进程内对象。

### 2.3 Contract-driven Artifacts

关键阶段必须产生可独立保存和复核的：

- Versioned Artifact；
- Manifest；
- Source Provenance；
- Config Snapshot；
- Error 或 Verification Record（适用时）。

下游组件只依赖公开的 Contract。具体文件格式可以演进，但不应让下游依赖某个 Parser 或某个评测框架的私有输出格式。

### 2.4 Non-goals

当前 V1 不追求：

~~~text
microservices
service mesh
distributed message queue
real-time streaming
online serving
Kubernetes-native architecture
~~~

这些能力在未来出现明确需求时可以作为架构演进方向，但当前系统优先满足：

~~~text
simple
reproducible
debuggable
batch-oriented
restartable
~~~

## 3. Overall Architecture View

### 3.1 三个 Plane

~~~text
                         MIGB Control Plane
              Config / Registry / Manifest / Orchestration
                                  │
                                  ▼
                           MIGB Data Plane
    Inventory → Parse → Evidence → Generate → QA → Assemble → Evaluate
                                  │
                                  ▼
                          MIGB Artifact Plane
 Source / Parsed / Assets / Items / Snapshots / Results / Reports
~~~

三个 Plane 的边界如下：

| Plane | 主要职责 | 典型内容 |
| --- | --- | --- |
| MIGB Control Plane | 描述一次运行做什么、使用什么版本和配置，以及如何组织 Stage | Config、Registry、Job Manifest、Orchestration、Run Metadata |
| MIGB Data Plane | 执行 Corpus Inventory、来源选择、解析、构题、验证、组装、评测和报告工作 | 各个可独立运行的 Pipeline Module |
| MIGB Artifact Plane | 保存输入引用、处理中间产物、Canonical Records、Snapshot、结果和报告 | Source、Parsed、Evidence、Items、Results、Reports |

三者是逻辑分层，不要求在 V1 部署成三个独立服务或三个独立进程。

### 3.2 端到端数据流

Candidate Source Corpus 首先进入 Corpus Inventory，得到物理文件、逻辑文档、重复关系和质量统计。Source Selection 再依据 Taxonomy、覆盖、质量、权限和污染风险选择 Benchmark Source Corpus 的来源。

选定来源在后续阶段经过 Document Parser Adapter 和 Normalizer，形成可供 Evidence Builder 使用的 Normalized Document。Evidence / Asset Construction 生成文本、公式、表格、图纸和其他视觉证据。Candidate Item Builder 再将 Evidence 转换为统一的 Canonical Candidate Benchmark Item。

Candidate Item 必须通过 Verification / QA，才能被 Dataset Assembly 纳入 Pilot Benchmark 或 Benchmark V1 Dataset。Dataset Snapshot 冻结具体 Item Revision 后，Evaluation 使用 Evaluation Profile、Model Adapter、Answer Parser Registry 和 Evaluator Registry 形成 Evaluation Result，Reporting 从 Canonical Evaluation Result 生成统一报告。

## 4. MIGB Control Plane

Control Plane 回答：

~~~text
运行了什么？
使用什么输入？
使用什么配置？
使用什么代码版本？
产生什么输出？
~~~

### 4.1 控制对象

| 控制对象 | 主要职责 | V1 基线表示 |
| --- | --- | --- |
| Pipeline Config | 定义 Stage 行为参数、过滤条件、资源选项和策略引用 | versioned YAML / JSON |
| Job Manifest | 描述一次重大 Pipeline Run 的输入、输出、配置、版本、状态和资源 | manifest file |
| Version Registry | 记录 Schema、Taxonomy、Prompt、Document Parser、Answer Parser、Evaluator、Adapter、Dataset 和 Report 版本 | Git 管理的版本化文件及 Manifest |
| Taxonomy Registry | 引用当前使用的 Benchmark Taxonomy 版本 | versioned config / registry record |
| Prompt Template Registry | 管理 LLM 辅助构题或评测所使用的 Prompt Template 版本 | versioned template metadata |
| Answer Parser Registry | 管理 Evaluation Answer Parser 的 parser_id、parser_version 及 answer_type / parsing policy compatibility | parser metadata；仅用于 Evaluation Answer Parsing |
| Evaluator Registry | 管理 Answer Type / Task 对应的评分器及版本 | evaluator metadata |
| Model Adapter Registry | 管理模型接口、输入能力和 Adapter 版本 | adapter metadata |
| Dataset Registry | 管理 Candidate Pool、Pilot Benchmark、Benchmark V1 Snapshot 的版本和 Manifest | dataset manifest / registry record |
| Run Metadata | 记录运行环境、资源、状态、错误和可复现信息 | Job Manifest 及其关联 Artifact |

### 4.2 Registry 的 V1 边界

V1 不实现独立的 Registry Service。当前可以使用：

~~~text
versioned config files
+
manifest files
+
Git metadata
~~~

实现上述控制能力。未来是否引入数据库或服务化 Registry，取决于数据规模、并发 Review 和治理要求，不在本文件中提前决定。

Dataset Registry、Source Registry 和各类 Registry Record 可以作为 Artifact 保存，但不能让数据库成为 V1 唯一的 Source of Truth。

这里的 Answer Parser Registry 是 Evaluation 侧的逻辑 Registry，不是 PDF / Document Processing 使用的 Document Parser Adapter Registry。Evaluation Specification 中关于 Answer Parser Registry 与 Evaluator Registry 是否分开物理维护的决策仍保持 TBD；System Architecture 只要求逻辑上能够追踪 parser_id、parser_version 以及与 answer_type / parsing policy 的兼容关系。

## 5. MIGB Data Plane

Data Plane 至少包含以下模块。下表中的 Idempotency expectation 描述语义要求，不代表当前已经实现。

| Module | Responsibility | Input Contract | Output Contract | Failure Boundary | Idempotency expectation | Phase mapping |
| --- | --- | --- | --- | --- | --- | --- |
| A. Corpus Inventory | 扫描 Candidate Source Corpus，建立文件、文档、重复和错误画像 | Candidate Source Corpus、Inventory Config | Corpus Inventory、File Instance Registry、Duplicate Groups、Error Registry、Statistics、Representative Sample Manifest | 单个 File Instance；运行级错误单独记录 | 相同文件引用、哈希和配置不应重复产生冲突记录 | Phase 1 |
| B. Source Selection | 根据质量、覆盖、权限和污染风险选择 Benchmark Source Corpus | Corpus Inventory、Taxonomy、Sample Manifest、Selection Config | Benchmark Source Corpus Registry、Exclusion Registry、Coverage Matrix | 单个 Source Document 或 Selection Batch | Selection 输出通过版本和输入 Manifest 固定 | Phase 2 |
| C. Document Processing | 对已选择来源执行 Document Parser、OCR、Layout 和 Normalization | Selected Source、Document Parser Config、Document Parser Adapter | Raw Parser Artifact、Normalized Document Artifact、Processing Manifest | 单个 Document | 同一来源、Document Parser Version 和 Config 可复用或重建相同语义结果 | Phase 3 |
| D. Evidence / Asset Construction | 从 Normalized Document 构建 Source Evidence 和 Visual Asset | Normalized Document、Evidence Config | Evidence Records、Asset Records、Asset Manifest | 单个 Evidence 或 Asset；源文档不因局部失败而丢失 | Evidence / Asset ID 和输入引用稳定，Transformation 可重放 | Phase 3 |
| E. Benchmark Item Construction | 按 Track Builder 构建统一的 Candidate Item | Evidence、Taxonomy、Generation Config、构题规则 | Canonical Candidate Benchmark Item、Construction Metadata | 单个 Item Revision | 同一输入、配置和生成版本尽量复用；非确定生成必须保留 Raw Output | Phase 4 |
| F. Verification / QA | 运行 Schema、Source、Ground Truth、Calculation、Duplicate、Contamination 和人工检查 | Item Revision、Evidence、Verification Config | Verification Records、QA Issue、Review Queue Manifest | 单个 Item / Revision 或单个检查 | 每种检查按版本写入独立 Record，不静默覆盖 Item | Phase 5 |
| G. Dataset Assembly | 执行 Coverage、Balance、Duplicate、Contamination 和 Quality Gate，冻结集合 | Accepted Item Revisions、Assembly Config | Dataset Snapshot、Dataset Manifest、Membership Records | 单个 Item Membership、Snapshot 或 Assembly Run | 相同输入和配置生成同一 Snapshot 身份；历史 Snapshot 不漂移 | Phase 5 / Phase 7 |
| H. Evaluation | 绑定 Dataset Snapshot、Evaluation Profile、Model Adapter 并生成结果 | Frozen Dataset Snapshot、Model、Profile、Runner Config | Canonical Response、Evaluation Result、Run Manifest | 单个 Evaluation Item；基础设施错误可上升到 Run | 已完成结果可复用；失败项单独重试且不覆盖历史结果 | Phase 6 / Phase 8 |
| I. Reporting | 从 Canonical Evaluation Result 生成整体、分项和诊断报告 | Result Store、Report Config、版本 Manifest | JSON、CSV / Parquet、Markdown、HTML 等报告 Artifact | 单个 Report 或 Report Slice | 同一 Result Snapshot、配置和代码版本可重建同一语义报告 | Phase 6 / Phase 8 |

每个模块都必须将输入、输出、版本、状态和错误通过 Artifact 或 Manifest 显式传递。

## 6. MIGB Artifact Plane 与 Contract

### 6.1 Artifact 分层

Artifact Plane 的逻辑层如下：

~~~text
Source Corpus
Inventory Artifacts
Raw Parser Artifacts
Normalized Document Artifacts
Evidence Records
Visual Assets
Candidate Items
Verification Records
Accepted Items
Dataset Snapshots
Evaluation Runs
Evaluation Results
Reports
~~~

Artifacts 与 Code Repository 分离。70k PDF、大规模 Parsed Artifact、Visual Asset、Candidate Pool 和 Evaluation Raw Response 不直接进入 Git Repository。

Git 主要保存：

- code；
- docs；
- configs；
- schemas；
- small manifests；
- tests；
- version metadata。

### 6.2 Artifact Contract 通用要求

具体 Artifact Schema 由对应文档和后续实现定义，但关键 Artifact 通常需要能够关联：

~~~text
artifact_id
artifact_type
schema_version
source_or_input_refs
output_refs
source_provenance
job_run_id
code_version
tool_versions
config_snapshot
checksum
storage_reference
status
created_at
~~~

上述是架构层的审计要求，不替换 Data Specification 对 Canonical Benchmark Item、Source Evidence、Ground Truth 和 Dataset Membership 的规范。

任何被跳过、失败、替代或撤回的 Artifact，都必须在对应 Error Registry、Verification Record、Membership Record 或 Manifest 中留下可解释的状态。

### 6.3 Artifact Immutability and Lineage

Canonical Pipeline Artifact 默认采用：

~~~text
append / version / supersede
~~~

而不是 silent in-place overwrite。尤其适用于：

- Normalized Document；
- Evidence Record；
- Visual Asset metadata；
- Candidate Item Revision；
- Verification Record；
- Dataset Snapshot；
- Evaluation Result；
- Run Manifest。

如果内容发生实质改变，应创建新的 Artifact Version、新的 Item Revision、新的 Dataset Version 或新的 Evaluation Run，具体取决于变化所在的实体。历史引用必须继续解析到历史 Artifact，不能因后续修订而静默漂移。

允许原地删除或覆盖的主要对象是：

~~~text
cache
temporary workspace
rebuildable intermediate scratch data
~~~

但即使 Cache 被删除，也必须能够从 Canonical Input、Config 和 Tool Version 重建结果。Cache != Source of Truth。

### 6.4 Artifact Lineage

source_or_input_refs 是本 System Architecture 采用的 Canonical Lineage Reference 字段。它用于形成：

~~~text
Output Artifact
→ Input Artifact(s)
→ Source / Previous Stage
~~~

的 Lineage，回答“这个 Evidence、Item 或 Result 是由什么输入和哪个 Job 产生的”。本架构不再另设一个与 source_or_input_refs 完全重复的 parent_artifact_refs[] 字段。需要追踪的上游 Artifact、Source Document、前一 Stage 输出和相关 Job，应统一通过 source_or_input_refs 及其对应的 Manifest 引用表达。

Lineage 引用必须随 Artifact Version、Item Revision、Dataset Version 和 Evaluation Run 一起保留。删除 Cache 或临时中间文件不能破坏 Canonical Artifact 对其输入和生成过程的可解释性。

## 7. External Data Root

大规模数据正式使用独立的 MIGB_DATA_ROOT 概念。不要把实际绝对路径写死在代码、文档 Contract 或 Manifest 示例中。

概念目录结构如下：

~~~text
MIGB_DATA_ROOT/
  corpus/
  inventory/
  parsed/
  evidence/
  assets/
  candidates/
  datasets/
  evaluations/
  reports/
  cache/
~~~

实际路径、挂载方式和存储后端由环境配置决定。

仓库中的 data/ 目录不应默认承载 70k PDF。它只用于：

- README；
- tiny samples；
- test fixtures；
- example data。

如果需要在 Git 中保存小型示例，必须明确标记为 Example / Fixture，不能让示例路径被误认为生产数据路径。

## 8. Storage Strategy v0.1

V1 采用 Hybrid File-based Storage 作为基线。不同类型的数据使用适合其结构的文件形式，具体后端通过 storage_reference 和抽象接口隔离。

### 8.1 Source / Binary Assets

以下内容属于 Source 或 Binary Assets：

- PDF；
- page images；
- figure crops；
- drawing crops；
- table images；
- charts；
- equipment images；
- multi-view assets。

使用 Filesystem / Object-storage-compatible abstraction。V1 可以首先使用 POSIX filesystem，未来可以迁移到 S3、MinIO 或 shared storage，而不改变 Canonical Benchmark Item。

### 8.2 Corpus Inventory

Corpus Inventory 推荐使用 Parquet：

- 70k Document Metadata 属于表格型数据；
- 便于统计、过滤和分区；
- 可直接被 DuckDB、Python 等工具分析；
- 不依赖数据库才能读取。

### 8.3 Canonical Benchmark Items

Canonical Benchmark Items 推荐使用 JSONL 作为主要 Canonical Serialization：

- Item 结构可能包含 nested object；
- 一条 Item 一行，便于 Schema Validation；
- 对小型样本具备可读性；
- 与模型框架解耦。

大型 Dataset Snapshot 可以另外生成 Parquet analytical view，但 JSONL 仍保持 Canonical Semantic Representation。

### 8.4 Evaluation Results

Evaluation Results 推荐使用 Parquet，因为常见分析粒度是：

~~~text
Model × Item
~~~

原始 Evaluation Result 和 Evaluation Run Manifest 必须同时保留。Report 不是唯一结果来源。

### 8.5 Config / Manifest

Config / Manifest 使用 YAML / JSON。运行时必须保存 Config Snapshot，防止配置文件后续变更导致历史 Run 无法解释。

### 8.6 Analytics Query Layer

DuckDB 是初期本地或 Server Analytics Engine 的 Recommended baseline candidate，可用于：

- query Parquet；
- Corpus statistics；
- Dataset balance；
- Evaluation result analysis。

DuckDB 不是 Canonical Data Contract。Data Specification 不依赖 DuckDB，未来替换 Analytics Engine 不应改变 Canonical Artifact。

## 9. Corpus Inventory Architecture

Corpus Inventory 是 Phase 1 第一项真正实现的系统。其输入是 Candidate Source Corpus，输出至少包括：

~~~text
Corpus Inventory
File Instance Registry
Duplicate Groups
Error Registry
Corpus Statistics
Representative Sample Manifest
~~~

### 9.1 Physical File Instance 与 Logical Source Document

必须区分：

| Entity | 含义 |
| --- | --- |
| Physical File Instance | 一个实际存在的文件，例如某个目录中的 A.pdf |
| Logical Source Document | 在内容、元数据、重复分析和 document-family 关系基础上识别的逻辑文档 |

建议引入 Corpus Inventory 专用的 Operational Entity：

~~~text
CorpusFileInstance
  file_instance_id
  source_locator
  file_hash
  file_size
  scan_status
  inventory_status
  document_id                 # null / provisional / resolved
  document_family_id          # null / partial / resolved
~~~

CorpusFileInstance 是 Inventory 的运行实体，不是 Benchmark Item Data Specification 的一部分。

### 9.2 Document Identity Resolution

Physical File Instance 发现、Logical Source Document 识别和 document-family 关联是不同步骤。建议采用以下逻辑流程：

~~~text
Physical File Discovery
        ↓
file_instance_id
        ↓
File Hash / Metadata / Exact Duplicate Analysis
        ↓
Logical Document Resolution
        ↓
document_id
        ↓
Document-family Resolution
        ↓
document_family_id
~~~

规则如下：

- 发现一个 Physical File Instance 后即可稳定分配 file_instance_id；
- document_id 只有在完成必要的 Logical Document Resolution 后才视为 resolved；
- 早期 Inventory Record 允许 document_id = null 或 provisional，不得为了填字段而默认 1 PDF File = 1 Logical Document；
- document_family_id 比 document_id 更高层，Phase 1 可以只完成部分 family resolution；
- document-family Resolution 通常需要综合 metadata、edition、hash、similarity、filename / title 和 sample inspection；
- document_id 不等于 file_hash，也不因文件路径变化而改变。

路径不能作为稳定的 document_id。Logical Document Resolution 需要结合：

- content hash；
- document metadata；
- duplicate analysis；
- document-family 关系。

文件级哈希的 baseline 推荐 SHA-256，用于 exact file duplicate、完整性检查和缓存键。Logical document identity 与 exact binary file hash 不是同一个概念。

同一本书可能存在扫描版、OCR 版、重排版或不同来源，因此不能简单规定 document_id 等于文件哈希。具体 document_id 生成算法保持 Implementation Decision。

document-family_id 用于关联版本、扫描版 / 文本版、同一资料不同来源和高度重复资料。

### 9.3 Phase 1 Light Inventory

Phase 1 默认禁止：

~~~text
70k PDF
→
full MinerU processing
~~~

Inventory Stage 只运行相对便宜的操作，例如：

- filesystem scan；
- file metadata；
- file hash；
- page count；
- PDF validity；
- encryption；
- text layer detection；
- lightweight scan / text heuristic；
- exact duplicate detection；
- lightweight sampling。

需要高成本 OCR、Layout、Formula、Table 或 Drawing 解析的工作进入 Phase 3。

### 9.3 Representative Sample Pipeline

Phase 1 应输出 Representative Sample Manifest。初始规模可以约为 100–300 PDF，最终数量仍需根据覆盖和成本调整。

Representative Sample 用于在 Phase 3 正式大规模解析前验证：

- Parser；
- OCR；
- Table；
- Formula；
- Drawing；
- Scan PDF；
- Text PDF；
- Long documents。

Document Parser 技术选型必须先通过 Representative Sample 验证，不能在没有样本 QA 的情况下直接对整个 Benchmark Source Corpus 做高成本解析。

## 10. Source Selection Architecture

Source Selection Component 接收：

~~~text
Corpus Inventory
Taxonomy v0.1
Representative Sample
~~~

输出：

~~~text
Benchmark Source Corpus Registry
Exclusion Registry
Coverage Matrix
Source Quality Metadata
~~~

Selection 需要支持以下维度：

- authority；
- quality；
- coverage；
- parseability；
- duplicate family；
- rights；
- contamination risk。

70k Candidate Source Corpus 不要求全部进入 Benchmark Source Corpus，V1 也不要求使用完全部 7 万本 PDF。

“PDF 数量最多的领域”不能自动成为 Benchmark 权重最高的领域。Source Selection 的结果应同时记录纳入和排除理由，并能够回溯到 Corpus Inventory 与对应版本。

## 11. Document Processing Architecture

Phase 3 的 Parser 架构必须采用 Adapter Boundary：

~~~text
            Document Parser Adapter Interface
                    /           \
                MinerU         Future Parser
                    \           /
                Normalized Document
~~~

MinerU 可以是首选候选工具，但 Canonical downstream 不允许依赖 MinerU 私有输出格式。Document Parser Adapter 至少要负责将不同 Document Parser 的原始结果转换到系统可接受的内部接口。

### 11.1 Raw Parser Artifact 与 Normalized Artifact

系统必须同时区分：

- Raw Parser Artifact：Document Parser 原始 JSON、Markdown、Layout Objects、OCR Objects 等；
- Normalized Document Artifact：经 Normalizer 转换后供下游使用的稳定逻辑模型。

下游 Evidence Builder 只依赖 Normalized Document，不直接读取某个 Document Parser 的私有格式。保留 Raw Parser Artifact 用于问题排查、Document Parser 对比和未来重新 Normalization。

### 11.2 Normalized Document Model

System Architecture 只定义逻辑层，不在本次创建具体 Schema。逻辑模型至少包含：

~~~text
document
pages[]
blocks[]
~~~

Block 类型可以包括：

~~~text
text
formula
table
figure
drawing
heading
caption
~~~

每个 Block 至少能够关联：

~~~text
document_id
page_index
bbox
block_type
content/reference
parser_provenance
~~~

Normalized Document Model 不与 Canonical Benchmark Item Schema 合并为一个对象。

### 11.3 Document Parser 与 Answer Parser 的命名边界

本架构明确区分两个不同组件：

| 名称 | 作用 | 典型阶段 | 版本追踪方式 |
| --- | --- | --- | --- |
| Document Parser Adapter | 处理 PDF / Document，输出 Raw Parser Artifact 和 Normalized Document | Phase 3 - Corpus Processing | Document Parser ID / Version、Tool Versions |
| Answer Parser Registry | 处理模型 Response，按 Evaluation Policy 提取 Parsed Answer 和 Parse Status | Phase 6 / Phase 8 - Evaluation | parser_id / parser_version、answer_type / parsing policy compatibility |

两者不是同一个组件，也不共享隐含的注册或版本语义。Evaluation 侧只通过 Answer Parser Registry 追踪 parser_id / parser_version；PDF / Document Processing 侧使用 Document Parser Adapter。Evaluation Specification 对 Answer Parser Registry 与 Evaluator Registry 是否分开物理维护的决策仍保持 TBD。

## 12. Evidence / Asset Architecture

### 12.1 Evidence Builder

Evidence Builder 的输入是 Normalized Document，输出是 Source Evidence 和相关 Visual Asset Reference。职责包括：

- Evidence segmentation；
- Page / bbox mapping；
- text、formula、table、figure reference；
- asset extraction；
- Source Provenance preservation。

必须能够形成以下追溯链：

~~~text
Item
  →
Evidence
  →
Document
  →
Page
  →
bbox
~~~

Source Evidence 是 Source Provenance 的核心实体。一条 Benchmark Item 可以引用一个或多个 Evidence。具体字段遵循 Data Specification；架构只负责保证引用、存储和版本关系不丢失。

### 12.2 Asset Pipeline

Visual Asset 可以包括：

- page image；
- figure crop；
- drawing crop；
- table image；
- chart；
- equipment image；
- multi-view asset。

每个 Asset 至少应能保留：

~~~text
asset_id
source_evidence_id
checksum
storage_reference
visual_type
~~~

原始页面和裁剪 Asset 分开保存。不得覆盖 Source 原图。每个 crop、render、resize、conversion 等 Transformation 都必须能够追溯到输入 Asset / Evidence、Transformation 参数、输出 checksum 和对应运行版本。

## 13. Benchmark Construction Architecture

Benchmark Construction 拆分为三个 Builder，但三个 Builder 必须输出同一套 Canonical Candidate Benchmark Item：

~~~text
Candidate Item Builder
├── Knowledge Builder
├── Calculation Builder
└── Multimodal Builder
~~~

不能为 Knowledge、Calculation、Multimodal 分别创造互不兼容的数据格式。Candidate Item 不等于 accepted Item，所有 Candidate Item 都必须进入 Verification / QA。

### 13.1 Knowledge Builder

输入：

~~~text
Evidence
Taxonomy
Generation Config
~~~

可以支持：

- Human authored；
- Rule / template assisted；
- LLM assisted。

输出只是 Candidate Item。LLM 辅助生成不能默认成为最终 Ground Truth 来源，Knowledge Item 应尽量回溯到原始权威资料并保留 Source Provenance。

### 13.2 Calculation Builder

Calculation Builder 的逻辑流程是：

~~~text
Formula Evidence
      ↓
Formula Structuring
      ↓
Variables / Constraints
      ↓
Parameterized Generator
      ↓
Deterministic Solver
      ↓
Ground Truth
      ↓
Verification
~~~

Solver 的候选实现可以包括 Python、SymPy 或 domain-specific deterministic code。LLM 不能作为 Numeric Ground Truth Calculator 的唯一来源。计算题的 Formula、Variables、Constraints、Intermediate Values 和验证记录应遵循 Data Specification；Formula Registry 是否独立存储仍是 Architecture Open Question。

### 13.3 Multimodal Builder

输入：

~~~text
Visual Asset
+
Evidence
+
Taxonomy
~~~

输出 T3 Candidate Item，并要求：

~~~text
visual_dependency_required = true
~~~

Multimodal Builder 只声明题目设计要求视觉依赖，不负责自己宣布 visual_dependency_check 已通过。后续 Verification / QA 的 Visual Dependency Checker 必须验证：如果移除或无法看到视觉信息，题目是否仍能仅凭文本得到相同答案；如果可以，则应进入 review / revision。

## 14. Generation Adapter 与 Prompt Registry

### 14.1 Generation Adapter Layer

所有 LLM 辅助构题通过统一的 Generation Adapter 概念接入。Provider 可以是：

- OpenAI-compatible endpoint；
- local vLLM；
- other API。

架构不绑定具体厂商。每一次辅助生成尽可能记录：

~~~text
model
model_version
prompt_template
prompt_template_version
generation_config
~~~

API Key、Token 和 Secret 不进入 Artifact、Dataset、Manifest 或日志。

Generation Adapter 的输出必须被标记为构题过程产物，不能绕过 Ground Truth、Verification / QA 或人工审核边界。

### 14.2 Prompt Template Registry

Prompt Template Registry 至少保存：

~~~text
prompt_template_id
version
purpose
input_contract
output_contract
~~~

每条 Candidate Item 不需要重复保存整份 Prompt。Prompt 变更必须产生新版本，运行时保存其 Config Snapshot 和 Registry 引用。

## 15. Verification / QA Architecture

系统设计统一 Verification Pipeline，至少包括：

~~~text
Schema Validator
Source Verifier
Ground Truth Verifier
Calculation Verifier
Unit Checker
Duplicate Detector
Ambiguity Checker
Visual Dependency Checker
Contamination Checker
Human Review
~~~

每个 Verifier 接收 Item Revision，输出独立的 Verification Record。Verification Record 至少能够包含：

~~~text
verification_id
verification_type
method
verifier_type
status
timestamp
notes
artifact_refs
~~~

Verifier 不得静默修改 Item。如果发现问题，应进入 review / revision 流程，必要时产生新的 Item Revision 或 QA Issue。

### 15.1 Ground Truth 验证边界

Ground Truth 的可信度优先于题目数量：

- Knowledge 题尽量回溯原始权威资料；
- Calculation 题优先用程序、公式或规则验证；
- Multimodal 题需要验证图像或区域是否真实参与解题；
- LLM 可以辅助构题或审核，但不能默认作为最终 Ground Truth 来源。

如果专家资源有限，系统必须支持 source verification、programmatic verification、cross-check、抽样审核和人工升级等不同 Verification Record 类型；具体 Ground Truth 验证策略仍需在后续 Data Specification / Pilot Design 和资源决策中确定。

### 15.2 Human Review Queue

系统预留 Human Review Queue，但 Phase 0 不设计 Web UI。V1 可以通过以下方式完成 Review：

- manifest；
- CSV / JSONL export；
- simple internal tool。

Review Queue 至少应能够引用 Item Revision、Evidence、问题类型、优先级、处理人、结论和时间。是否需要完整 Annotation Platform 保持为后续决策，不在 Architecture v0.1 中提前要求。

## 16. Duplicate Architecture

必须区分三个层级：

~~~text
File Duplicate
Document-family Duplicate
Benchmark Item Duplicate
~~~

对应关系为：

~~~text
file_hash
document_family_id
item duplicate groups
~~~

Benchmark Item Duplicate 还可以进一步区分：

~~~text
exact
near
semantic
~~~

这些层级不能混为一个 dedup field。

其中：

- File Duplicate 关注相同二进制文件；
- document-family Duplicate 关注同一本书不同版本、扫描版 / 文本版、同一资料不同来源和高度重复资料；
- Benchmark Item Duplicate 关注题目内容、轻微改写或语义等价题目。

Document-family 相同不必然表示题目完全相同，但在 Contamination 检查和 Dataset Split 决策中必须共同考虑。

## 17. Contamination Architecture

至少存在两条检查链：

~~~text
Benchmark Source
vs
Training Corpus
~~~

以及：

~~~text
Benchmark Item
vs
Known Benchmark / Other MIGB Split
~~~

如果未来 CPT / SFT Corpus 与 70k Candidate Source Corpus 有交集，系统必须支持使用以下信息建立隔离关系：

- document_id；
- document_family_id；
- hash / similarity。

Benchmark Source Registry 需要能够导出：

~~~text
training_exclusion_manifest
~~~

供未来 CPT / SFT Pipeline 使用。污染控制不能只检查题目字符串，也必须考虑 document-family 级别的数据污染。

## 18. Dataset Assembly 与 Snapshot

### 18.1 Dataset Assembly

Dataset Assembly 接收 accepted Item Revisions，依次或按可解释的策略执行：

~~~text
Coverage Check
Balance Check
Duplicate Check
Contamination Check
Quality Gate
~~~

输出：

~~~text
Dataset Snapshot
Dataset Manifest
Dataset Membership Records
~~~

Snapshot 必须冻结：

~~~text
dataset_version
item_id
item_revision
~~~

历史 Dataset Snapshot 永不自动漂移。

### 18.2 Candidate Pool、Pilot Benchmark 与 Benchmark V1

系统以逻辑 Collection 区分：

~~~text
Candidate Pool
Pilot Benchmark
Benchmark V1
~~~

不能通过移动、覆盖同一文件或覆盖同一 Item 来表达状态变化，而要通过 Dataset Membership 记录集合关系和历史。

同一个 Item Revision 可以存在于多个历史 Snapshot。若 Question、Ground Truth、Source Provenance、关键 Taxonomy、视觉依赖或验证结论发生实质变化，应使用新的 Item Revision，并由新的 Dataset Version 明确引用。

### 18.3 Internal View 与 Export View

系统必须实现以下概念边界：

~~~text
Canonical Internal Dataset
        ↓
Export Builder
        ↓
Public / External Export View
~~~

Export Builder 根据以下信息决定导出内容：

~~~text
visibility
rights_status
release policy
~~~

可能被单独控制的内容包括：

- Evidence；
- source title；
- Visual Asset；
- explanation；
- Verification。

禁止直接把 Canonical Internal Dataset 整包发布。题目可公开不代表 Source PDF、Image Crop 或完整 Evidence 必须公开。

## 19. Evaluation Architecture

System Architecture 只规定 Evaluation 组件的连接方式，严格遵守 Evaluation Specification，不改变 Score Semantics。

逻辑结构如下：

~~~text
Dataset Snapshot
       ↓
Evaluation Profile
       ↓
Model Adapter
       ↓
Inference Backend
       ↓
Canonical Response
       ↓
Answer Parser Registry
       ↓
Evaluator Registry
       ↓
Evaluation Result
       ↓
Aggregator
       ↓
Report
~~~

### 19.1 主要组件边界

| Component | 输入 | 输出 | 主要边界 |
| --- | --- | --- | --- |
| Dataset Snapshot Loader | Frozen Dataset Snapshot、Dataset Manifest | 固定顺序的题目和输入 Asset | 不改变历史 Snapshot，不自动使用最新 Item Revision |
| Evaluation Profile Loader | Evaluation Profile、Evaluation Specification Version | Prompt、Decoding、输入和评分引用 | 不在运行时隐式改变官方规则 |
| Model Adapter | Model metadata、输入题目和 Asset | 规范化请求及模型 Response | 不查看 Ground Truth，不把模型差异隐藏为题目差异 |
| Inference Backend | Adapter request | Raw Model Response、运行状态 | 正常错误与基础设施错误分开记录 |
| Answer Parser | Model Response、Answer Parser Version | Parse Status、Parsed Answer | 只提取和规范化，不替模型修答案 |
| Evaluator | Parsed Answer、Canonical Ground Truth、Evaluator Version | Item Score、正确性和错误类别 | 遵循 Evaluation Specification，不静默重算历史 Result |
| Aggregator | Item-level Evaluation Result | Track、Domain、Capability、Difficulty、Overall 等汇总 | 使用批准的聚合语义，保留原始结果 |
| Report Builder | Canonical Evaluation Result、Report Config | 报告和诊断视图 | Report 不是唯一结果来源 |

Evaluation Result 独立于 Canonical Benchmark Item，至少能够关联：

~~~text
run_id
item_id
item_revision
dataset_version
inference_status
raw_response
parse_status
parsed_answer
parser_id
parser_version
evaluator_id
evaluator_version
item_score
is_fully_correct
error_category
judge_result
judge_model（如有）
judge_model_version（如有）
judge_prompt_version（如有）
rubric_version（如有）
latency
usage
timestamp
~~~

Evaluation Specification 是 Evaluation Result 语义的权威来源；System Architecture 只负责存储和连接这些字段。Judge 相关字段均为 Conditional，本文件不重新定义 Judge Scoring Semantics，具体语义直接引用 Evaluation Specification。

如果 Inference 没有成功，必须按照 Evaluation Specification 的约束记录 Parsed Answer、Parse Status 和 Item Score 的不可用状态。Latency 和 Usage 属于运行信息，不进入能力 Score。

### 19.2 Evaluation Backend Adapter

架构允许：

~~~text
Custom Runner
OpenCompass Adapter
VLMEvalKit Adapter
~~~

最终采用哪一种或哪几种仍可后续决定。推荐的连接方式是：

~~~text
OpenCompass / VLMEvalKit
        ↓
Framework Adapter
        ↓
Canonical Evaluation Result
~~~

OpenCompass、VLMEvalKit 或其他 Framework 不能成为 Result Schema 本身。

### 19.3 Runner-specific Execution 与 Unified Result Contract

Text / Calculation 和 Multimodal 可能最适合不同 Runner。因此采用：

~~~text
Runner-specific Execution
+
Unified Result Contract
~~~

而不是强制所有 Track 进入一个框架。所有 Runner 都必须遵守 Dataset Snapshot、Prompt Policy、Raw Response Preservation、Answer Parser、Item Evaluator、Aggregation 和 Result Provenance 约束。

不同 Answer Type / Task 的 Evaluator 通过 Evaluator Registry 版本化。框架接入前应通过 Evaluator Conformance Test，至少覆盖正确、错误、Numeric Tolerance、单位转换、Invalid Output、Multiple Choice、Structured Answer 和 Multimodal Asset 等 Golden Cases。

## 20. Result Store 与 Reporting Layer

### 20.1 Result Store

Evaluation Result 推荐使用 Parquet 保存 Model × Item 级结果，并同时保存 Evaluation Run Manifest。Manifest 至少包括：

- Dataset Version；
- Item Revisions；
- Evaluation Profile；
- Model；
- Adapter；
- Prompt；
- Generation Config；
- Parser；
- Evaluator；
- Judge；
- Runtime Environment。

原始 Result 必须保留。不得只保存最终 Report 而丢失 Raw Response、Parse Status、Evaluator Version 或错误类别。

### 20.2 Reporting Layer

Reporting 读取 Canonical Evaluation Result，可以输出：

~~~text
Overall
Track
Domain
Capability
Difficulty
Answer Type
Modality
Error Analysis
~~~

报告格式可以包括：

- JSON；
- CSV / Parquet；
- Markdown；
- HTML。

具体 Dashboard 技术不是 Phase 0 的决策。报告必须能够回溯到 Dataset Version、Item Revision、Evaluation Run 和对应版本的 Parser / Evaluator。

## 21. Pipeline Orchestration

V1 优先采用 CLI / Batch Job。每个 Stage 应能够独立运行。未来的概念命令可以包括：

~~~text
inventory
parse
build-evidence
generate
verify
assemble
evaluate
report
~~~

这里只表示模块边界，不要求当前实现 CLI。

如果未来 Pipeline 的规模、依赖和并发复杂度明显增加，再考虑 workflow engine、queue 或 distributed scheduler。不要从 Airflow、Kubernetes 或 Microservices-first 起步。

## 22. Job Manifest、Code Version 与 Config Snapshot

### 22.1 Job Manifest

每次重大 Pipeline Run 应生成 Job Manifest，至少包含：

~~~text
job_run_id
stage
input_manifest
config_snapshot
code_version
tool_versions
started_at
completed_at
status
output_manifest
error_manifest
resource_summary
~~~

Job Manifest 是复现、重启、错误审计和资源估算的重要基础。

### 22.2 Code Version

Job、Dataset Build 和 Evaluation Run 应尽可能记录：

~~~text
git_commit
~~~

如果工作区不是 clean，建议记录：

~~~text
dirty = true
~~~

正式 Benchmark Release Build 是否强制 dirty = false 仍需在 Release Gate 前确认。

### 22.3 Config-driven Pipeline

行为参数尽量放在 configs/，而不是硬编码。未来可以按 Stage 提供：

- inventory config；
- parser config；
- generation config；
- verification config；
- dataset assembly config；
- evaluation config。

Config 必须版本化，运行时生成 Config Snapshot，并在 Job Manifest 中记录引用。

## 23. Idempotency、Restartability 与 Failure Isolation

### 23.1 Idempotency

每个 Stage 尽量满足：

~~~text
same input
+
same config
+
same tool version
→
same semantic output
~~~

对于 LLM Generation 等非完全确定组件，必须记录 model、version、generation config、seed（如支持）和 Raw Output。不得声称其绝对 deterministic。

### 23.2 Restartability / Checkpointing

70k PDF Pipeline 必须支持：

~~~text
partial failure
restart
resume
~~~

一个 PDF 或一个 Item 失败，不能要求全部 70k 重新运行。每个 Document / Item 应成为合理的 Failure Unit。失败应进入 Error Registry 或 Error Manifest，并支持后续重试。

### 23.3 Failure Isolation

至少区分：

~~~text
Document-level Failure
Evidence-level Failure
Item-level Failure
Evaluation Item Failure
Run-level Failure
~~~

Pipeline 不允许 silent failure。任何被跳过、延后或排除的数据，都必须有明确原因、状态和对应 Artifact / Manifest 引用。

### 23.4 Caching

可以支持 content-aware cache。例如：

~~~text
PDF hash + Document Parser Version + Config
~~~

可以作为解析缓存的候选键。但 Cache 不属于 Canonical Source of Truth，必须可以删除 Cache 后重新构建结果。

## 24. Observability、Logging 与 Secrets

### 24.1 Observability

每个 Batch Stage 至少记录：

~~~text
processed_count
success_count
failure_count
skipped_count
duration
~~~

适用时可以记录：

- CPU time；
- GPU time；
- LLM token usage；
- API cost；
- disk usage。

这些信息用于 debugging、resource planning 和 cost estimation。V1 baseline 不要求现在设计 Prometheus / Grafana 服务，简单日志和运行统计足够。

### 24.2 Logging

日志至少包含：

~~~text
job_run_id
document_id / item_id
stage
severity
error_category
message
timestamp
~~~

日志不得记录 API Key、Secret 或其他敏感凭证。大量 Model Raw Response 应进入 Artifact Store，而不是全部塞入 console log。

### 24.3 Secrets

Secrets 使用：

~~~text
environment variables
or
future secret management solution
~~~

不得将 Secret：

- commit to Git；
- 写入 Dataset；
- 写入 Run Manifest；
- 写入日志。

Architecture 不绑定具体 Secret Manager。

## 25. Copyright、Access Control 与数据治理

系统至少从逻辑层区分：

~~~text
internal_only
exportable
withheld
needs_review
~~~

Asset / Evidence 的导出必须同时检查：

~~~text
visibility
+
rights_status
~~~

原始 70k PDF 默认属于 internal source corpus，除非明确知道允许重新分发。Candidate Source Corpus、Benchmark Source Corpus、Evidence、Asset、Question、Answer、Explanation 和 Verification 的可见性可以不同。

Copyright、Data Usage Constraints 和 CPT / SFT 使用边界是全生命周期的治理要求，不能因为某个 Item 可评测就推定其全部 Source Asset 可公开。

## 26. Repository Logical Module Layout

本次只设计未来模块，不创建代码文件或重构仓库。建议未来的逻辑布局为：

~~~text
src/
  migb/
    inventory/
    source_selection/
    parsing/
    evidence/
    generation/
    verification/
    dataset/
    evaluation/
    reporting/
    adapters/
    registries/
    common/
~~~

其中 adapters/ 可以进一步承担：

- Document Parser Adapters；
- LLM Adapters；
- Evaluation Framework Adapters。

具体 Python Package、CLI 入口和依赖组织留给实现阶段。

## 27. Future Schema 与 Tests Layout

未来可以使用：

~~~text
schemas/
tests/
configs/
~~~

Tests 至少应覆盖：

- Schema Validation；
- Parser Normalization；
- Ground Truth Calculation；
- Evaluator Golden Cases；
- Dataset Snapshot；
- Adapter Conformance。

本次不创建代码、Schema 文件、数据库或测试实现。

## 28. Phase Mapping

| Phase | Architecture Components Activated |
| --- | --- |
| Phase 0 - Benchmark Design | Architecture baseline、三 Plane、Artifact Contract、版本和 Manifest 原则、Storage baseline、未来模块边界 |
| Phase 1 - Corpus Inventory | Corpus Scanner、Inventory Store、Duplicate Detector、Representative Sampler |
| Phase 2 - Taxonomy Calibration & Source Selection | Source Registry、Coverage Analyzer、Training Exclusion Manifest、Source Quality Metadata |
| Phase 3 - Corpus Processing | Document Parser Adapter、Normalizer、Evidence Builder、Asset Store |
| Phase 4 - Question Construction & Ground Truth | Candidate Builders、Formula / Calculation Pipeline、Generation Adapter、Prompt Template Registry |
| Phase 5 - Quality Control & Pilot Benchmark | Verification Pipeline、QA、Human Review Queue、Pilot Assembler、最小 Evaluation Runner 准备 |
| Phase 6 - Model Validation & Calibration | Minimal Evaluation Runner、Result Store、Calibration Analysis、多个能力层级模型运行条件 |
| Phase 7 - Benchmark V1 Expansion | Scale-out Candidate Construction、QA、Contamination Control、Benchmark V1 Assembly、Dataset Snapshot |
| Phase 8 - Evaluation & Reporting | Framework Adapters、Production Evaluation、Automatic Scoring、Reporting、Leaderboard-ready outputs |

表中的 Activated 表示该阶段需要启用或验证的架构组件，不表示本文件已经实现这些组件，也不改变 Project Plan 对各 Phase 的交付边界。

## 29. Architecture Gates

系统不能一次性全部开发。以下 Architecture Gate 是系统就绪检查，与 Project Plan 的 Gate 0–8 互补，不改变其项目决策含义。

### Architecture Gate A

Phase 1 Inventory Pipeline 验证完成后，才批准并实施大规模 Document Parser Execution。验证内容至少包括文件识别、Inventory Contract、错误处理、重复关系和 Representative Sample Manifest 是否可用。

### Architecture Gate B

Representative Sample Document Parser QA 通过后，才允许批量解析 Benchmark Source Corpus。Document Parser、OCR、Table、Formula、Drawing、Scan PDF、Text PDF 和长文档的适用性必须有可审计证据。

### Architecture Gate C

Canonical Candidate Benchmark Item 与 Verification Pipeline 可以运行后，才扩大 Candidate Generation。必须先证明统一 Item Contract、Ground Truth 记录和 Verification Record 可以闭环。

### Architecture Gate D

Pilot Evaluation Runner Conformance 通过后，才运行多个 Baseline / Anchor Models。Conformance 至少要覆盖 Dataset Snapshot 绑定、Canonical Response、Answer Parser、Evaluator、Result Contract 和异常处理。

## 30. Resource Dependency

当前服务器和存储资源尚未提供。开始 Phase 1 Implementation 前，需要用户或项目方提供、确认或授权：

~~~text
70k PDF actual path
total corpus size
directory structure

server OS
CPU
RAM
GPU
GPU memory
disk capacity
free disk
filesystem
network/storage layout
Docker availability

internet/API accessibility
LLM endpoints if any
~~~

还需要明确 Candidate Source Corpus 的访问权限、版权限制、Source Asset 的处理边界以及未来 CPT / SFT Corpus 的隔离信息。

本文件不假定具体服务器型号、机器数量、GPU、磁盘容量、网络拓扑或 Docker 可用性。

## 31. Storage Capacity Planning

Parsed Artifact、Page Image、Visual Asset、Cache 和临时工作区可能比原 PDF Corpus 占用更大空间。正式进入 Phase 3 前，必须通过 Representative Sample 估算：

~~~text
raw corpus size
parser expansion ratio
page image size
asset size
cache size
temporary workspace
~~~

扩容决策应使用实际样本数据和保守的峰值工作空间估算，不在 Phase 0 编造固定倍率。估算结果应进入 Phase 3 Resource Plan 和对应 Job / Gate Review Record。

## 32. Compute Planning

不同阶段的资源性质不同：

- Phase 1 主要使用 CPU 和 Disk I/O；
- Phase 3 的 OCR、Layout 和 VLM Parser 可能需要 GPU；
- Phase 4 的 LLM Generation 需要 API 或 Local Inference；
- Phase 6 的 Multi-model Evaluation 可能成为主要 GPU / API Cost。

Architecture 只描述资源性质，不填写未知的机器参数、吞吐量或成本数字。

## 33. Scaling Strategy

采用：

~~~text
Scale Up first
→
Document-level parallelism
→
Multi-worker
→
Distributed only if justified
~~~

不要先做分布式系统。Document Processing 天然可以按 document_id 分片，Evaluation 天然可以按 item / model 分片。未来如果单机和多 Worker 仍不足，再增加分布式调度，但必须保留相同的 Artifact Contract、Failure Unit 和 Job Manifest。

## 34. Technology Decision Table

| Concern | Baseline | Status |
| --- | --- | --- |
| Corpus Inventory Storage | Parquet | Proposed Baseline |
| Canonical Items | JSONL | Proposed Baseline |
| Evaluation Results | Parquet | Proposed Baseline |
| Binary Assets | Filesystem / Object Storage abstraction | Baseline |
| Analytics | DuckDB | Recommended Candidate |
| Document Parser | Adapter-based, MinerU candidate | TBD |
| Evaluation Framework | Adapter-based | TBD |
| Workflow Engine | CLI / Batch first | Baseline |
| Database | Not required initially | Baseline |

本表不把 MinerU、OpenCompass 或 VLMEvalKit 锁死。Parser 和 Evaluation Framework 的最终选择必须经过对应的样本验证、Conformance Test、资源评估和后续技术评审。

## 35. Architecture Decision Records

未来使用 ADR 记录重要技术决策，例如：

~~~text
ADR-001 Batch-first architecture
ADR-002 Canonical storage strategy
ADR-003 Document Parser selection
ADR-004 Evaluation backend strategy
~~~

ADR 至少应说明背景、候选方案、决策、影响、依赖和变更原因。本次只定义 ADR 机制，不创建大量 ADR 文件，也不在本文件中替代正式决策。

## 36. Architecture Open Questions

以下问题全部保持 TBD，不在 System Architecture v0.1 中擅自解决：

1. Phase 1 实际服务器配置是什么？—— TBD
2. 70k PDF 总体积和目录结构是什么？—— TBD
3. MIGB_DATA_ROOT 使用本地盘、NAS 还是对象存储？—— TBD
4. MinerU 是否最终作为 Primary Parser？—— TBD
5. 是否需要第二 Parser 做 fallback / cross-check？—— TBD
6. Formula Registry 是否独立存在？—— TBD
7. Taxonomy / Prompt / Evaluator Registry 是否只使用文件，还是需要数据库？—— TBD
8. Human Review 是否需要专门 UI？—— TBD
9. Pipeline 规模到什么程度才引入 Workflow Engine？—— TBD
10. Phase 6 采用 Custom Runner、OpenCompass、VLMEvalKit 的具体组合？—— TBD
11. 是否需要独立 Object Storage？—— TBD
12. Canonical Item JSONL 是否需要同时发布 Parquet analytical mirror？—— TBD
13. Dataset Registry 是否需要签名 / checksum manifest？—— TBD
14. Benchmark Release Build 是否强制 clean Git workspace？—— TBD
15. Data backup / disaster recovery 策略是什么？—— TBD
16. document_id 的 Logical Document Resolution / Entity Resolution 算法最终采用什么策略？—— TBD
17. Canonical Artifact 的长期 Retention / Garbage Collection / Archive 策略是什么？—— TBD

Cache 清理和 Canonical Artifact Retention 是两回事。Cache 可以按可重建性清理，但 Canonical Artifact 的长期保留、归档和回收策略仍须单独决定。

## 37. End-to-End Conceptual Example

以下例子只说明 ID、版本和 Artifact 关系，不创建真实题目或真实数据：

~~~text
A.pdf
  ↓
CorpusFileInstance
  file_instance_id = FI-0001
  source_locator = external://candidate/A.pdf
  file_hash = sha256:...
  ↓
DOC-xxxx
  logical document_id
  document_family_id = DF-0001
  ↓
Inventory Record
  inventory_version = inventory-v0.1
  scan_status = passed
  ↓
Selected Source
  source_registry_version = source-v0.1
  selection_status = selected
  ↓
Document Parser Raw Output
  document_parser_id = parser-candidate
  document_parser_version = ...
  ↓
Normalized Document
  normalization_version = norm-v0.1
  ↓
EVD-001 + AST-001
  evidence_id / asset_id
  page_index / bbox / checksum
  ↓
MIGB-000123 candidate
  schema_version = 0.1
  item_revision = 1
  source_provenance = ...
  ↓
Verification Records
  source / ground_truth / schema / duplicate checks
  ↓
accepted revision 2
  same item_id = MIGB-000123
  item_revision = 2
  ↓
Pilot-v0.1 Snapshot
  dataset_version = Pilot-v0.1
  item_id = MIGB-000123
  item_revision = 2
  ↓
Model Evaluation
  run_id = RUN-0001
  evaluation_profile_version = ...
  ↓
EvaluationResult
  item_id / item_revision / dataset_version / score / status
  ↓
T2 / Domain / Overall Report
  report_version = ...
~~~

这个例子体现：

- file_instance_id 识别物理文件；
- document_id 识别逻辑 Source Document；
- document-family_id 关联文档版本和来源关系；
- item_id 在 Item Revision 间保持稳定；
- item_revision 记录内容和验证结论变化；
- Source Provenance 连接 Evidence、Document、Page 和 bbox；
- Dataset Snapshot 冻结具体 Item Revision；
- Evaluation Result 关联 Run、Dataset Version 和评分版本。

这里的 ID、内容和版本均为架构示例，不代表真实题目、真实 Source Document 或已经作出的实现选择。

## 38. 文档状态与当前交付边界

当前文档状态：

~~~text
Version: 0.1
Status: Reviewed - Baseline
Phase: Phase 0 - Benchmark Design
Current Task: System Architecture v0.1
~~~

本次交付完成 System Architecture v0.1 的设计说明及正式评审后的小范围修订，尚未实现：

- Corpus Inventory；
- Parser 或 Normalizer；
- Evidence / Asset Pipeline；
- Candidate Item 或 Dataset Generation；
- Ground Truth 生成；
- Evaluation Runner；
- Pilot Benchmark；
- Reporting Service。

本次评审结论为小修后通过，当前文档作为 Reviewed - Baseline 使用。但这不表示后续阶段的工程实现已经完成，也不表示已经开始 Pilot Design 或其他数据、模型和评测实现工作。

## 39. Repository Hygiene 与检查要求

大规模数据、Parser Artifact、Visual Asset、Raw Response 和运行缓存不进入 Git。仓库只保留适合版本管理的代码、文档、配置、Schema、测试和小型示例。

项目根目录的 .gitignore 应忽略 .DS_Store。现有 .DS_Store 即使存在，也不纳入本次提交。

文档修改完成后执行：

~~~text
git diff --check
~~~

并在提交前确认：

- 变更只涉及本次架构文档和 Repository Hygiene 所需文件；
- 没有提交 .DS_Store；
- 没有处理 70k PDF；
- 没有生成 Dataset；
- 没有调用 LLM；
- 没有实现 Evaluation Runner。

## 40. 变更记录

| 版本 | 日期 | 变更说明 |
| --- | --- | --- |
| v0.1 | 2026-09-11 | 将系统架构占位结构扩展为 Offline Batch-first、Modular Pipeline、Contract-driven Artifacts 基线，补充三 Plane、数据流、存储、组件边界、版本与运行机制、资源依赖、架构 Gate 和 Open Questions；保持 Draft - Pending Review |
| v0.1 | 2026-09-11 | 根据正式评审完成 Evaluation Result、Answer Parser Registry、Document Identity Resolution、Artifact Immutability / Lineage 和 Architecture Gate A 等小范围修订，Status 更新为 Reviewed - Baseline |
