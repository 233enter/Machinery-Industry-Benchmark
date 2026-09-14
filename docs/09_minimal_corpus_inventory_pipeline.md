# Minimal Corpus Inventory Pipeline Design v0.1

Project: Mechanical Industry General Benchmark
Document: Minimal Corpus Inventory Pipeline Design
Version: 0.1
Status: Draft - Awaiting Review
Phase: Phase 1 - Corpus Inventory
Current Task: Minimal Corpus Inventory Pipeline Design v0.1

## 1. 文档定位与设计边界

本文档定义 Phase 1 Minimal Corpus Inventory Pipeline 的目标、输入输出契约、记录粒度、
安全边界、资源策略、Dry-run 门禁和后续实现前的未决事项。

本文档只进行设计，不创建 Pipeline 代码，不创建数据目录，不安装依赖，也不运行任何
Inventory Job。所有字段、路径和参数均为设计层面的 Contract 或 Candidate，具体实现前仍须
经过评审，并由 Implementation ADR 冻结必要的技术选择。

本设计的首个 Inventory Scope 为：

~~~text
source_root_id = cmes_journal
source_root = /mnt/data_nfs/dataset/original/cmes/journal
PDF count = 60454
~~~

`60454` 是当前 `cmes_journal` Source Root 的 authoritative operational count，不是整个项目
Complete Candidate Source Corpus 的最终数量。Pipeline 必须支持未来增加其他 Source Root。

## 2. Pipeline Goal

Minimal Corpus Inventory Pipeline 的目标不是理解 PDF 内容，也不是直接构建 Benchmark 数据。
它的目标是建立从物理文件到可审计 Inventory Artifact 的最小基础链路，为 Phase 2 Source
Selection 和 Phase 3 Parser Validation 提供输入：

~~~text
Physical PDF File
        ↓
CorpusFileInstance
        ↓
Lightweight PDF Metadata
        ↓
Exact File Identity
        ↓
PDF Health / Text-layer Signals
        ↓
Inventory Parquet
        ↓
Duplicate / Statistics / Sample Inputs
~~~

Pipeline 需要回答：

- 当前配置的 Source Root 中有哪些 physical file instance；
- 每个文件的稳定运行身份、路径、大小和修改时间是什么；
- 文件是否能够进行轻量 PDF 打开和 metadata 读取；
- 文件是否存在 exact binary duplicate 关系；
- 文件是否具有粗粒度 text-layer signal；
- 哪些记录成功、部分成功或失败，以及失败发生在哪个 stage；
- 一次 Inventory Run 使用了什么配置、代码、输入快照和输出 Artifact。

本阶段不输出 Benchmark Quality Score，不进行 Domain Taxonomy 映射，也不理解 PDF 的完整
语义内容。

## 3. Source Corpus Safety

### 3.1 Read-only Logical Boundary

Candidate Source Corpus 必须被视为：

~~~text
Source Corpus = read-only logical boundary
~~~

当前 `/mnt/data_nfs` 的实际 filesystem mount mode 为 `rw`，但这不改变项目的 Operational
Source Safety Policy。Pipeline 只能以 read-only input 的方式访问 Candidate Source Corpus。

Pipeline 禁止：

- rename source；
- move source；
- delete source；
- 故意修改 source timestamps；
- 在 PDF 旁创建 sidecar files；
- 在 Source Directory 写入 cache；
- 在 Candidate Source Corpus 内进行 OCR；
- 在 Candidate Source Corpus 内执行 MinerU；
- 将 Parser output、page images、Evidence assets、temporary workspace、cache 或 Benchmark derived data 写回 Candidate Source Corpus。

所有输出必须进入独立的 `MIGB_DATA_ROOT`，不得与任何 configured source root 重叠。

### 3.2 Output Path Safety Check

实现时必须在 Job 启动前执行 Output Path Safety Check：

