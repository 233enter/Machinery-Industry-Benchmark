# Phase 1 Environment & Candidate Source Corpus Intake

```text
Version: 0.1
Status: Draft - Awaiting Environment Data
Phase: Phase 1 - Corpus Inventory
Current Task: Phase 1 Environment & Corpus Intake
```

## 1. Purpose and Scope

本文档是 Phase 1 的环境与 Candidate Source Corpus Intake / Readiness Record。
当前只回填已采集的运行环境和 Candidate Source Corpus 观察信息，并记录 Intake Closeout
所需的核验项；不实现 Corpus Inventory Pipeline，也不预先确定具体的 Benchmark 设计内容。

项目当前拥有的约 70,000 本机械工业相关 PDF 仍然只定义为 **Candidate Source Corpus**，
不直接等同于 Benchmark 数据或 Benchmark Source Corpus。正式统计结果需要在实际 Intake
完成后填写。

本文档中的未知项统一标记为 `TBD`。本次只使用已提供的实测数据，不执行额外环境探测，
不扫描或处理 Source PDF，也不根据已有估计猜测任何统计值。

## 2. Runtime Environment

以下信息根据本次实际环境采集结果回填。仍未采集项保持为 `TBD`。

| Item | Value | Notes |
| --- | --- | --- |
| hostname / environment name | `xuelangyun` | 实测环境名称 |
| OS | `Ubuntu 22.04.5 LTS` | 实测操作系统 |
| kernel | `5.15.0-185-generic` | 实测 Kernel 版本 |
| architecture | `x86_64` | 实测系统架构 |
| CPU model | `Intel Xeon E5-2678 v3 @ 2.50GHz` | 实测 CPU 型号 |
| CPU cores / threads | `2 sockets; 12 physical cores / socket; 2 threads / core; 24 physical cores; 48 logical CPUs` | 实测核心和线程配置 |
| RAM total | `94 GiB` | 实测总内存 |
| RAM available at collection time | `~54 GiB` | 采集时可用内存，仅为采集时状态 |
| swap | `8 GiB total; ~8 GiB used at collection time` | Swap 已基本完全使用，记录为资源风险；暂不判定为 Phase 1 Blocking Issue |
| GPU model | `NVIDIA GeForce RTX 3090` | `4` 张，每张 `24 GiB` VRAM |
| GPU count | `4` | 采集时 GPU 0–2 被 Python / vLLM workload 占用，GPU 3 基本空闲 |
| GPU memory | `24 GiB VRAM each` | 实测显存配置 |
| CUDA / driver information if available | `NVIDIA Driver 595.58.03; CUDA reported by nvidia-smi: 13.2` | 采集时报告值 |
| disk devices | `/`, `/data-ssd`, `/data`, `/mnt/data_nfs` | 具体物理设备映射仍待确认 |
| filesystem type | `/`: ext4; `/data-ssd`: ext4; `/data`: ext4; `/mnt/data_nfs`: nfs4 | 按挂载点记录 |
| total capacity | `TBD` | 本次数据只提供各挂载点可用容量，未提供总容量 |
| free capacity | `/`: ~697 GiB; `/data-ssd`: ~870 GiB; `/data`: ~2.7 TiB; `/mnt/data_nfs`: ~437 GiB | 采集时可用容量 |
| Docker availability | `yes` | Docker Engine 可用，NVIDIA runtime 可用 |
| Docker version | `Docker Engine 28.3.1` | 实测版本 |
| Python version | `Python 3.10.12 (/usr/bin/python3)` | 实测版本和路径 |
| network / internet accessibility | `TBD` | 待确认网络和互联网访问条件 |
| API accessibility | `TBD` | 待确认所需 API 的访问条件和限制 |

### Runtime Environment Collection Boundary

