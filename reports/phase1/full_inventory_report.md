# Full Corpus Inventory Report

Project: Mechanical Industry General Benchmark
Phase: Phase 1 - Corpus Inventory
Milestone: Corpus Inventory v0.1
Report Status: Remote Full Inventory Completed - Awaiting Phase 1 Gate Review
Full Inventory Verdict: **PASS**

## 1. Run Identity

| Field | Value |
| --- | --- |
| Run ID | `full-20260914T075902Z-faa4565` |
| Remote Repository | `/data/suzhe/Machinery-Industry-Benchmark` |
| Remote Host | `xuelangyun` |
| SSH Alias | `migb` |
| Source Root | `/mnt/data_nfs/dataset/original/cmes/journal` |
| `MIGB_DATA_ROOT` | `/data/suzhe/migb` |
| Git Commit | `faa45659bb5e16a6d634725d2f636f9c3ed450d1` |
| Git dirty state | `false` |
| Inventory Schema | `inventory-v0.2` |
| Python | `3.10.12` |
| PyMuPDF | `1.28.2` |
| PyArrow | `21.0.0` |
| PyYAML | `6.0.3` |
| Worker count | `4` |
| Checkpoint batch size | `500` |
| Started at | `2026-09-14T07:59:18.344805Z` |
| Completed at | `2026-09-14T09:10:22.731506Z` |
| Wall time | `4279.921072496101 s` |

本次 Full Run 使用远程项目本地 `.venv`，运行时 `dirty=false`。本报告只记录 Inventory
Artifact Review 结果，不将 Inventory Statistics 解释为 Benchmark 能力分数。

## 2. Full Scope、Selection 与 Preflight

Full Run 对当前配置的 `cmes_journal` Source Root 执行全量选择，不排除 D1、D2 或 D3 的历史
样本。

| Field | Value |
| --- | --- |
| `selection_stage` | `full` |
| `selection_method` | `all_eligible_pdf_in_configured_source_root` |
| Expected PDF count | `60454` |
| Discovered PDF count | `60454` |
| Expected top-level group count | `20` |
| Actual top-level group count | `20` |
| Selected count | `60454` |
| Processed count | `60454` |
| Unique File Instances | `60454` |
| `sample_manifest.json` | `60454` 个 selected File Instances 的 Full Selection Manifest |

Full Preflight Count Gate 通过：discovery 结果与 authoritative expected count 一致，因此未
忽略新增或缺失路径，也未以旧数字强行匹配。`sample_manifest.json` 保留了六 Artifact Contract，
其语义是 Full Selection Manifest，而不是抽样清单。

### Source Snapshot

| Signal | Before | After |
| --- | ---: | ---: |
| Discovered files | 60454 | 60454 |
| Total bytes | 241371609617 | 241371609617 |
| Top-level groups | 20 | 20 |
| Source snapshot fingerprint | `405e758b3211ef671b6caf80c291de78f09960b74f531993c3b8ba29e33e10c8` | `405e758b3211ef671b6caf80c291de78f09960b74f531993c3b8ba29e33e10c8` |

Snapshot diff：`match=true`，`added_count=0`，`missing_count=0`，
`metadata_changed_count=0`。Full Run 前后 Source Root 保持一致。

## 3. Full Inventory 结果摘要

| Metric | Count / Value |
| --- | ---: |
| Total files | 60454 |
| Successful files | 60447 |
| Partial files | 7 |
| Failed files | 0 |
| Error rows | 7 |
| Total bytes | 241371609617 |
| Hash failures | 0 |
| `source_changed_during_run` | 0 |
| Source snapshot match | `true` |
| Full Inventory Verdict | `PASS` |

### PDF Health

| Signal | Count |
| --- | ---: |
| `pdf_open_status=success` | 60453 |
| `pdf_open_status` failed | 1 |
| `pdf_status=valid` | 60447 |
| `pdf_status=corrupted_or_invalid` | 6 |
| `pdf_status=unknown` | 1 |
| Encrypted | 0 |
| Zero-page PDFs | 6 |