- 读取所有 configured source roots 和 output roots；
- 对路径进行规范化并检查路径包含关系；
- 如果 output path 位于任何 configured source root 内，立即拒绝启动；
- 对符号链接解析后的路径也必须执行同样的边界检查；
- 将 `source_safety_check` 结果写入 Job Manifest；
- 安全检查失败不得通过降级或静默方式继续运行。

本次只定义检查要求，不实现检查代码，也不创建输出目录。

### 3.3 Output Location Baseline

当前统一采用：

~~~text
MIGB_DATA_ROOT=/data/suzhe/migb
~~~

这是 xuelangyun Remote Linux Server 上 Canonical / persistent derived artifacts 的当前项目路径，
并统一作为当前项目的 `MIGB_DATA_ROOT`。
`/data` 仍然只是远程服务器的底层挂载点；`/data/suzhe/migb` 才是当前项目的 `MIGB_DATA_ROOT`。
该目录在本次设计任务中不创建。

该远程路径不要求在 Local Mac 上存在。Python Source Code 不得硬编码该绝对路径，必须通过
Environment Config / configuration injection 提供。`/data/suzhe/migb` 不加入 Git。

`/data-ssd` 当前 writable 为 `no`，本设计不依赖 `/data-ssd`，也不将 `/data-ssd/migb` 作为
当前可用 scratch 或 cache root。

## 4. Multiple Source Root Support

Pipeline 不得把单个 Source Root 硬编码到代码中。配置需要支持多个独立的 Source Root：

~~~yaml
source_roots:
  - source_root_id: cmes_journal
    path: /mnt/data_nfs/dataset/original/cmes/journal
    access_policy: read_only
    enabled: true
~~~

未来可以追加其他 Candidate Source Corpus：

~~~yaml
source_roots:
  - source_root_id: cmes_journal
    path: /mnt/data_nfs/dataset/original/cmes/journal
    access_policy: read_only
    enabled: true
  - source_root_id: xxx_books
    path: /some/other/candidate/source/root
    access_policy: read_only
    enabled: true
~~~

### 4.1 Environment Config Example

未来运行配置可以采用以下边界：

~~~yaml
source_roots:
  - source_root_id: cmes_journal
    path: /mnt/data_nfs/dataset/original/cmes/journal
    access_policy: read_only

migb_data_root: /data/suzhe/migb

inventory:
  worker_count: 4
~~~

该配置示例只定义配置注入边界，不在本次创建配置文件。Secret、SSH Password、Private Key
和 API Key 禁止进入 Repository、Config、Manifest 或 Log。

每个 Inventory Record 必须带有：

~~~text
source_root_id
~~~

新 Source Root 原则上通过新的配置和新的 Inventory Run 加入，不修改既有 Root 的历史记录。
不同 Root 的合并、比较和项目级统计仍列为 Open Question。

## 5. Path Handling and Traversal

### 5.1 Structured Traversal

正式实现优先使用：

- Python `pathlib` / `os.scandir`；
- in-memory path objects；
- structured records；
- Parquet / JSON 等结构化传输格式。

不得把 newline-delimited raw path list 作为文件身份或中间传输协议。此前 line-based counting
得到 `60460`，NUL-safe count 得到 `60454`，说明文件名中可能存在 newline 或其他特殊字符。

如果 shell 工具参与 traversal，必须使用 NUL-safe protocol；不得用 `find | wc -l` 的输出作为
authoritative file count 或稳定身份来源。

### 5.2 Path Representation

- `relative_path` 相对于对应的 configured source root 保存；
- 结构化记录必须保留文件名中的特殊字符；
- absolute source path 只作为运行时访问定位，不作为 stable ID；
- `file_name` 保存 basename；
- `parent_group` 保存当前一级 Source Directory / Publication Group 信息；
- 路径规范化不得改变 Candidate Source Corpus 中 Source PDF 的实际内容或文件名。

## 6. File Instance Identity

### 6.1 Operational Entity

引入以下 Operational Entity：

~~~text
CorpusFileInstance
~~~

它表示某个 configured Source Root 下的一个 physical file instance，不等同于一个语义文档，
也不等同于一个 exact binary identity。

