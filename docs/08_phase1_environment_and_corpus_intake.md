# Phase 1 Environment & Candidate Source Corpus Intake

```text
Version: 0.1
Status: Draft - Awaiting Environment Data
Phase: Phase 1 - Corpus Inventory
Current Task: Phase 1 Environment & Corpus Intake
```

## 1. Purpose and Scope

本文档是 Phase 1 的环境与 Candidate Source Corpus Intake / Readiness Record。
当前只记录后续 Corpus Inventory 工作所需的运行环境、存储条件和候选语料基本信息，
不实现 Corpus Inventory Pipeline，也不预先确定具体的 Benchmark 设计内容。

项目当前拥有的约 70,000 本机械工业相关 PDF 仍然只定义为 **Candidate Source Corpus**，
不直接等同于 Benchmark 数据或 Benchmark Source Corpus。正式统计结果需要在实际 Intake
完成后填写。

本文档中的未知项统一标记为 `TBD`。本次不自动探测环境、不扫描或处理 Source PDF，
也不根据已有估计猜测任何统计值。

## 2. Runtime Environment

以下信息待在实际运行环境中采集。未采集项保持为 `TBD`。

| Item | Value | Notes |
| --- | --- | --- |
| hostname / environment name | `TBD` | 待确认运行主机或环境名称 |
| OS | `TBD` | 待确认操作系统及版本 |
| kernel | `TBD` | 待确认 Kernel 版本 |
| architecture | `TBD` | 待确认 CPU / 系统架构 |
| CPU model | `TBD` | 待确认 CPU 型号 |
| CPU cores / threads | `TBD` | 待确认物理核心数和逻辑线程数 |
| RAM total | `TBD` | 待确认总内存 |
| swap | `TBD` | 待确认 Swap 配置和可用量 |
| GPU model | `TBD` | 如无 GPU 也需要在采集后明确记录 |
| GPU count | `TBD` | 待确认 GPU 数量 |
| GPU memory | `TBD` | 待确认每张 GPU 的显存 |
| CUDA / driver information if available | `TBD` | 待确认 CUDA 和 GPU Driver 信息 |
| disk devices | `TBD` | 待确认磁盘设备及挂载关系 |
| filesystem type | `TBD` | 待确认相关文件系统类型 |
| total capacity | `TBD` | 待确认相关磁盘总容量 |
| free capacity | `TBD` | 待确认相关磁盘剩余容量 |
| Docker availability | `TBD` | 待确认是否允许使用 Docker |
| Docker version | `TBD` | Docker 不可用时也应记录确认结果 |
| Python version | `TBD` | 待确认 Python 版本 |
| network / internet accessibility | `TBD` | 待确认网络和互联网访问条件 |
| API accessibility | `TBD` | 待确认所需 API 的访问条件和限制 |

### Runtime Environment Collection Boundary

- 本记录不执行环境探测命令，也不安装依赖或修改运行环境。
- GPU、CUDA、Driver、Docker、网络和 API 等信息需要由环境负责人或后续受控采集过程补充。
- 如果同一项目存在多个运行环境，应分别记录环境名称及对应资源，不将不同环境的资源合并为单一结论。

## 3. Candidate Source Corpus Intake

本节只记录 Candidate Source Corpus 的 Intake 信息和统计摘要，不记录 70,000 个文件的完整列表。
在实际 Intake 完成前，所有统计值均为 `TBD`。

| Field | Value | Notes |
| --- | --- | --- |
| `corpus_root` | `TBD` | Candidate Source Corpus 的实际根目录待确认 |
| `access_mode` | `TBD` | 例如本地目录、网络挂载或其他受控访问方式，待确认 |
| `total_size` | `TBD` | Candidate Source Corpus 总大小待统计 |
| `total_file_count` | `TBD` | 根目录下文件总数待统计 |
| `pdf_file_count` | `TBD` | 实际 PDF 文件数量待统计 |
| `directory_structure_summary` | `TBD` | 目录层级和组织方式摘要待记录 |
| `sample_filenames` | `TBD` | 仅记录少量代表性样例文件名，不记录完整列表 |
| `other_file_types` | `TBD` | 是否混有非 PDF 文件及其类型待确认 |
| `permissions / accessibility` | `TBD` | 读取权限、访问限制和失败路径待确认 |

### Corpus Identity and Interpretation

- 当前语料的工作名称为 **Candidate Source Corpus**。
- `pdf_file_count`、`total_size` 等字段必须来自后续实际 Intake 统计，不使用“约 70,000”这一项目背景估计替代。
- 只有在后续完成 Inventory、去重、分类、质量评估和 Source Selection 后，Candidate Source Corpus 中的部分资料才可能进入 **Benchmark Source Corpus**。
- V1 不要求使用完全部 Candidate Source Corpus。