Full Run 使用已冻结的 zero-page 语义：当 `pdf_open_status=success` 且 `page_count=0` 时，
记录为 `pdf_status=corrupted_or_invalid`、`inventory_status=partial`、
`text_layer_status=check_failed`，并产生 `text_sample / zero_page_count` Error Record。

### Text-layer Signal

| Text-layer status | Count |
| --- | ---: |
| `text_present` | 56798 |
| `text_absent` | 3486 |
| `mixed_or_uncertain` | 163 |
| `check_failed` | 7 |

### Text-layer Signal by Parent Group

| Parent group | Total files | Text present | Text absent | Mixed / uncertain | Check failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `duanyajishu` | 1073 | 1073 | 0 | 0 | 0 |
| `hanjie` | 1397 | 1397 | 0 | 0 | 0 |
| `hanjiexuebao` | 7409 | 7291 | 2 | 116 | 0 |
| `jinshurechuli` | 1992 | 1992 | 0 | 0 | 0 |
| `jixiechuandong` | 198 | 198 | 0 | 0 | 0 |
| `jixiegongchengcailiao` | 1481 | 1481 | 0 | 0 | 0 |
| `jixiegongchengxuebao` | 14971 | 14110 | 829 | 28 | 4 |
| `jixiegongchengxuebao2` | 2094 | 2073 | 14 | 7 | 0 |
| `jixieqiangdu` | 2500 | 2499 | 1 | 0 | 0 |
| `lihuajianyan-huaxuefence` | 5559 | 5306 | 253 | 0 | 0 |
| `lihuajianyan-wulifence` | 3658 | 3189 | 469 | 0 | 0 |
| `suxinggongchengxuebao` | 9 | 6 | 0 | 0 | 3 |
| `wusunjiance` | 4489 | 3837 | 652 | 0 | 0 |
| `yeyayuqidong` | 4142 | 4118 | 24 | 0 | 0 |
| `zhizaojishuyujichuang` | 2135 | 1504 | 628 | 3 | 0 |
| `zhizaoyezidonghua` | 1412 | 897 | 512 | 3 | 0 |
| `zhongguohanjie` | 543 | 470 | 73 | 0 | 0 |
| `zhongguojixiegongcheng` | 2891 | 2888 | 0 | 3 | 0 |
| `zhongguozhuzaozhuangbeiyujishu` | 1078 | 1059 | 16 | 3 | 0 |
| `zhuzao` | 1423 | 1410 | 13 | 0 | 0 |
| **Total** | **60454** | **56798** | **3486** | **163** | **7** |

### Filename Signal

| Filename parse status | Count |
| --- | ---: |
| `matched` | 48517 |
| `unmatched` | 11937 |
| `error` | 0 |
| Match rate | `0.8025440831045092`（约 80.25%） |

Filename Parser 仍使用冻结的轻量规则。`unmatched` 表示未匹配该规则，不表示文件错误，
本次未扩展正则规则。

### Exact Duplicate

| Metric | Value |
| --- | ---: |
| Exact duplicate groups | 207 |
| Exact duplicate files | 495 |
| Largest duplicate group size | 15 |
| Recorded duplicate rate | `0.008188043801898965`（约 0.819%） |

以上为 exact binary duplicate 结果，不等同于 document-family、semantic duplicate 或最终
Source Selection 结论。

## 4. Page-count 与 File-size 分布

### Page-count Distribution

Page-count 统计覆盖 60453 个成功打开的 PDF；1 个 PDF 未能打开，因此没有可用 page count。

| Statistic | Value |
| --- | ---: |
| Count | 60453 |
| Minimum | 0 |
| Median | 6 |
| P90 | 10 |
| P95 | 12 |
| P99 | 17 |
| Maximum | 254 |

### File-size Distribution

