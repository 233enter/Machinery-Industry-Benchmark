# Evidence v0.3 Visual/OCR Diagnostic Report

Project: Mechanical Industry General Benchmark
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Milestone: Source Corpus Calibration v0.1
Report Status: Completed - Fallback Strategy Frozen
Gate 2B Diagnostic Status: HOLD
Related Design: `docs/13_phase2_evidence_v03_visual_ocr_fallback.md`

## 1. Diagnostic Scope

本次只执行 Evidence v0.3 的固定 8-file Diagnostic Set，不重跑 767 条，不修改历史
Gate 2B Runtime Artifact，不执行 Taxonomy Annotation、Source Selection、LLM、MinerU 或
全量 OCR。

固定输入仍为：

```text
/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565
```

## 2. Runtime Environment and Dependency Gate

远程环境：

```text
SSH alias: migb
hostname: xuelangyun
Python runtime: /data/suzhe/Machinery-Industry-Benchmark/.venv/bin/python
```

在远程项目 `.venv` 中安装并验证：

| Component | Result |
| --- | --- |
| `rapidocr` | available；`3.9.2` |
| `onnxruntime` | available；`1.23.2` |
| `CPUExecutionProvider` | available；RapidOCR detection/classification/recognition sessions 均实际使用 CPU |
| `tesseract` | unavailable；本次未安装 |
| `paddleocr` | unavailable；不属于本次最小依赖 |

未使用 sudo、apt、conda 或 GPU OCR stack。`pyproject.toml` 已声明独立 `[ocr]` optional
extra；RapidOCR 不成为 inventory、sampling 或既有 PyMuPDF Evidence 的 mandatory
dependency。

### Synthetic Image Check

合成图包含：

```text
机械制造与自动化
齿轮传动磨损分析
Mechanical Engineering
123456
```

RapidOCR 识别出上述四行，Synthetic Chinese/English/Digit Check: `PASS`。

## 3. Fixed Problem / Control Set

固定复用 Evidence v0.2 已确定的 4 个 Problem 和 4 个 Control，不重新抽样，不更换
`calibration_item_id`、`file_instance_id` 或 `relative_path`。

| Item | Role | `calibration_item_id` | Relative path |
| --- | --- | --- | --- |
| P1 | problem | `67504202-11fc-51ae-8017-9ad5f4bdefe5` | `hanjie/【2020-12】Ag和Zn对Sn58Bi钎料润湿性及焊点组织的影响.pdf` |
| P2 | problem | `8ff31d50-6ffe-5e49-8890-917e51c8e936` | `jinshurechuli/【2024-10】冷轧压下率对IF钢退火热处理织构及成形性的影响.pdf` |
| P3 | problem | `791f9b84-1b42-54eb-a977-6400614f0285` | `yeyayuqidong/【2018-09】多柱塞阀配流往复式容积泵新型流量调节方法研究.pdf` |
| P4 | problem | `d2816f50-ace1-5dfd-87b0-6ab4b8df929e` | `zhongguozhuzaozhuangbeiyujishu/【2022-5】V法造型密闭式涂料烘干系统的优化设计.pdf` |
| C1 | control | `79562004-0aef-5222-afc8-b0e0bcb73cba` | `suxinggongchengxuebao/【2026-06】组合本构模型对高强钢CTB电池箱体纵梁辊弯回弹预测精度的影响.pdf` |
| C2 | control | `006ef0ba-d56b-5aab-b4d6-f45fbb3922ca` | `hanjiexuebao/【2011-12】基于SYSWELD的穿孔等离子弧焊接温度场有限元分析.pdf` |
| C3 | control | `78ba6d84-c7b6-5dca-9ff9-1838689c8bc1` | `zhuzao/【2023-03】厚大断面球墨铸铁齿轮铸件的研制.pdf` |
| C4 | control | `7d1cfa14-757d-56aa-9c0f-9b59c27405aa` | `lihuajianyan-huaxuefence/【2015-12】八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素.pdf` |

## 4. Rendering and Evidence Contract

每个 selected page 均由 PyMuPDF 从原始 PDF 直接 render 到系统临时 PNG，再交给
RapidOCR；没有对乱码 text layer 截图或 OCR。页面选择复用 Evidence v0.2：

```text
first 3 + floor((N - 1) * 0.50) + floor((N - 1) * 0.75)
```

固定 contract：

- P1、P2 比较 200 DPI 和 300 DPI；
- 其余 Item 在最终选择的 200 DPI 下运行；
- 每页最多保存 4,000 Unicode chars；
- 全局最多保存 20,000 chars；
- 保留 `<<<PAGE:n>>>` delimiter；
- RapidOCR 检测结果按 bbox top-to-bottom、left-to-right 排序；
- 记录 extractor、engine/version、languages、DPI、page indices、raw/stored chars 和 runtime。

## 5. Paired Review Results

### 5.1 Problem / Control Decision

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

Problem Set sufficient rate: `4 / 4`。

Control Set sufficient rate: `4 / 4`。

最低条件为 Problem `>= 3 / 4` 且 Control `>= 3 / 4`，本次满足。

