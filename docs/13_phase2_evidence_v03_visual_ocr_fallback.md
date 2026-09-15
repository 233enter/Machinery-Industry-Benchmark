# Phase 2 Evidence v0.3 Visual/OCR Fallback

Project: Mechanical Industry General Benchmark
Document: Phase 2 Evidence v0.3 Visual/OCR Fallback
Version: 0.1
Status: Reviewed - Contract Frozen
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2B Routing Contract Gate Decision

## 1. Background

Evidence v0.2 的 8-file diagnostic 已确认：PyMuPDF 增加正文页和 `pdftotext -layout` 均未
解决 4 个 Problem Item 的主要乱码问题。本次进一步验证原始 PDF 页面是否可以通过视觉
渲染和中文 OCR 恢复可用 Evidence。

本文件记录 Evidence v0.3 visual/OCR fallback 的诊断结果和当前冻结的 fallback strategy。
本次只对固定 8-file Diagnostic Set 做验证，不代表已经完成 Full Evidence v0.3 Runtime。

## 2. Environment and OCR Engine Availability

远程环境：

```text
SSH alias: migb
hostname: xuelangyun
Python runtime: /data/suzhe/Machinery-Industry-Benchmark/.venv/bin/python
```

本次在远程项目 `.venv` 中按授权安装并验证最小 CPU OCR 依赖。运行时检查结果：

| Component | Result |
| --- | --- |
| `rapidocr` | available；version `3.9.2` |
| `onnxruntime` | available；version `1.23.2` |
| `CPUExecutionProvider` | available；text detection/classification/recognition sessions 均实际使用 CPU |
| `command -v tesseract` | unavailable；本次未安装 Tesseract |
| `paddleocr` | unavailable；未安装且不属于本次最小依赖 |

合成图包含以下四行：

```text
机械制造与自动化
齿轮传动磨损分析
Mechanical Engineering
123456
```

RapidOCR 均识别出上述四行。安装仅发生在
`/data/suzhe/Machinery-Industry-Benchmark/.venv`，未执行 `sudo apt install`、
`apt install` 或 `conda install`。当前运行时结论为：

```text
RapidOCR CPU Runtime Available
Chinese/English/Digit Synthetic Check Passed
```

## 3. Fixed Problem / Control Set

本次仍固定使用 Evidence v0.2 diagnostic 已确定的 4 个 Problem 和 4 个 Control，不重新
抽样，不更换 `calibration_item_id`、`file_instance_id` 或 `relative_path`。

| Item | Role | `calibration_item_id` | Parent Group | Relative path |
| --- | --- | --- | --- | --- |
| P1 | problem | `67504202-11fc-51ae-8017-9ad5f4bdefe5` | `hanjie` | `hanjie/【2020-12】Ag和Zn对Sn58Bi钎料润湿性及焊点组织的影响.pdf` |
| P2 | problem | `8ff31d50-6ffe-5e49-8890-917e51c8e936` | `jinshurechuli` | `jinshurechuli/【2024-10】冷轧压下率对IF钢退火热处理织构及成形性的影响.pdf` |
| P3 | problem | `791f9b84-1b42-54eb-a977-6400614f0285` | `yeyayuqidong` | `yeyayuqidong/【2018-09】多柱塞阀配流往复式容积泵新型流量调节方法研究.pdf` |
| P4 | problem | `d2816f50-ace1-5dfd-87b0-6ab4b8df929e` | `zhongguozhuzaozhuangbeiyujishu` | `zhongguozhuzaozhuangbeiyujishu/【2022-5】V法造型密闭式涂料烘干系统的优化设计.pdf` |
| C1 | control | `79562004-0aef-5222-afc8-b0e0bcb73cba` | `suxinggongchengxuebao` | `suxinggongchengxuebao/【2026-06】组合本构模型对高强钢CTB电池箱体纵梁辊弯回弹预测精度的影响.pdf` |
| C2 | control | `006ef0ba-d56b-5aab-b4d6-f45fbb3922ca` | `hanjiexuebao` | `hanjiexuebao/【2011-12】基于SYSWELD的穿孔等离子弧焊接温度场有限元分析.pdf` |
| C3 | control | `78ba6d84-c7b6-5dca-9ff9-1838689c8bc1` | `zhuzao` | `zhuzao/【2023-03】厚大断面球墨铸铁齿轮铸件的研制.pdf` |
| C4 | control | `7d1cfa14-757d-56aa-9c0f-9b59c27405aa` | `lihuajianyan-huaxuefence` | `lihuajianyan-huaxuefence/【2015-12】八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素.pdf` |