| Statistic | Value (bytes) |
| --- | ---: |
| Count | 60454 |
| Minimum | 3241 |
| Median | 1395642 |
| P90 | 7437202.3000000045 |
| P95 | 12694347.299999999 |
| P99 | 50430544.220000006 |
| Maximum | 327124975 |

## 5. Error Analysis

Full Run 共产生 7 个 Error Rows，全部被保留在 `errors.parquet`，没有静默跳过。

| Stage | Error category | Count | Parent group |
| --- | --- | ---: | --- |
| `pdf_open` | `FileDataError` | 1 | `jixiegongchengxuebao` |
| `text_sample` | `zero_page_count` | 6 | `jixiegongchengxuebao`（4）；`suxinggongchengxuebao`（3） |

受影响的相对路径如下：

| File Instance ID | Relative path | Stage / category |
| --- | --- | --- |
| `f9e3ee94-207f-50ce-9f42-97ddbb580ec9` | `jixiegongchengxuebao/【2023-13】基于QP改进模型的离心泵性能预测方法.pdf` | `pdf_open / FileDataError` |
| `242da99c-3454-5175-8732-8ebbe746b89f` | `jixiegongchengxuebao/【2023-13】基于数字孪生的大马力拖拉机湿式离合器压力控制方法研究.pdf` | `text_sample / zero_page_count` |
| `1d6f3fb4-e303-5388-ae6f-11fd87738395` | `jixiegongchengxuebao/【2026-8】从低阶建模到全域智能：分布式驱动车辆多物理场耦合机理、估计与控制综述.pdf` | `text_sample / zero_page_count` |
| `4a230461-f25b-5215-bfdd-b61600c26f07` | `jixiegongchengxuebao/【2026-8】面向网络不可靠的智能汽车纵侧向运动控制研究综述.pdf` | `text_sample / zero_page_count` |
| `9f08077a-5387-570b-bec4-c183964c7041` | `suxinggongchengxuebao/【2026-06】十八辊精密轧机辊系非自稳定行为分析及高效控制策略研究.pdf` | `text_sample / zero_page_count` |
| `362a1eda-97e2-5000-92d3-58cbc32bbe99` | `suxinggongchengxuebao/【2026-06】立辊减宽和定宽机减宽对板厚均匀性的影响.pdf` | `text_sample / zero_page_count` |
| `96e2b8db-a59c-56fa-a891-764b2b770962` | `suxinggongchengxuebao/【2026-06】铜_铝异质薄壁管冷滚压连接成形锁头截面圆度分析.pdf` | `text_sample / zero_page_count` |

本次无 retry、无 exhausted retry、无 hash failure、无 Source Consistency failure。1 个
`FileDataError` 和 6 个 zero-page 条件均作为 `partial` 记录，不影响全量行数与 Artifact
完整性。

## 6. Filename Parse 按 Parent Group 分布

| Parent group | Total files | Matched | Unmatched | Error |
| --- | ---: | ---: | ---: | ---: |
| `duanyajishu` | 1073 | 1073 | 0 | 0 |
| `hanjie` | 1397 | 1389 | 8 | 0 |
| `hanjiexuebao` | 7409 | 7409 | 0 | 0 |
| `jinshurechuli` | 1992 | 1992 | 0 | 0 |
| `jixiechuandong` | 198 | 198 | 0 | 0 |
| `jixiegongchengcailiao` | 1481 | 380 | 1101 | 0 |
| `jixiegongchengxuebao` | 14971 | 7590 | 7381 | 0 |
| `jixiegongchengxuebao2` | 2094 | 0 | 2094 | 0 |
| `jixieqiangdu` | 2500 | 2500 | 0 | 0 |
| `lihuajianyan-huaxuefence` | 5559 | 5559 | 0 | 0 |
| `lihuajianyan-wulifence` | 3658 | 3658 | 0 | 0 |
| `suxinggongchengxuebao` | 9 | 9 | 0 | 0 |
| `wusunjiance` | 4489 | 4489 | 0 | 0 |
| `yeyayuqidong` | 4142 | 4142 | 0 | 0 |
| `zhizaojishuyujichuang` | 2135 | 2123 | 12 | 0 |
| `zhizaoyezidonghua` | 1412 | 1412 | 0 | 0 |
| `zhongguohanjie` | 543 | 444 | 99 | 0 |
| `zhongguojixiegongcheng` | 2891 | 2727 | 164 | 0 |
| `zhongguozhuzaozhuangbeiyujishu` | 1078 | 0 | 1078 | 0 |
| `zhuzao` | 1423 | 1423 | 0 | 0 |
| **Total** | **60454** | **48517** | **11937** | **0** |