P1–P4 的 OCR Evidence 均能稳定提供标题、摘要或正文中的机械/工程主题和技术上下文；
个别图表、公式或英文片段仍需人工复核，不因 OCR 可读就绕过 Ground Truth 或质量审查。

### 5.2 DPI Comparison

| Item | 200 DPI runtime (s) | 300 DPI runtime (s) | Quality conclusion |
| --- | ---: | ---: | --- |
| P1 | 16.389 | 17.847 | 两者均 sufficient；300 DPI 无明显额外收益 |
| P2 | 14.974 | 15.517 | 两者均 sufficient；300 DPI 无明显额外收益 |

因此选择 `200 DPI`：在固定对照中质量相近，运行成本更低。300 DPI 只作为本次 P1/P2
诊断对照，不进入当前冻结的默认 fallback 参数。

## 6. Runtime Cost and Provenance

最终 200 DPI 的 8 个 item 共处理 32 个页面；P1/P2 另处理 9 个 300 DPI 对照页面，
合计 41 个 OCR 页面。

| Metric | Result |
| --- | --- |
| Final item-level Evidence records | 8；仅保存在诊断过程，未写入正式 Runtime Artifact |
| Final 200 DPI OCR runtime | 约 115.683 秒 |
| Including 300 DPI comparison | 约 149.047 秒 |
| Per-page truncation | 0 |
| Global truncation | 0 |
| Temporary PNG | 41 个临时文件，均已清理；无持久化图片 |
| Source PDF writes | 0 |

最终 200 DPI item-level 统计：

| Item | `selected_page_indices` | `ocr_raw_char_count` | `ocr_stored_char_count` | `ocr_runtime_seconds` |
| --- | --- | ---: | ---: | ---: |
| P1 | `[0,1,2,4,6]` | 6687 | 6756 | 16.389 |
| P2 | `[0,1,2,3]` | 7846 | 7901 | 14.974 |
| P3 | `[0,1,2,3]` | 7063 | 7118 | 18.340 |
| P4 | `[0,1,2]` | 3538 | 3579 | 9.699 |
| C1 | `[0,1,2,4,6]` | 10044 | 10113 | 18.559 |
| C2 | `[0,1,2,3]` | 7108 | 7163 | 14.827 |
| C3 | `[0,1,2,3]` | 4439 | 4494 | 11.631 |
| C4 | `[0,1,2]` | 6029 | 6070 | 11.264 |

每条记录使用以下 provenance：

```text
extractor: pymupdf_render_to_png+rapidocr
ocr_engine: rapidocr
ocr_engine_version: 3.9.2
ocr_languages: ch+en
render_dpi: 200
selected_page_indices: item-specific frozen selector
ocr_raw_char_count: recorded
ocr_stored_char_count: recorded
ocr_runtime_seconds: recorded
execution_provider: CPUExecutionProvider
onnxruntime_version: 1.23.2
```

`ocr_raw_char_count` 不包含 page delimiter；`ocr_stored_char_count` 为全局 cap 后保存的
Evidence 长度，包含组装后的 delimiter。

## 7. Safety and Immutability Checks

- 8 个 Source PDF 的 size 和 mtime 均与 Full Inventory 记录一致；
- 历史 Gate 2B Runtime Artifact 的 `calibration_sample.parquet`、
  `calibration_evidence.jsonl`、`manifest.json`、`statistics.json` checksum/size 均未变化；
- 未 rename、move、OCR 写回或 rewrite Source PDF；
- 未写入历史 Run Directory；
- 运行结束后没有保留临时 PNG。

## 8. Fallback Strategy Decision

本次冻结 Evidence v0.3 fallback strategy：

```text
Stage 1: Primary PyMuPDF text Evidence
Stage 2: Text quality assessment
Stage 3: Conditional RapidOCR retry on insufficient/unreadable Evidence
Stage 4: Final Evidence + provenance + manual review queue
```

冻结参数：

```text
RapidOCR: 3.9.2
ONNX Runtime: 1.23.2
Execution Provider: CPUExecutionProvider
OCR languages: ch+en
Render DPI: 200
Per-page cap: 4000 Unicode chars
Global cap: 20000 chars
```

OCR 仍只作为 conditional fallback，不对全部 Main Sample、Audit Pool、767 items 或
Candidate Source Corpus 做全量 OCR。`pdftotext -layout` 继续为 `diagnostic-only`，不
进入 Evidence v0.3 fallback。

本次诊断足以冻结 fallback strategy，但不代表 Full Evidence v0.3 Runtime 已获授权。

## 9. Gate 2B Status and Stop Boundary

```text
Evidence v0.3 OCR Diagnostic: PASS
Evidence v0.3 Fallback Strategy: FROZEN
Gate 2B: HOLD
Gate 2C: NOT AUTHORIZED
Full 767-item Evidence v0.3 rerun: NOT AUTHORIZED
```

下一任务为：

```text
Gate 2B Evidence v0.3 Implementation on the same 767-item Sample
```

该下一任务仍需单独授权；在此之前不执行 767-item rerun、Taxonomy Annotation、Source
Selection 或 Benchmark Source Registry。