- 本次回填不执行额外环境探测命令，也不安装依赖或修改运行环境。
- Phase 1 Light Corpus Inventory 不要求使用 GPU；GPU 占用情况只作为本次采集时的资源快照记录。
- Swap 当前已经基本完全使用，需要在后续大规模并发任务设计中作为资源风险记录，但目前不判定为 Phase 1 Blocking Issue。
- 网络和 API 信息需要由环境负责人或后续受控采集过程补充。
- 如果同一项目存在多个运行环境，应分别记录环境名称及对应资源，不将不同环境的资源合并为单一结论。

## 3. Candidate Source Corpus Intake

本节只记录 Candidate Source Corpus 的 Intake 信息和统计摘要，不记录 70,000 个文件的完整列表。
以下为当前实测或初步观察结果；尚未核验的统计值继续标记为 `TBD`。

| Field | Value | Notes |
| --- | --- | --- |
| `corpus_root` | `/mnt/data_nfs/dataset/original/cmes/journal/` | 当前实测 root；是否为完整 Candidate Source Corpus 仍待确认 |
| `access_mode` | `NFS4 mounted directory` | 当前通过 NFS4 挂载目录访问 |
| `total_size` | `≈225 GiB` | 当前 root 的初步统计值 |
| `total_file_count` | `TBD` | 观察到 `60460` 和 `60454` 两个计数，尚未完成 NUL-safe reconciliation |
| `pdf_file_count` | `TBD` | `pdf_file_count_status = needs_reconciliation`; `observed_counts = [60460, 60454]` |
| `directory_structure_summary` | `Observed: 一级目录按期刊 / 专业来源组织` | 仅表示 Source Directory / Publication Group，不直接映射 D01–D12 |
| `sample_filenames` | `【YYYY-MM】文章标题.pdf`；例如 `【2010-06】基于声发射的滚动轴承故障诊断方法.pdf` | 仅记录少量样例，不记录完整列表 |
| `other_file_types` | `TBD` | 需通过后续 non-PDF file count 确认 |
| `permissions / accessibility` | `TBD` | NFS4 挂载已观察；read-only、挂载权限和访问失败情况仍待确认 |

### Corpus Identity and Interpretation

- 当前语料的工作名称为 **Candidate Source Corpus**。
- `pdf_file_count`、`total_size` 等字段必须来自后续实际 Intake 统计，不使用“约 70,000”这一项目背景估计替代。
- 只有在后续完成 Inventory、去重、分类、质量评估和 Source Selection 后，Candidate Source Corpus 中的部分资料才可能进入 **Benchmark Source Corpus**。
- V1 不要求使用完全部 Candidate Source Corpus。

### Observed Top-level Directory Samples

以下为当前观察到的少量一级目录样例，仅用于描述 Source Directory / Publication Group，
不代表完整目录列表，也不作为后续 Domain Taxonomy 的直接划分依据：

```text
wusunjiance
zhizaojishuyujichuang
zhongguojixiegongcheng
lihuajianyan-huaxuefence
jixiegongchengxuebao2
jixieqiangdu
hanjiexuebao
lihuajianyan-wulifence
zhizaoyezidonghua
zhongguohanjie
jixiegongchengcailiao
jixiechuandong
hanjie
jixiegongchengxuebao
zhongguozhuzaozhuangbeiyujishu
duanyajishu
suxinggongchengxuebao
yeyayuqidong
jinshurechuli
zhuzao
```

### PDF Size Observations

当前 PDF 大小统计为初步观察值：

| Metric | Observed Value | Interpretation |
| --- | --- | --- |
| average PDF size | `≈3.81 MiB` | 初步统计值 |
| maximum PDF size | `≈311.97 MiB` | 初步统计值 |
| minimum displayed size | `0.00 MiB` | 不等于已确认存在 zero-byte PDF，需单独执行 zero-byte check |

### Filename Pattern Observation

当前文件名通常包含以下模式：

```text
【YYYY-MM】文章标题.pdf
```

未来 Inventory 可以考虑从 Filename 提取以下 Potential Lightweight Metadata：

```text
filename_year
filename_issue
filename_title
```

这些字段只作为 Potential Lightweight Metadata，不能直接替代 PDF internal metadata。
本次不实现 Filename Parser。