### Unmatched Filename Pattern Examples

以下是从 `statistics.json` 保留的样例，用于后续评估 Filename Parser v0.2；本次不据此修改
规则，也不据此排除文件。

| Parent group | Filename example |
| --- | --- |
| `hanjie` | `2195铝锂合金焊接缺陷固相准等强修复技术.pdf` |
| `hanjie` | `双立爆炸大板面TA2_Q235B复合板宏观变形初探 (1).pdf` |
| `hanjie` | `预热温度对U75V激光熔覆成形性能的影响.pdf` |
| `jixiegongchengcailiao` | `【2019-3】316L奥氏体不锈钢稳定辊轴头断裂的原因.pdf` |
| `jixiegongchengcailiao` | `【2019-3】不同温度锻压时Inconel 625镍基高温合金的形变量和晶粒尺寸.pdf` |
| `jixiegongchengxuebao` | `【2005-6】湿型砂质量参数智能测试车的研制.pdf` |
| `jixiegongchengxuebao` | `【2016-7】复杂零件结构设计的概念单元方法.pdf` |

## 7. Throughput、Checkpoint 与 Runtime Snapshot

| Metric | Value |
| --- | ---: |
| Wall time | `4279.921072496101 s` |
| Files/sec | `14.12502683483892` |
| MiB/sec | `53.78367986284364` |
| Checkpoint write time | `485.24072059616446 s` |
| Checkpoint batch size | `500` |
| Resume count | `0` |
| Checkpoint reused count | `0` |
| Checkpoint reprocessed count | `0` |
| Resume startup time | `0.0 s` |
| Retry attempts total | `0` |
| Files recovered by retry | `0` |

Full Run 不是 resume invocation；以上 throughput 是本次完整 Run 的最终记录。

| Runtime signal | Value |
| --- | ---: |
| Runtime hostname | `xuelangyun` |
| Runtime disk path | `/data/suzhe/migb` |
| Disk total | `4960385134592` bytes（约 4.51 TiB） |
| Disk available | `2948515033088` bytes（约 2.68 TiB） |
| Available memory snapshot | `40495050752` bytes（约 37.7 GiB） |
| Swap status | `enabled` |
| Swap total | `8589930496` bytes（约 8 GiB） |
| Swap free | `0` bytes |
| Worker count | `4` |

Swap 在采集时无可用空间，记录为运行时风险信号；本次 Run 未因此产生失败。后续扩大
Inventory workload 前应重新检查内存、Swap 和并发策略。

## 8. Source Safety、Provenance 与历史 Artifact 完整性

- Source Root `/mnt/data_nfs/dataset/original/cmes/journal` 按项目策略作为 read-only input。
- Full Run 未 rename、move、delete、OCR、执行 MinerU 或向 Source Corpus 写回。
- 所有派生 Artifact 均写入 `/data/suzhe/migb`，与 Source Corpus 保持物理/逻辑分离。
- Output Path Safety Check 为 `passed`。
- `source_changed_during_run`、Source Consistency issue 和 snapshot metadata change 均为 0。
- Manifest 记录了 hostname、commit、dirty state、Python/tool versions、config snapshot、
  source snapshot 和运行时资源信息。