## 4. Rendering Strategy

页面必须从原始 PDF 直接使用 PyMuPDF render，不得对乱码文本截图或做 OCR。页面集合继续
复用 Evidence v0.2：

```text
first 3 pages + floor((N - 1) * 0.50) + floor((N - 1) * 0.75)
```

本次实际比较：

```text
200 DPI
300 DPI
```

P1、P2 在两个 DPI 下运行；根据识别质量和运行时间选择 200 DPI。最终 200 DPI 在 P1–P4
和 C1–C4 上运行。每页都从原始 PDF 直接 render 到系统临时目录，处理结束后临时 PNG
自动清理；OCR Probe 本身没有写入 Source Root、历史 Runtime Artifact 或诊断输出目录。
后续 routing signal calibration 只在诊断输出目录写入独立 `quality_signals.parquet`，不写回
canonical Run。

## 5. OCR Configuration

本次冻结的路径为 PyMuPDF render + RapidOCR：

```python
engine = RapidOCR()
page_pixmap = page.get_pixmap(dpi=200, alpha=False)
engine(rendered_png_path)
```

RapidOCR 使用 `onnxruntime` 的 `CPUExecutionProvider`；当前记录的 OCR languages 为
`ch+en`（RapidOCR 中英文兼容模型）。无论实现方式，OCR Evidence 必须：

- 使用原始 PDF 页面图像；
- 继续使用相同 `selected_page_indices`；
- 每页最多保存 4,000 Unicode chars；
- 全局最多保存 20,000 chars；
- 保留 `<<<PAGE:n>>>` delimiter；
- 记录 page-level raw/stored count 和 truncation；
- 不把 OCR 应用于全部 600、767 或 60,454 个文件。

本次不采用 Tesseract；`pdftotext -layout` 仍为 `diagnostic-only`。

## 6. Paired Review Protocol

未来 OCR Probe 需要对每个 Item 依次比较：

```text
A = Evidence v0.1
B = PyMuPDF body-probe Evidence
C = pdftotext body-probe Evidence
D = OCR fallback Evidence
```

Review scale 不变：

```text
sufficient / borderline / insufficient
```

Quality labels 不变：

```text
readable
potentially_sufficient
garbled
too_short
empty
needs_more_pages
```

OCR 路径值得进入 Evidence v0.3 的最低条件为：

```text
Problem Set: at least 3 / 4 sufficient
Control Set: at least 3 / 4 remain sufficient
```

本次 OCR 结果为 Problem Set `4 / 4 sufficient`，Control Set `4 / 4 sufficient`，满足
进入 Evidence v0.3 fallback strategy 冻结的最低条件。

P1、P2 的 300 DPI 对照与 200 DPI 均可稳定理解；300 DPI 没有带来足以抵消额外运行时间
的明显质量提升，因此当前冻结 200 DPI。

固定 8-file Diagnostic Set 的人工复核结果：

| Item | 200 DPI | 300 DPI 对照 | Final decision |
| --- | --- | --- | --- |
| P1 | sufficient | sufficient | sufficient |
| P2 | sufficient | sufficient | sufficient |
| P3 | sufficient | not run | sufficient |
| P4 | sufficient | not run | sufficient |
| C1 | sufficient | not run | sufficient |
| C2 | sufficient | not run | sufficient |
| C3 | sufficient | not run | sufficient |
| C4 | sufficient | not run | sufficient |

## 7. Provenance and Runtime Cost

每次实际 OCR Evidence 至少记录：

```text
extractor
ocr_engine
ocr_engine_version
ocr_languages
render_dpi
selected_page_indices
ocr_raw_char_count
ocr_stored_char_count
ocr_runtime_seconds
```

本次最终 200 DPI 结果：

