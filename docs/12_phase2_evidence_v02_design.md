# Phase 2 Evidence v0.2 Design

Project: Mechanical Industry General Benchmark
Document: Phase 2 Evidence v0.2 Design
Version: 0.2
Status: Diagnostic Design Only - v0.3 Fallback Diagnostic Completed Separately
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2B Evidence v0.3 Implementation

## 1. Background

Gate 2B Evidence v0.1 使用既有 Calibration Sample 和 Audit Pools，以 PyMuPDF 提取
physical first 3 pages，并使用 12,000 字符全局 cap。Runtime Sampling、Artifact Schema、
Source Provenance 和 checksum 均已通过，但 20-item Main Evidence Review Set 的
Evidence Sufficiency 只有 16/20 sufficient。

本设计基于既有 Gate 2B Runtime Artifact 的只读诊断，不改变 Calibration Sample、pool
membership 或任何 Runtime Artifact。诊断目标仅是判断：增加确定性的正文页和使用第二种
文本 extractor，是否足以让后续 Annotator 理解文档主题；不进行 Domain classification，
也不填写 D01-D12 标签。

## 2. Evidence v0.1 Review Findings

原 Review 的 4 个问题项为 3 条 `insufficient` 和 1 条 `borderline`。问题集中在：

- 部分 Evidence 的字符映射异常，标题、摘要或正文片段不可稳定理解；
- `needs_more_pages` 与 `garbled` 在问题项中同时出现，但增加页面不能自动解决编码问题；
- Unicode 统计指标与人工可读性不能等价，不能用单一字符阈值自动判定 `garbled`。

因此，Evidence v0.2 必须把以下四件事分开定义：

1. page selection；
2. extractor；
3. quality signal；
4. fallback routing。

本设计不把它们合并成一个自动 routing 函数。

## 3. Problem Set

Problem Set 固定复用已完成 Evidence Sufficiency Review 的 4 条问题项，不重新抽样：

| Item | `calibration_item_id` | `file_instance_id` | Parent Group | Relative path | Pages | v0.1 pages | v0.1 chars | v0.1 quality labels | v0.1 sufficiency |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| P1 | `67504202-11fc-51ae-8017-9ad5f4bdefe5` | `73140782-13a3-5089-91f3-830dac4c50bb` | `hanjie` | `hanjie/【2020-12】Ag和Zn对Sn58Bi钎料润湿性及焊点组织的影响.pdf` | 10 | `[0,1,2]` | 4339 | `garbled, needs_more_pages` | insufficient |
| P2 | `8ff31d50-6ffe-5e49-8890-917e51c8e936` | `cbb7bbfc-3ae1-5543-ac19-fd35f0c1ef6c` | `jinshurechuli` | `jinshurechuli/【2024-10】冷轧压下率对IF钢退火热处理织构及成形性的影响.pdf` | 5 | `[0,1,2]` | 5703 | `readable, garbled, needs_more_pages` | borderline |
| P3 | `791f9b84-1b42-54eb-a977-6400614f0285` | `7a88b028-bc38-51f1-b522-2708d361aea6` | `yeyayuqidong` | `yeyayuqidong/【2018-09】多柱塞阀配流往复式容积泵新型流量调节方法研究.pdf` | 5 | `[0,1,2]` | 5617 | `garbled, needs_more_pages` | insufficient |
| P4 | `d2816f50-ace1-5dfd-87b0-6ab4b8df929e` | `db620b26-0f63-566f-ac8c-b5ecc9586cc4` | `zhongguozhuzaozhuangbeiyujishu` | `zhongguozhuzaozhuangbeiyujishu/【2022-5】V法造型密闭式涂料烘干系统的优化设计.pdf` | 3 | `[0,1,2]` | 3749 | `garbled, needs_more_pages` | insufficient |

Review note 只描述 Evidence 的可读性和主题上下文，不表示 Domain 分类结果。

## 4. Control Set