- D1、D2、D3 历史 Artifact 的完整性复核结果为 `prior_artifact_integrity_unchanged=true`。

| Prior Run | Artifact integrity |
| --- | --- |
| `d1-20260914T060712Z-406473f` | 6/6 unchanged |
| `d2-20260914T062102Z-18a5aad` | 6/6 unchanged |
| `d3-20260914T070000Z-ba05b05` | 6/6 unchanged |

Full Run 只覆盖当前配置的 `cmes_journal` Source Root，不代表项目级完整 Candidate Source
Corpus，也不自动做 Benchmark Source Corpus Selection。

## 9. Canonical Artifact Validation

Canonical Artifact Directory：

```text
/data/suzhe/migb/inventory/runs/full-20260914T075902Z-faa4565
```

### Artifact Checksums

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `files.parquet` | 15986177 | `608e8fcbbcd22f464b849a4f87d1f16068a506a01c718911572502c0fa54102f` |
| `duplicate_groups.parquet` | 48873 | `b016a7f7ed2c15ae8ab90deb9a31219c277ab4cdbca5ae1d5985aaac8e35fac2` |
| `errors.parquet` | 4677 | `88654ad1dc1817369b7e43f8df1deeef2ef9563fca34e10b3e8e2e762d913de0` |
| `sample_manifest.json` | 17108170 | `da7556524d315e6bbfc5524e69b08a422046c6fc0e0f7cf9c11c2b088e19bf72` |
| `manifest.json` | 12963 | `c46a7170c3c391fcb551a449e046f55ee0fa29fc477edc3cdbbec735f44a23e3` |
| `statistics.json` | 24298 | `24d4ad3a7d6efb53859fb02379da9e6ffb39a1834f6755fd11e7cdd65a9dd2d4` |

`manifest.json` 的 checksum 使用既定规则：将自身 `sha256` 规范化为 64 个零后计算；其余
Artifact 使用原始文件 SHA-256。

### Validation Summary

| Validation | Result |
| --- | --- |
| Canonical Artifact count | 6 |
| `files.parquet` row count | 60454 |
| `duplicate_groups.parquet` row count | 495 |
| `errors.parquet` row count | 7 |
| Full Selection Manifest item count | 60454 |
| Schema validation | `passed` |
| Row accounting | `passed` |
| Checksum validation | `passed` |
| Artifact validation status | `passed` |

`duplicate_groups.parquet` 按一条 duplicate member 一行记录；495 行对应 207 个 exact
duplicate groups。六个 Canonical Artifact 均已生成并通过校验。

## 10. Findings、限制与后续 Gate

本次 Full Inventory 已完成当前 `cmes_journal` Source Root 的全量、可审计 Inventory。需要
在后续 Corpus Review / Source Selection 中关注的观测包括：

1. 6 个 zero-page / invalid PDF 和 1 个 `FileDataError` 需要在后续质量评估中保留其状态并
   决定是否进入后续 Source Selection。
2. `text_absent`、`mixed_or_uncertain` 和 `check_failed` 是轻量 text-layer signal，不是
   完整 OCR 或内容质量结论。
3. 11,937 个文件未匹配当前 Filename Parser 规则，不应因此直接删除或排除。
4. Exact duplicate 结果不替代 document-family 级别的重复、版本和 contamination 分析。
5. 当前结果不解决项目级约 70k Candidate Source Corpus 的最终范围，也不决定
   Benchmark Source Corpus。

以上均属于后续评审输入，不在本次报告中擅自作 Source Selection 或 Taxonomy 决策。

### Review Boundary

Full Inventory Verdict 和 Artifact Validation 均为 `PASS`，但本报告完成后仍需进行 Phase 1
Gate Review。当前不自动进入 Phase 2，也不授权 Phase 2 Taxonomy Calibration & Source
Selection。

Next Task：Review Full Corpus Inventory and close Phase 1 before authorizing Phase 2 Taxonomy
Calibration & Source Selection.