| Metric | Result |
| --- | --- |
| OCR pages processed | 32 个最终页面；另有 P1/P2 的 9 个 300 DPI 对照页面，共 41 页 |
| PNG/temp images created | 41 个临时 PNG，均已清理；无持久化图片 |
| OCR runtime seconds | 最终 200 DPI 约 115.683 秒；含对照约 149.047 秒 |
| OCR Evidence rows | 8 个最终 item-level assembled records；未写入正式 Runtime Artifact |
| Page/global truncation | 0 / 0；每页均未超过 4,000 chars，全局均未超过 20,000 chars |
| Source PDF modifications | 0；8 个 PDF 的 size/mtime 均与 Full Inventory 一致 |

## 8. Text Quality Signals

OCR Probe 仍应保留：

```text
replacement_char_count
private_use_char_count
control_char_count
printable_char_ratio
evidence_char_count
```

本次 routing calibration 另外计算并独立保存 `ascii_letter_count`、`cjk_char_count`、
`digit_count`、`whitespace_count`、`whitespace_ratio` 和 `suspicious_char_rate` 等字段；
完整字段及 Unicode 定义见 `reports/phase2/evidence_v03_routing_calibration_report.md`。

本次在既有 767-item Evidence 上完成独立 Quality Signals 计算和有限 threshold enumeration。
Quality Signals 属于 derived diagnostic data，不写回 `calibration_evidence.jsonl`，也不
修改 Gate 2B canonical Runtime。

结果表明，当前 20-item reviewed set 上没有简单规则能够同时满足：

```text
garbled recall = 100%
AND
600 Main triggered rate <= 15%
```

最优单 signal 为 `printable_char_ratio <= 0.9258285113098369`，可覆盖 4/4 garbled
reference，但会触发 288/600 Main（48.0%）；最优 two-signal OR 规则没有降低该路由量。
因此本次不冻结 `Automatic OCR Trigger v0.1`，也不以单一 Unicode 指标直接决定 `garbled`
或绕过人工 Review。

当前冻结为 annotation-side retry：先由 Gate 2C Annotator 检查 PyMuPDF Evidence，只有
出现 `insufficient_evidence` / `unreadable` 才触发 RapidOCR fallback。

## 9. Root Cause Refinement

现有 v0.2 Probe 已支持：

```text
primary suspected cause = text_extraction_encoding_issue
```

OCR 结果表明，固定 8-file Diagnostic Set 的问题项可以通过原始页面 OCR 恢复可读的主题
和技术上下文，但本次仍不能据此对全部 Candidate Source Corpus 做全局归因。仍需区分：

- 原始页面视觉清晰、但 text layer / extractor 的编码映射损坏；
- 原始页面本身低清、扫描模糊或版面变形；
- OCR engine 能力不足。

因此本次不把问题根因统一改判为 `visual_quality_issue` 或 `ocr_engine_limitation`；仅将
RapidOCR fallback 标记为固定诊断集上的有效路径。

## 10. OCR Fallback Decision

当前决策为：

```text
RapidOCR CPU Runtime: Available
Evidence v0.3 OCR Probe: Passed (Problem 4/4, Control 4/4)
Evidence v0.3 Fallback Strategy: Frozen
Selected render DPI: 200
Automatic OCR Routing Trigger: NOT FROZEN
Routing contract: annotation-side retry
Gate 2B: HOLD
Gate 2C: NOT AUTHORIZED
Full 767-item Evidence v0.3 Runtime: NOT AUTHORIZED
```

`pdftotext -layout` 根据 Evidence v0.2 结果保持 `diagnostic-only`，不进入 Evidence
v0.3 fallback。Full 767-item Evidence v0.3 Runtime 仍需单独授权。

## 11. Evidence v0.3 Frozen Fallback Strategy

当前冻结的 fallback contract 为 annotation-side retry，路由时机不是 pre-annotation
automatic trigger：

```text
Stage 1: Primary PyMuPDF Evidence
Stage 2: Gate 2C Annotator
Stage 3: RapidOCR retry for annotator-marked insufficient_evidence / unreadable Evidence
Stage 4: Re-annotation + final Evidence + provenance + review queue
```

RapidOCR fallback 的冻结参数为：