为避免只针对问题项设计，从原 Main Review Set 的 16 条 `sufficient` 中确定性选择 4 条
control。原 16 条中没有与 4 个问题项相同的 Parent Group，因此按 page count 距离最小、
再按 `parent_group`、`relative_path`、`file_instance_id` 稳定排序的一对一匹配规则选择：

| Control | `calibration_item_id` | `file_instance_id` | Parent Group | Relative path | Pages | v0.1 chars | v0.1 quality labels | v0.1 sufficiency | Matched problem |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| C1 | `79562004-0aef-5222-afc8-b0e0bcb73cba` | `845edf7c-b950-5e5b-887c-532796b567b0` | `suxinggongchengxuebao` | `suxinggongchengxuebao/【2026-06】组合本构模型对高强钢CTB电池箱体纵梁辊弯回弹预测精度的影响.pdf` | 10 | 8389 | `readable, potentially_sufficient` | sufficient | P1 |
| C2 | `006ef0ba-d56b-5aab-b4d6-f45fbb3922ca` | `a8035ce4-5217-5179-ac86-2ac2f0f3ae51` | `hanjiexuebao` | `hanjiexuebao/【2011-12】基于SYSWELD的穿孔等离子弧焊接温度场有限元分析.pdf` | 5 | 4086 | `readable, potentially_sufficient` | sufficient | P2 |
| C3 | `78ba6d84-c7b6-5dca-9ff9-1838689c8bc1` | `43fef19b-d65e-5a6b-b0f4-5085d21881d2` | `zhuzao` | `zhuzao/【2023-03】厚大断面球墨铸铁齿轮铸件的研制.pdf` | 5 | 3510 | `readable, potentially_sufficient` | sufficient | P3 |
| C4 | `7d1cfa14-757d-56aa-9c0f-9b59c27405aa` | `38c6fc51-b6b8-5086-ba9f-63f367db71b4` | `lihuajianyan-huaxuefence` | `lihuajianyan-huaxuefence/【2015-12】八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素.pdf` | 4 | 5829 | `readable, potentially_sufficient` | sufficient | P4 |

## 5. Diagnostic Method

### 5.1 Immutable Inputs and Stop Boundary

诊断只读取：

```text
/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565
```

以下 Runtime Artifact 保持 immutable：

```text
calibration_sample.parquet
calibration_evidence.jsonl
manifest.json
statistics.json
```

诊断没有重新抽样，没有写入 Runtime Artifact，没有写回 Source Corpus，没有执行 OCR、
MinerU、LLM Taxonomy Annotation 或 Source Selection。8 个 Source PDF 的 size 和 mtime
在 probe 前后均未变化。

### 5.2 Deterministic Probe Selection

对于 page count 为 `N` 的 PDF，Probe B/C 使用：

```python
base = [0, 1, 2]
middle_probe = floor((N - 1) * 0.50)
late_probe = floor((N - 1) * 0.75)
selected = sorted(unique(i for i in base + [middle_probe, late_probe] if 0 <= i < N))
```

8 个 Item 的实际页面集合为：

| Items | Page count | Probe B/C pages |
| --- | ---: | --- |
| P1, C1 | 10 | `[0,1,2,4,6]` |
| P2, P3, C2, C3 | 5 | `[0,1,2,3]` |
| P4, C4 | 3 / 4 | `[0,1,2]` |

Probe A 不重新读取 PDF，直接使用既有 v0.1 Evidence Artifact 作为 baseline：physical
first 3 pages，global cap 12,000。

### 5.3 Extraction Strategies

| Probe | Extractor | Pages | Per-page cap | Global cap | Purpose |
| --- | --- | --- | ---: | ---: | --- |
| A | existing PyMuPDF v0.1 Artifact | `[0,1,2]` | not recorded in v0.1 | 12000 | immutable baseline |
| B | PyMuPDF | deterministic first3 + body probes | 4000 | 20000 | test page coverage and bounded page contribution |
| C | `/usr/bin/pdftotext -layout` | exactly the same pages as B | 4000 | 20000 | test whether Poppler improves extraction encoding |

本次远程环境中 `pdftotext` 可用：