### 6.2 Core Inventory Fields

`files.parquet` 至少需要支持以下核心字段：

~~~text
inventory_schema_version

file_instance_id

source_root_id
relative_path
file_name
parent_group

extension

size_bytes
mtime_ns

sha256
hash_status

inventory_status

collected_at
inventory_run_id
~~~

轻量 PDF、错误和一致性相关字段见后续章节。字段是否最终按上述名称冻结，需要在实现前通过
Schema Review 确认。

### 6.3 Stable Identity Rules

建议 `file_instance_id` 基于以下输入生成 deterministic identity：

~~~text
source_root_id
+
relative_path
~~~

UUIDv5 或稳定 hash 均可作为候选实现。具体算法在实现前冻结。无论采用何种算法，都必须满足：

~~~text
file_instance_id != document_id
file_instance_id != sha256
~~~

`sha256` 只代表 exact binary file identity；`file_instance_id` 表示 Source Root 中的文件实例。

文件 rename / relocate 是否应产生新的 File Instance，必须在实现规范中明确，当前不在本文档
中擅自给出最终规则。

## 7. Lightweight PDF Metadata

Phase 1 的每个 PDF 最多进行轻量读取，不进行全文理解。建议支持以下字段：

~~~text
pdf_open_status
pdf_error_category

page_count

is_encrypted

pdf_version

metadata_title
metadata_author
metadata_subject
metadata_keywords
metadata_creator
metadata_producer
metadata_creation_date
metadata_modification_date
~~~

PDF metadata 允许为空、缺失或异常。metadata 缺失不得直接把 PDF 判为 invalid。

轻量读取的最终 library 仍未冻结，候选包括 PyMuPDF 和 pypdf，见第 15 节。当前不运行
PDF parser，也不执行全文 page count 扫描。

## 8. PDF Health Status and Failure Boundary

### 8.1 Controlled PDF Status

建议 `pdf_status` 使用以下受控值：

~~~text
valid
encrypted
open_error
corrupted_or_invalid
unknown
~~~

`pdf_open_status`、`pdf_status` 和 `inventory_status` 的最终关系在 Schema Review 中确认。
一个 metadata 缺失或单字段解析异常不应无依据地将整个 PDF 判为 invalid。

### 8.2 Independent Failure Unit

每个 PDF 都是独立 Failure Unit。单个异常 PDF 不得导致整个 Job 失败。

以下错误不得 silent skip：

- hash failure；
- open failure；
- metadata parse failure；
- text sample failure；
- source changed during run；
- 其他导致记录不完整的 stage failure。

错误应进入 `errors.parquet` 或等价 Error Manifest，至少包含错误 stage、category、message 和
对应 File Instance。错误记录不能包含秘密信息。

## 9. SHA-256 Strategy

Phase 1 Full Run 需要对纳入 Scope 的完整文件执行 SHA-256，用于：

- exact binary duplicate detection；
- integrity reference；
- cache identity；
- 后续 lineage support。

核心字段为：

~~~text
sha256
hash_status
~~~

Hash Failure 必须记录，不得把失败文件静默排除。`sha256` 只表示 exact binary file identity，
不得使用：

~~~text
document_id = sha256
~~~

本设计定义 Full Run 的要求，但本次不执行 60,454 个文件的 SHA-256。

## 10. Exact Duplicate Detection

完成 SHA-256 后建立：

~~~text
exact_duplicate_group
~~~

建议生成独立 Artifact：

~~~text
duplicate_groups.parquet
~~~

至少需要表达：

~~~text
duplicate_group_id
sha256
file_count
file_instance_ids
representative_file_instance_id
~~~

`file_instance_ids` 可以采用适合 Parquet 的 normalized representation，具体 representation
仍需在实现前确定。

Duplicate Detection 只记录关系：

- 不删除重复文件；
- 不移动重复文件；
- 不自动挑选一个文件覆盖其他文件；
- 不把 duplicate group 当作语义 document family 的最终结论。

## 11. Lightweight Text-layer Detection