- 原始 PDF 页面由 PyMuPDF 直接 render；
- `render_dpi = 200`；
- RapidOCR `3.9.2` + ONNX Runtime `1.23.2`；
- `CPUExecutionProvider`；
- `ocr_languages = ch+en`；
- 每页最多 4,000 Unicode chars，全局最多 20,000 chars；
- 保留 `<<<PAGE:n>>>` delimiter，并按 bbox top-to-bottom、left-to-right 排序；
- 仅对 Evidence 不足或人工复核路由的页面执行，不对所有 Main Sample、Audit Pool 或
  Candidate Source Corpus 做全量 OCR。

当前没有可靠 automatic encoding-risk classifier，因此不冻结 `Automatic OCR Trigger v0.1`。
Quality Signals 只作为 diagnostic data；`insufficient_evidence` / `unreadable` 的
annotation-side retry 是当前正式 routing contract。只有更大、已人工标注的 calibration set
证明质量信号可稳定区分后，才考虑重新评估 automatic trigger。

`text_absent` Audit Pool 仍单独处理，不因本次获得 OCR 能力就自动 OCR 全部 60 条。

## 12. Proposed Schema Changes

未来 v0.3 Evidence Record 建议增加：

| Field | Purpose |
| --- | --- |
| `primary_extractor` | 记录 PyMuPDF primary path |
| `primary_evidence_status` | 记录 primary 结果 |
| `quality_signal_revision` | 标识质量信号版本 |
| `quality_signals` | 保存 Unicode 和字符统计 |
| `fallback_required` | 是否触发 fallback |
| `fallback_reason` | `encoding_unreadable`、`insufficient_text`、`extraction_failure` 或 `manual_review` |
| `fallback_extractor` | 记录 `rapidocr` |
| `fallback_status` | 记录 OCR fallback 结果 |
| `final_evidence_source` | `pymupdf` 或 `ocr` |
| `final_evidence_revision` | 记录最终 Evidence Contract 版本 |
| `ocr_engine` | OCR engine 名称 |
| `ocr_engine_version` | OCR engine 版本 |
| `ocr_languages` | 记录 `ch+en` |
| `render_dpi` | 页面渲染 DPI |
| `ocr_runtime_seconds` | 单 item OCR 成本 |

历史 v0.1/v0.2 Artifact 不修改，不回写这些字段。

## 13. Dependency Decision and Integration Impact

本次已完成最小中文 OCR dependency 的环境决策和验证：

1. 在远程项目 `.venv` 中安装 `rapidocr==3.9.2` 和 `onnxruntime==1.23.2`；
2. 通过独立懒加载适配器 `src/migb/phase2/ocr.py` 使用该可选依赖；
3. `pyproject.toml` 通过 `[project.optional-dependencies].ocr` 声明依赖，未将 RapidOCR
   变为 inventory、sampling 或现有 PyMuPDF Evidence 的 mandatory dependency；
4. 当前不安装 Tesseract、PaddlePaddle 或 GPU OCR stack。

该适配器只在显式请求 OCR 时导入 RapidOCR/ONNX Runtime；未安装 `[ocr]` extra 时，其他
既有路径仍可继续工作。模型文件位于远程虚拟环境的 package 目录，不进入 Source Corpus、
历史 Runtime Artifact 或 Git。

## 14. Gate 2B Status and Next Boundary

本次 OCR routing signal calibration 已完成，但仍保持以下边界：

- 不授权 Full Evidence v0.3 Runtime；
- 不重跑 767 条；
- 不执行 LLM Taxonomy Annotation；
- 不执行 Source Selection；
- 不关闭 Gate 2B。

本次选择的是 Case B：`annotation-side retry routing`。因此下一步必须先取得 Project
Owner / Gate Decision，确认是否接受 PyMuPDF primary Evidence 加上 Gate 2C
`insufficient_evidence` / `unreadable` retry contract；在该决策之前不得自动进入 Gate 2C。

下一步只有在单独授权后，才可在同一 767-item Sample 上执行 Evidence v0.3 Implementation
和 paired Gate 2B Review。Gate threshold 仍为：

```text
sufficient >= 18 / 20
insufficient <= 1 / 20
```

当前下一任务：

```text
Gate 2B Routing Contract Gate Decision
```