```text
/usr/bin/pdftotext
pdftotext version 22.02.0
```

Probe C 对每个 selected page 使用 page-range extraction，没有读取全文。

### 5.4 Character and Page Accounting

Probe B/C 对每一页先独立应用 4,000 字符 cap，再组装 page delimiter，最后应用 20,000
字符 global cap。每个 page record 必须保留：

```text
page_index
raw_char_count
stored_char_count
page_truncated
```

`raw_char_count` 不包含 page delimiter；`evidence_char_count` 包含组装后的 delimiter，
并表示 global cap 后的 stored Evidence 长度。Global `evidence_truncated` 与 page-level
`page_truncated` 分开记录。

## 6. Root Cause Findings

### 6.1 Paired Problem Comparison

| Item | v0.1 | PyMuPDF Probe B | pdftotext Probe C |
| --- | --- | --- | --- |
| P1 | insufficient；first 3 pages 主要是不可读编码片段 | insufficient；增加 pages `[4,6]` 后仍为相同类型乱码 | insufficient；layout 改善字符可打印比例，但标题和技术上下文仍不可稳定理解 |
| P2 | borderline；题目和部分技术词可辨，摘要/正文受乱码影响 | borderline；增加 page 3 提供正文/图示片段，但没有消除字符映射问题 | borderline；排版结构略有改善，但 glyph mapping 仍不足以升为 sufficient |
| P3 | insufficient；Evidence 主要为异常编码 | insufficient；增加 page 3 仍为异常编码 | insufficient；可打印比例上升，但主题仍不能稳定理解 |
| P4 | insufficient；全部 3 页均受异常编码影响 | insufficient；文件仅 3 页，没有额外正文页可增加 | insufficient；字符量增加，但语义仍不可稳定识别 |

### 6.2 Paired Control Regression

| Control | v0.1 | PyMuPDF Probe B | pdftotext Probe C | Regression conclusion |
| --- | --- | --- | --- | --- |
| C1 | sufficient | sufficient | sufficient | no meaningful regression |
| C2 | sufficient | sufficient | sufficient | no meaningful regression |
| C3 | sufficient | sufficient | sufficient | no meaningful regression |
| C4 | sufficient | sufficient | sufficient | no meaningful regression |

## 7. Evidence v0.2 Decision

诊断结果属于 **Case D**：additional body pages 没有解决问题项，`pdftotext -layout` 也
没有把问题项提升到 `sufficient`。因此当前不能把任何 text-only extractor 方案宣称为
Gate 2C 的通用 Evidence Contract。

Evidence v0.2 的诊断设计边界为：

1. page selection 使用 first 3 pages 加 deterministic middle/late body probes；
2. primary extractor 使用 PyMuPDF；
3. per-page cap 为 4,000，global cap 为 20,000；
4. quality signal 使用人工 review labels 加轻量 Unicode metrics，暂不冻结生产阈值；
5. `pdftotext -layout` 仅保留为 diagnostic-only extractor，不作为 Evidence v0.2/v0.3 的
   Production Fallback，也不对全部 767 条默认双重抽取；
6. fallback 仍不可读的 Item 必须进入 unresolved review queue，不得自动标为 sufficient；
7. 视觉/OCR 处理单独进入 Evidence v0.3 设计，不在本次 v0.2 或当前 Probe 中执行。

因此：

```text
Evidence v0.2: Diagnostic design only; not accepted for Full Gate 2B rerun
pdftotext: diagnostic-only
Gate 2B operational status: HOLD
Gate 2C: NOT AUTHORIZED
```

## 8. Page Selection Contract

未来 Evidence v0.2 Runtime 只能使用上述 deterministic selector。Selector 必须：

- 保留 page 0、1、2 的顺序；
- 添加 `floor((N - 1) * 0.50)` 和 `floor((N - 1) * 0.75)`；
- 删除越界 index 和重复 index；
- 最终按升序输出；
- 将最终 `evidence_page_indices` 写入 Evidence Record；
- 不使用 runtime random，不使用 semantic page selection；
- 对少于 3 页的 PDF 只读取现有页面。