Phase 1 不 OCR。允许使用少量页面进行 text layer heuristic，目的只是粗分：

~~~text
text_present
text_absent
mixed_or_uncertain
check_failed
~~~

建议抽取：

~~~text
first page
middle page
last page
~~~

最多 3 页。对于少页 PDF，重复的 sampled page 必须自动去重。建议记录：

~~~text
sampled_page_count
sampled_text_char_count
text_layer_status
~~~

具体 character threshold 必须保持 config-driven，并在实现前冻结或明确版本化。该 heuristic
不能声称为最终的：

~~~text
scanned_pdf
~~~

如果 PDF 加密、打开失败或抽样检查失败，应记录 `check_failed` 或相应 failure，而不是猜测
其 text layer 状态。本次不执行 OCR，也不分析全文。

## 12. Filename Metadata

当前文件名多数类似：

~~~text
【YYYY-MM】文章标题.pdf
~~~

可以做非常保守的 Lightweight Filename Parsing，候选字段为：

~~~text
filename_year
filename_issue
filename_title
filename_parse_status
~~~

只有正则明确匹配时才填入 `filename_year`、`filename_issue` 和 `filename_title`；不匹配时：

~~~text
filename_parse_status = unmatched
~~~

不得猜测，也不得让 Filename Metadata 覆盖 PDF internal metadata。Filename Metadata 不能替代
PDF internal metadata。本次不实现 Filename Parser。

## 13. Source Group

当前一级目录对应期刊或专业来源组。Inventory 可以记录：

~~~text
parent_group
~~~

例如：

~~~text
wusunjiance
jixiegongchengxuebao
jixieqiangdu
~~~

`parent_group` 的语义是 Source Directory / Publication Group：

~~~text
parent_group != Benchmark Domain
~~~

Phase 1 不自动将 Source Group 映射到 D01–D12，也不在 Inventory 中生成 Domain Taxonomy 结论。

## 14. Inventory Record Schema

### 14.1 `files.parquet` Granularity

原则：

~~~text
1 physical file instance
=
1 row
~~~

当前首个 `cmes_journal` Scope 预期约 `60,454 rows`。这是当前 Source Root 的规模，不是整个
项目最终 Candidate Source Corpus 的规模。

V1 不需要为了文件数量过早设计复杂 Parquet Partition，可以采用单个 Parquet 或少量文件。
不得产生：

~~~text
one parquet per PDF
~~~

### 14.2 Recommended Record Fields

以下为推荐字段集合，具体类型、nullability 和 controlled vocabulary 通过 Schema Review 冻结：

| Group | Fields | Purpose |
| --- | --- | --- |
| Identity | `inventory_schema_version`, `file_instance_id`, `source_root_id`, `relative_path`, `file_name`, `parent_group`, `extension` | 表示文件实例及其 Source Root 位置 |
| File state | `size_bytes`, `mtime_ns`, `source_changed_during_run` | 表示输入状态和运行期间一致性 |
| Hash | `sha256`, `hash_status` | exact binary identity、完整性和后续 lineage |
| PDF health | `pdf_open_status`, `pdf_error_category`, `pdf_status`, `is_encrypted`, `pdf_version`, `page_count` | 轻量 PDF 状态和 metadata |
| PDF internal metadata | `metadata_title`, `metadata_author`, `metadata_subject`, `metadata_keywords`, `metadata_creator`, `metadata_producer`, `metadata_creation_date`, `metadata_modification_date` | 保留 PDF 内部 metadata，允许为空 |
| Text signal | `sampled_page_count`, `sampled_text_char_count`, `text_layer_status` | 粗粒度 text-layer heuristic |
| Filename signal | `filename_year`, `filename_issue`, `filename_title`, `filename_parse_status` | 保守的 Filename Lightweight Metadata |
| Run metadata | `inventory_status`, `collected_at`, `inventory_run_id` | 表示运行状态和记录来源 |