### Candidate Source Corpus Scope Issue

当前项目背景描述约 `70k PDFs`，但当前观察到的 root 为：

```text
/mnt/data_nfs/dataset/original/cmes/journal/
```

该 root 当前仅观察到约 `60.45k PDFs` 的规模，但计数尚未核验，且路径名称表明它可能是
journal 子集。因此当前状态为：

```text
Candidate Source Corpus scope not yet fully confirmed
```

需要确认 `/mnt/data_nfs/dataset/original/cmes/journal/` 是否就是完整 Candidate Source Corpus，
还是约 70k Candidate Source Corpus 中的 journal 子集。在确认前，不能将约 60.45k 视为项目完整
Candidate Source Corpus Count。

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

以下信息用于判断后续工作是否具备独立、可控的存储条件。当前只记录推荐候选，
不将其确定为正式 Architecture Contract，也不创建候选目录。

| Field | Value | Notes |
| --- | --- | --- |
| candidate `MIGB_DATA_ROOT` | `/data/migb` | Canonical / persistent derived artifacts candidate |
| cache / temporary high-I/O workspace candidate | `/data-ssd/migb` | Cache / temporary high-I/O workspace candidate |
| candidate path status | `Proposed - pending permission / readiness confirmation` | 尚未正式决定，也未创建目录 |
| available disk space | `/`: ~697 GiB; `/data-ssd`: ~870 GiB; `/data`: ~2.7 TiB; `/mnt/data_nfs`: ~437 GiB | 采集时可用容量 |
| same disk / different disk from source corpus | `TBD` | Source 位于 `/mnt/data_nfs`；候选路径的物理磁盘关系仍需确认 |
| filesystem | `/`: ext4; `/data-ssd`: ext4; `/data`: ext4; `/mnt/data_nfs`: nfs4 | 按挂载点记录 |
| temporary workspace availability | `TBD` | `/data-ssd/migb` 为候选，写权限和生命周期待确认 |

### Storage Decision Boundary

- `/data/migb` 和 `/data-ssd/migb` 当前仅为 Proposed candidates，状态为 `Proposed - pending permission / readiness confirmation`，不正式决定 `MIGB_DATA_ROOT`。
- 不在本次 Intake 中创建 `/data/migb` 或 `/data-ssd/migb` 目录。
- 如果磁盘空间明显不足，只记录风险和影响，不自行移动或删除任何数据。
- `/mnt/data_nfs` 为 Candidate Source Corpus 所在 NFS，采集时约 `91% used`，记录为：

  ```text
  Storage Risk: High usage on source NFS
  ```

- Candidate Source Corpus 所在 NFS 不应用于保存 Parser output、page images、Evidence assets、temporary workspace、cache 或 Benchmark derived data。
- Candidate Source Corpus 与后续工作区的关系应在信息充分后再确定，并保持 Source Corpus 的 read-only 边界。

## 6. Intake Closeout Checks

以下检查仍属于 Phase 1 Intake Closeout，当前只记录待执行事项，不在本次执行：

| Check | Status | Notes |
| --- | --- | --- |
| NUL-safe total file count | `Pending` | 用于核对根目录下文件总数 |
| NUL-safe PDF count | `Pending` | 用于核对实际 PDF 数量 |
| top-level directory count | `Pending` | 用于补充目录结构统计 |
| non-PDF file count | `Pending` | 用于确认是否混有其他文件类型 |
| symlink count | `Pending` | 用于确认软链接情况 |
| zero-byte PDF count | `Pending` | 用于核对 `0.00 MiB` 观察值，不预设结果 |
| unreadable PDF count | `Pending` | 用于确认读取权限和异常路径 |
| NFS mount options | `Pending` | 用于确认 Candidate Source Corpus 挂载条件 |
| `/data` write permission | `Pending` | 用于确认 `/data/migb` 候选条件 |
| `/data-ssd` write permission | `Pending` | 用于确认 `/data-ssd/migb` 候选条件 |
| candidate corpus parent-directory inspection | `Pending` | 用于确认当前 root 是否为完整 Candidate Source Corpus 或 journal 子集 |