## 4. Corpus Safety

Intake 阶段遵循以下安全边界：

- 不修改任何 Source PDF。
- 不 rename Source PDF。
- 不 move Source PDF。
- 不对 Source PDF 执行 OCR。
- 不执行 MinerU。
- 不将处理结果写回 Source Corpus。
- 后续针对 Source Corpus 的 Pipeline 默认采用 read-only 访问。
- 本文档只保存 Intake / Readiness Record，不在 Source Corpus 内创建中间文件、索引或派生数据。

如果后续工作需要生成清单、缓存或其他派生结果，应使用与 Source Corpus 分离的受控工作区，
并在实施前完成相应的设计和审批。

## 5. Storage Readiness

以下信息用于判断后续工作是否具备独立、可控的存储条件。当前不正式决定 `MIGB_DATA_ROOT`。

| Field | Value | Notes |
| --- | --- | --- |
| candidate `MIGB_DATA_ROOT` | `TBD` | 仅作为候选位置记录，尚未正式确定 |
| available disk space | `TBD` | 待确认可用于项目工作区的剩余空间 |
| same disk / different disk from source corpus | `TBD` | 待确认与 Source Corpus 的磁盘关系 |
| filesystem | `TBD` | 待确认候选工作区的文件系统 |
| temporary workspace availability | `TBD` | 待确认是否有足够的临时工作区及其生命周期 |

### Storage Decision Boundary

- 在环境信息不足时，不正式决定 `MIGB_DATA_ROOT`。
- 如果磁盘空间明显不足，只记录风险和影响，不自行移动或删除任何数据。
- Candidate Source Corpus 与后续工作区的关系应在信息充分后再确定，并保持 Source Corpus 的 read-only 边界。

## 6. Phase 1 Readiness Questions

以下问题均为当前未决事项，状态统一为 `TBD`，不在本文档中擅自给出答案。

| # | Readiness Question | Status |
| ---: | --- | --- |
| 1 | 70k PDF 实际根目录是什么？ | `TBD` |
| 2 | Source Corpus 总大小？ | `TBD` |
| 3 | 实际 PDF 数量？ | `TBD` |
| 4 | 是否混有其他文件类型？ | `TBD` |
| 5 | 是否存在明显按领域/书籍分类的目录？ | `TBD` |
| 6 | Source Corpus 是否可视为 read-only？ | `TBD` |
| 7 | 是否存在软链接 / 网络挂载？ | `TBD` |
| 8 | 可用于 `MIGB_DATA_ROOT` 的磁盘还有多少空间？ | `TBD` |
| 9 | 是否允许 Docker？ | `TBD` |
| 10 | 是否允许联网？ | `TBD` |
| 11 | 是否有 GPU？ | `TBD` |
| 12 | 是否有资源限制或作业调度系统？ | `TBD` |
| 13 | 是否与 CPT/SFT Corpus 位于同一存储区域？ | `TBD` |
| 14 | 是否已有已知重复目录或备份目录？ | `TBD` |
| 15 | 是否存在版权 / 权限限制信息？ | `TBD` |

## 7. Do Not Implement Yet

本次 Intake / Readiness Record 不实现以下内容：

- 全量 SHA-256
- PDF page count 扫描
- PDF parser
- MinerU
- OCR
- text layer detection
- duplicate detection
- representative sampling
- Parquet Inventory
- 数据库
- LLM 调用

以上内容属于后续 **Minimal Corpus Inventory Pipeline** 或更后续阶段。本次不创建代码、数据库、
数据集或 Pipeline，也不执行任何全量或抽样 PDF 处理。

## 8. Current Progress Boundary

在 Runtime Environment、Candidate Source Corpus 和 Storage Readiness 信息尚未完成采集与确认前，
项目状态保持为：

```text
Current Phase: Phase 1 - Corpus Inventory
Current Milestone: Corpus Inventory v0.1
Current Task: Phase 1 Environment & Corpus Intake
```

当前不将任务推进到 `Inventory Pipeline Implementation`。只有在 Intake / Readiness 信息充分、
安全边界明确且后续设计条件满足后，才评估是否进入 Minimal Corpus Inventory Pipeline 的设计与实现。

## 9. Readiness Summary

| Area | Current Status |
| --- | --- |
| Runtime Environment completeness | `TBD` / Awaiting Environment Data |
| Candidate Source Corpus completeness | `TBD` / Awaiting Corpus Intake Data |
| Storage Readiness | `TBD` / Awaiting Storage Data |
| Minimal Corpus Inventory Pipeline design readiness | Not yet established |
| Source Corpus safety posture | Read-only by default; no source modification performed |