Schema 必须允许部分成功记录存在。例如 hash 成功但 PDF metadata 失败时，仍应保留 File Instance
和 hash 结果，并在 Error Manifest 中记录失败 stage。

## 15. Tooling Boundary

推荐的最小 Python 技术栈候选为：

~~~text
Python 3.10+
PyArrow
PDF lightweight library
~~~

PDF lightweight library 可以评估：

~~~text
PyMuPDF
pypdf
~~~

当前不因为个人偏好锁死具体 library。选择时至少比较：

- page_count reliability；
- encryption handling；
- metadata 读取能力；
- lightweight text extraction 能力；
- speed；
- dependency complexity。

最终选择可在 Implementation ADR 中决定。不要使用 MinerU 完成 Inventory，不把 OCR 或重型
Document Processing 工具引入 Minimal Inventory 的必要路径。

## 16. Inventory Output Artifact Layout

Canonical Inventory Storage 候选为 Parquet。初始输出布局建议为：

~~~text
MIGB_DATA_ROOT/
  inventory/
    runs/
      <inventory_run_id>/
        files.parquet
        duplicate_groups.parquet
        errors.parquet
        sample_manifest.json
        manifest.json
        statistics.json
~~~

当前 D1 Artifact Layout 为：

~~~text
/data/suzhe/migb/
  inventory/
    runs/
      <inventory_run_id>/
        files.parquet
        duplicate_groups.parquet
        errors.parquet
        sample_manifest.json
        manifest.json
        statistics.json
~~~

`/data/suzhe/migb` 是远程 Linux Server 路径；上述目录不要求存在于 Local Mac。输出布局必须满足：

- 文件实例记录、重复关系、错误和统计可以独立读取；
- 每个 Artifact 能关联到 `inventory_run_id`；
- Manifest 能指向本次 Run 的全部输出；
- 输出与 Candidate Source Corpus 物理隔离；
- 不在 Source Root 旁创建中间文件。

## 17. Error Manifest

任何 PDF 的以下失败都不能 silent skip：

- hash failure；
- open failure；
- metadata parse failure；
- text sample failure；
- source consistency failure。

至少记录：

~~~text
inventory_run_id
file_instance_id
source_root_id
relative_path
stage
error_category
error_message
timestamp
~~~

错误消息应便于排查，但不得包含密码、API key、Token 或其他秘密信息。单个 Error Record 不应
使整个 Inventory Job 无法产出其他文件的有效记录。

## 18. Job Manifest

每个 Inventory Run 必须生成 Job Manifest，至少包含：

~~~text
inventory_run_id
inventory_schema_version

source_roots

config_snapshot

git_commit
dirty

python_version
tool_versions

started_at
completed_at

discovered_count
processed_count
success_count
partial_count
failure_count

output_artifacts

source_safety_check
~~~

Manifest 必须能够说明一次 Run 使用了哪些 Source Root、配置、代码版本、工具版本、输入输出
统计和安全检查结果。`dirty` 用于说明运行时 Git working tree 是否存在未提交变更。

## 19. NFS I/O Strategy

当前 Source 位于 NFS4：

~~~text
mount: /mnt/data_nfs
actual mount mode: rw
~~~

虽然物理 mount 为 `rw`，Operational Source Safety 仍为 read-only。Inventory 的最大运行风险
是 shared NFS I/O，不是 GPU。

Pipeline 需要采用：

~~~text
bounded concurrency
~~~

不得默认使用：

~~~text
48 CPU → 48 workers
~~~

Initial concurrency baseline 建议从：

~~~text
4 workers
~~~

作为 D1 / dry-run 起点。根据实际以下指标再决定是否提高至 `8 workers`：

- files/s；
- MiB/s；
- NFS latency；
- error rate；
- server load。

没有测量依据时，不继续扩大并发。Hashing 和 PDF lightweight inspection 可以设计为同一
File Task，尽量避免重复打开文件和多轮全量扫描。

## 20. GPU Policy

Phase 1 Minimal Inventory：

~~~text
GPU required = false
~~~