## 9. Character Budget

Evidence v0.2 的候选预算为：

```text
per_page_cap = 4000
global_cap = 20000
```

Per-page cap 先于 global cap 生效。超过 per-page cap 的页面记录
`page_truncated=true`；组装后超过 global cap 才记录 global `evidence_truncated=true`。
Page delimiter、页面顺序和 cap 状态必须可复现。

Evidence v0.1 的 `max_extracted_chars=12000` 只作为 Probe A immutable baseline，不被
回写或修改。

## 10. Extractor Contract

Evidence v0.2 的 extractor contract 仅定义接口和记录要求，不在本次实现 Production
Runtime：

```python
select_evidence_pages(...)
extract_with_pymupdf(...)
extract_with_fallback(...)
compute_text_quality_signals(...)
assemble_evidence(...)
```

Primary extractor：

- PyMuPDF `text` extraction；
- 只读取 selected pages；
- 规范化 line endings；
- 保留 page-level raw/stored accounting；
- 不执行 OCR、MinerU 或 PDF rewrite。

## 11. Fallback Contract

本节只记录已完成的诊断对比，不冻结 Production Fallback。`pdftotext -layout` 的当前
状态为 `diagnostic-only`；它只能在后续单独授权的诊断中按同一 selected page set 执行，
不能作为 Evidence v0.2/v0.3 的生产 fallback。未来若采用其他 fallback，Fallback Record
至少记录：

- `fallback_reason`；
- `fallback_extractor`；
- `fallback_pages`；
- `fallback_status`；
- fallback 的 page-level raw/stored counts；
- fallback 后的 quality signals 和 manual review result。

当前 Probe 表明 `pdftotext` 对 P1–P4 没有形成足够改善，因此：

- 不把 `pdftotext` 结果自动视为优先结果或 Production Evidence；
- 不因 printable ratio 上升而自动清除 `garbled`；
- 不对所有 767 items 进行双重抽取；
- 不将失败项绕过 review queue 送入 Gate 2C。

Evidence v0.3 已在独立诊断中完成 RapidOCR CPU fallback 的验证，并冻结了当前诊断范围内
的 fallback strategy；本文件仍只定义 v0.2 的诊断设计，不把 v0.3 fallback 回写成 v0.2
Production Runtime。v0.3 的生产触发条件、成本边界、provenance 和质量复核以
`docs/13_phase2_evidence_v03_visual_ocr_fallback.md` 为准。

## 12. Quality Signals

每个 v0.2 Probe Record 至少保留以下诊断信号：

```text
total_chars
replacement_char_count
private_use_char_count
control_char_count
printable_char_ratio
```

定义：

- `replacement_char_count`：U+FFFD 数量；
- `private_use_char_count`：Unicode category `Co` 数量；
- `control_char_count`：Unicode category `Cc` 数量，但排除 `\n`、`\r`、`\t`；
- `printable_char_ratio`：从分母排除 `\n`、`\r`、`\t` 后，`isprintable()` 字符的比例。

这些指标只用于观察和 routing candidate analysis，不冻结生产 threshold，也不允许
使用类似 `private_use > X → garbled` 的自动判定。

Manual review 继续使用既有尺度：

```text
sufficient / borderline / insufficient
readable / potentially_sufficient / front_matter_heavy / too_short
garbled / empty / needs_more_pages
```

## 13. Schema Changes

现有 v0.1 Runtime Artifact 不修改。未来新建 v0.2 Evidence Record 时，建议在保留既有
provenance 字段和 `evidence_page_indices` 的基础上增加：