这些检查完成前，不将当前观察值升级为 Final Verified Count，也不推进到 Minimal Corpus Inventory Pipeline Implementation。

## 7. Phase 1 Readiness Questions

以下问题用于判断 Intake 是否可以 closeout。已观察信息不等于最终核验结论，仍未解决的事项保持为 `TBD`。

| # | Readiness Question | Status |
| ---: | --- | --- |
| 1 | 70k PDF 实际根目录是什么？ | `Partially confirmed: /mnt/data_nfs/dataset/original/cmes/journal/; complete scope TBD` |
| 2 | Source Corpus 总大小？ | `Preliminary: ≈225 GiB for observed root; full scope TBD` |
| 3 | 实际 PDF 数量？ | `Needs reconciliation: observed_counts = [60460, 60454]` |
| 4 | 是否混有其他文件类型？ | `TBD` |
| 5 | 是否存在明显按领域/书籍分类的目录？ | `Partially confirmed: observed publication / professional-source groups; taxonomy mapping TBD` |
| 6 | Source Corpus 是否可视为 read-only？ | `TBD` |
| 7 | 是否存在软链接 / 网络挂载？ | `Partially confirmed: NFS4 mount observed; symlink count and mount options TBD` |
| 8 | 可用于 `MIGB_DATA_ROOT` 的磁盘还有多少空间？ | `Partially confirmed: /data ~2.7 TiB; /data-ssd ~870 GiB; write permission TBD` |
| 9 | 是否允许 Docker？ | `Confirmed: Docker Engine 28.3.1; NVIDIA runtime available` |
| 10 | 是否允许联网？ | `TBD` |
| 11 | 是否有 GPU？ | `Confirmed: 4 × NVIDIA GeForce RTX 3090, 24 GiB VRAM each` |
| 12 | 是否有资源限制或作业调度系统？ | `TBD` |
| 13 | 是否与 CPT/SFT Corpus 位于同一存储区域？ | `TBD` |
| 14 | 是否已有已知重复目录或备份目录？ | `TBD` |
| 15 | 是否存在版权 / 权限限制信息？ | `TBD` |

## 8. Do Not Implement Yet

本次 Intake / Readiness Record 不实现以下内容：

- 全量 SHA-256
- PDF page count 扫描
- PDF validity parse
- PDF parser
- MinerU
- OCR
- text layer detection
- duplicate detection
- representative sampling
- Parquet Inventory
- 数据库
- LLM 调用
- GPU workload

以上内容属于后续 **Minimal Corpus Inventory Pipeline** 或更后续阶段。本次不创建代码、数据库、
数据集或 Pipeline，也不执行任何全量或抽样 PDF 处理。

## 9. Current Progress Boundary

在 Intake Closeout 尚未完成前，项目状态保持为：

```text
Current Phase: Phase 1 - Corpus Inventory
Current Milestone: Corpus Inventory v0.1
Current Task: Phase 1 Environment & Corpus Intake
```

当前不将任务推进到 `Inventory Pipeline Implementation`。等 Intake Closeout 完成后，
再推进 Minimal Corpus Inventory Pipeline Design；本次不实现 Pipeline。

## 10. Readiness Summary

| Area | Current Status |
| --- | --- |
| Runtime Environment completeness | `Substantially Complete`；尚缺 network / internet accessibility、API accessibility、resource scheduler / quota information |
| Candidate Source Corpus completeness | `Partially Complete`；尚缺 exact verified count、complete Candidate Source Corpus scope confirmation、symlink / unreadable / zero-byte information、read-only / mount permission confirmation |
| Storage Readiness | `Substantially Complete`；候选为 `/data/migb` 和 `/data-ssd/migb`，但需要 permission confirmation |
| Minimal Corpus Inventory Pipeline design readiness | `Nearly Ready - Intake Closeout Required` |
| Source Corpus safety posture | Read-only by default; no source modification performed |