当前环境的 4 × RTX 3090 保留给其他 workload，不在 Minimal Corpus Inventory 中使用 GPU。
本次不启动 GPU workload。

## 21. Memory Policy

当前服务器资源记录为：

~~~text
94 GiB RAM
8 GiB swap / 8 GiB used at collection time
~~~

Pipeline 不需要把约 60k Inventory Records 全部长期保存在内存中，采用：

~~~text
stream / bounded batches
~~~

设计。由于 Swap 在采集时已基本完全使用，应避免：

- 大量 Process fork；
- 大对象复制；
- 无界队列；
- 无界的 in-memory record accumulation。

## 22. Dry-run Strategy

正式 Full Inventory 前分三级验证。所有 Dry-run 只在设计评审通过、实现完成后执行；本次不运行
任何 Dry-run。

### Stage D1 — Smoke Test

目标：

~~~text
20 PDFs
~~~

建议每个当前 top-level group 选 1 个 PDF。当前已观察到 20 个一级目录，因此目标为约 20 个
输入记录。

D1 至少验证：

- source safety passed；
- 20 input records accounted；
- schema valid；
- manifest valid；
- failures captured；
- output readable。

### Stage D2 — Representative Dry-run

目标：

~~~text
200 PDFs
~~~

建议约每个 top-level group 10 个，并保持 deterministic sampling。观察：

- throughput；
- NFS behavior；
- PDF error patterns；
- metadata quality；
- text layer signals；
- memory usage。

### Stage D3 — Scale Test

目标：

~~~text
1000 PDFs
~~~

用于决定 Full Run 的：

- worker_count；
- batch_size；
- retry policy；
- estimated storage。

所有 sample 必须记录：

~~~text
sampling_seed
sampling_method
sample_manifest
~~~

采样结果必须能够由配置、Seed 和输入快照重新生成或审计。

## 23. Full Inventory Gate

只有 D1、D2、D3 都满足以下原则，才允许进入 Full Inventory：

~~~text
all input paths accounted for
no source writes
no silent failures
schema validation passes
manifest complete
resume/restart works
NFS load acceptable
~~~

Full Inventory Gate 只验收 Inventory 的正确性、完整性、安全性和可重启性，不使用模型准确率
等与 Inventory 无关的指标。

## 24. Restartability

Full Run 必须支持：

~~~text
resume
~~~

如果处理到：

~~~text
37,000 / 60,454
~~~

发生失败，不能重新 hash 前 37,000 个文件。恢复识别至少需要基于：

~~~text
file_instance_id
+
input file state
+
inventory config/version
~~~

识别已完成记录。具体 checkpoint implementation、覆盖策略和冲突处理在实现阶段设计。

## 25. File Change Detection

由于 Source NFS 实际 mount 为 `rw`，Full Run 前后建议记录 Corpus Snapshot Signals：

~~~text
file_count
total_size
root metadata
~~~

单个文件至少记录：

~~~text
size_bytes
mtime_ns
sha256
~~~

如果文件在运行期间发生变化，应标记：

~~~text
source_changed_during_run
~~~

不得静默认为 Hash 和 Metadata 属于同一输入版本。具体双 stat / consistency strategy 在实现
阶段设计。

## 26. Inventory Statistics

Full Run 至少输出：

~~~text
total_files
successful_files
partial_files
failed_files

total_bytes

page_count distribution

file_size distribution

encrypted_count

pdf_open_error_count

text_present_count
text_absent_count
mixed_or_uncertain_count

exact_duplicate_file_count
exact_duplicate_group_count

top-level source-group counts

filename_parse_success_rate
~~~

本阶段不输出 Benchmark Quality Score，也不把 Inventory Statistics 解释为 Benchmark 能力分数。

## 27. Corpus Scope and Source Root Registry

当前正式记录的首个 Inventory Scope 为：

~~~text
source_root_id = cmes_journal
source_root = /mnt/data_nfs/dataset/original/cmes/journal
PDF count = 60454
~~~