| Field | Purpose |
| --- | --- |
| `evidence_page_selection_strategy` | 记录 `first3_plus_middle_late_probes` |
| `evidence_per_page_char_cap` | 记录 4000 |
| `evidence_global_char_cap` | 记录 20000 |
| `evidence_page_records` | 记录 page index、raw/stored chars 和 page truncation |
| `evidence_primary_extractor` | 记录 `pymupdf` |
| `evidence_fallback_extractor` | 记录未来批准的 fallback；`pdftotext-layout` 在当前设计中为 diagnostic-only |
| `evidence_extractor_used` | 记录 primary / fallback / unresolved |
| `evidence_quality_signals` | 保存上述 Unicode metrics |
| `evidence_quality_labels` | 保存允许的 quality labels |
| `evidence_sufficiency` | 保存 `sufficient` / `borderline` / `insufficient` |
| `evidence_routing_reason` | 说明是否因 garbled、too short 或 needs more pages 路由 |
| `evidence_review_note` | 保存只描述 Evidence 的人工 Review note |

这些是 v0.2 设计字段，不代表本次已经创建或写入新的 Runtime Artifact。

## 14. Gate 2B Re-run Plan

本次不执行 Full Evidence v0.2 Runtime。后续如果获得明确授权：

1. 复用同一 `calibration_sample_id`；
2. 复用同一 767 个 `calibration_item_id`、`file_instance_id` 和 pool membership；
3. 不重新抽样，不覆盖 v0.1 Run，使用新的 run directory 和 manifest；
4. 运行前后验证 Source PDF size/mtime 不变；
5. 复用已完成诊断的 Evidence v0.3 visual/OCR fallback strategy，对 quality-risk item 决定是否调用 fallback；
6. 使用与本次完全相同的 20 个 Main Review Item 进行 paired Gate 2B Evidence Review；
7. 同时报告 Main、Short、Truncated、Encoding/Garbled、Mixed Text 和
   Filename-unmatched Review；
8. 如果仍需调整 visual/OCR 生产 contract，先完成独立设计和授权，不得以 OCR 全量处理绕过 Gate。

## 15. Acceptance Criteria

Evidence v0.2 后续只有在以下条件同时满足时，才可作为 Gate 2C 的候选输入：

- deterministic page selector 和 page-level/global cap 可复现；
- 767 items 与原 Calibration Sample 一一对应；
- v0.1 Runtime Artifact 保持 immutable；
- Primary / fallback extractor、quality signal 和 routing reason 完整记录；
- Source Provenance 和 Source Safety 校验通过；
- 使用同一 20-item Main Review Set；
- `sufficient >= 18 / 20`；
- `insufficient <= 1 / 20`；
- 不降低 Gate threshold，不以 Domain Annotation 替代 Evidence Review；
- Gate 2B 通过后才允许进入 Gate 2C。

当前诊断未满足最后两项 review rate 条件，因此不关闭 Gate 2B。

## 16. Open Questions

以下问题仍为 TBD，不在本次设计中擅自决定：

1. 4 个问题 PDF 的乱码究竟来自嵌入字体映射、PDF 内部编码，还是 extraction library 行为？
2. Evidence v0.3 生产运行的 OCR trigger、成本上限和人工复核比例如何在更大样本上定义？
3. 当前已验证的 RapidOCR fallback 是否需要增加 visual crop 或其他 PDF text extractor？
4. `pdftotext -layout` 是否保留为正式 fallback，还是仅作为诊断工具？
5. v0.2 quality signals 是否需要在更大样本上校准 routing threshold？
6. unresolved Evidence 是否允许进入后续 calibration audit，还是必须先完成 v0.3？

## 17. Current Decision and Stop Boundary

本次已完成 8-file deterministic diagnostic probe 和 Evidence v0.2 诊断设计。
结果支持“文本覆盖增加和 Poppler fallback 均不足以解决当前乱码样本”的结论，但不构成
Gate 2B 通过、Domain Taxonomy 冻结或 Gate 2C 授权。

当前停止在 v0.2 文档自身的设计边界；Evidence v0.3 已完成固定 8-file diagnostic，但
Full Gate 2B Runtime 仍未授权。当前状态为：

```text
Evidence v0.2 diagnostic design only
Full Gate 2B rerun not authorized
Gate 2B HOLD
No full 767-item rerun
No v0.2 OCR / MinerU Runtime
Evidence v0.3 diagnostic completed; fallback strategy frozen separately
No LLM Taxonomy Annotation
```