该 `60454` 是当前 Root 的 authoritative operational count。项目级 Complete Candidate Source
Corpus 是否还包含其他 Source Root，继续保持为 TBD。

Pipeline 必须支持未来把新 Root 加入新的 Inventory Run，而不重写既有 `cmes_journal` 历史
Artifact。新 Root 如何 merge / compare 与项目级统计如何聚合，列入 Open Questions。

## 28. MIGB_DATA_ROOT Decision Boundary

当前 xuelangyun Remote Linux Server 项目工作目录为：

~~~text
MIGB_DATA_ROOT=/data/suzhe/migb
~~~

路径约束：

- `/data` available 约 `2.7 TiB`；
- `/data` writable 为 `yes`；
- `/data-ssd` writable 为 `no`；
- 当前不设计依赖 `/data-ssd` 的路径；
- `/data/suzhe/migb` 是当前项目的 `MIGB_DATA_ROOT`，仍需遵守配置注入和 Output Path Safety Check；
- 本次不创建 `/data/suzhe/migb`。

如果后续管理员赋予 `/data-ssd` 写权限，可以通过配置增加独立 scratch / cache root，
不要求重构 Canonical Paths。Candidate Source Corpus 所在 `/mnt/data_nfs` 不用于保存派生
Artifact、缓存或临时工作区。

## 29. Phase 1 Intake Closeout Dependency

当前 `cmes_journal` Source Root 的 Intake Closeout 已完成并记录在：

~~~text
docs/08_phase1_environment_and_corpus_intake.md
~~~

Closeout 已确认：

~~~text
verified PDF count: 60454
top-level directories: 20
non-PDF: 0
symlinks: 0
zero-byte PDFs: 0
unreadable PDFs: 0
NFS4
rw mounted
/data writable: yes
/data-ssd writable: no
~~~

此前的 `60460` 来自 line-based counting，不作为正式 count。NUL-safe file count `60454` 为当前
Root 的 authoritative operational count。该 Closeout 不解决完整项目级 Candidate Source Corpus
scope 问题。

## 30. Implementation Boundary

本次只完成 Minimal Corpus Inventory Pipeline Design，禁止：

- 创建 `/data/suzhe/migb`；
- 创建 `/data-ssd/migb`；
- 安装依赖；
- 编写 Pipeline Python；
- 对 60k PDFs 执行全量 SHA-256；
- 读取全部 page counts；
- 执行 Full Inventory；
- 执行 PDF validity parse；
- 执行 text layer detection；
- 执行 MinerU；
- 执行 OCR；
- LLM 调用；
- GPU workload。

D1 / D2 / D3 以及 Full Inventory 均必须等待设计评审和后续实施授权。本次不运行 Pipeline。

## 31. Open Questions

以下问题全部保持 `TBD`，除非后续 Dry-run 提供实证依据：

1. PDF lightweight library 最终选择 PyMuPDF 还是 pypdf？
2. `file_instance_id` 最终生成算法？
3. text-layer heuristic 的 character threshold？
4. PDF text sampling 是否固定 first / middle / last？
5. Full Run `worker_count` 最终是多少？
6. retry policy？
7. checkpoint / resume 具体格式？
8. exact duplicate group representation？
9. Parquet 是否需要分片？
10. Inventory Run 是否需要 checksum manifest？
11. 新 Candidate Source Root 如何 merge / compare？
12. `/data-ssd` 未来是否获得写权限？
13. 完整约 70k Candidate Source Corpus 是否还有其他 Source Root？
14. 是否存在 scheduler / quota？
15. Inventory Artifact retention policy？

## 32. Current Progress

本设计文档完成后，项目状态为：

~~~text
Current Phase: Phase 1 - Corpus Inventory
Current Milestone: Corpus Inventory v0.1
Current Task: Minimal Corpus Inventory Pipeline Design v0.1
Next Task: Review Minimal Corpus Inventory Pipeline Design, then implement D1 Smoke Test only.
~~~

设计文档评审通过前，不进入 Pipeline Implementation，也不执行 D1 Smoke Test。
