# Evidence v0.3 Visual/OCR Diagnostic Report

Project: Mechanical Industry General Benchmark
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Milestone: Source Corpus Calibration v0.1
Report Status: Blocked - OCR Runtime Dependency Missing
Gate 2B Diagnostic Status: HOLD
Related Design: `docs/13_phase2_evidence_v03_visual_ocr_fallback.md`

## 1. Environment

本次只读检查使用既有远程环境：

```text
SSH alias: migb
hostname: xuelangyun
Python runtime: /data/suzhe/Machinery-Industry-Benchmark/.venv/bin/python
Source Root: /mnt/data_nfs/dataset/original/cmes/journal
```

历史 Gate 2B Runtime Artifact 和 4 个 v0.2 diagnostic inputs 均保持 immutable。本次未
读取或修改 Source PDF 内容以外的任何持久化 Artifact，也未创建临时图片。

## 2. OCR Engine Availability

### Tesseract

| Check | Result |
| --- | --- |
| `command -v tesseract` | unavailable；`tesseract: command not found` |
| `tesseract --version` | not available |
| `tesseract --list-langs` | not available |
| `chi_sim` | unavailable；Language Gate not passed |
| `eng` | unavailable；Language Gate not passed |

### Alternative Python Engines

| Module | Result |
| --- | --- |
| `paddleocr` | unavailable；`ModuleNotFoundError` |
| `rapidocr_onnxruntime` | unavailable；`ModuleNotFoundError` |
| `rapidocr` | unavailable；`ModuleNotFoundError` |

结论：

```text
OCR Runtime Dependency Missing
Chinese OCR unavailable
```

本次没有执行 `sudo apt install`、`apt install`、`conda install` 或 `pip install`。

## 3. Problem / Control Set

Diagnostic Set 固定为 Evidence v0.2 已使用的 4 个 Problem 和 4 个 Control；所有
`calibration_item_id`、`file_instance_id` 和 `relative_path` 均保持不变。

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

## 4. Rendering Strategy and DPI Comparison

计划从原始 PDF 直接用 PyMuPDF render，并复用 Evidence v0.2 页面集合：

```text
first 3 + floor((N - 1) * 0.50) + floor((N - 1) * 0.75)
```

计划比较 200 DPI 和 300 DPI。但由于 Tesseract、中文语言包和其他 OCR engine 均不可用，
本次按 Dependency Gate 停止：

| Render DPI | Result |
| ---: | --- |
| 200 | not run；OCR Runtime unavailable |
| 300 | not run；OCR Runtime unavailable |

因此本次没有生成 PNG、没有进行视觉清晰度判断，也不能区分“页面本身质量问题”和“OCR
engine limitation”。

## 5. OCR Configuration

首选候选配置仍为：

```python
page.get_textpage_ocr(
    language="chi_sim+eng",
    dpi=300,
    full=True,
)
```

如果 API 不可用，才考虑 PyMuPDF render page 后调用 Tesseract CLI。未来有效 Probe 必须
同时记录：

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

本次没有选择或执行 OCR engine。

## 6. Paired Results

### 6.1 Problem Set

以下 A/B/C 结果来自已完成的 Evidence v0.2 diagnostic；D 因依赖缺失为 `not tested`。

| Item | A: v0.1 | B: PyMuPDF body probe | C: pdftotext body probe | D: OCR fallback |
| --- | --- | --- | --- | --- |
| P1 | insufficient | insufficient | insufficient | not tested |
| P2 | borderline | borderline | borderline | not tested |
| P3 | insufficient | insufficient | insufficient | not tested |
| P4 | insufficient | insufficient | insufficient | not tested |

Problem Set OCR sufficient rate：`not available`。没有执行 OCR，不能报告为 0/4。

### 6.2 Control Set

| Control | A: v0.1 | B: PyMuPDF body probe | C: pdftotext body probe | D: OCR fallback |
| --- | --- | --- | --- | --- |
| C1 | sufficient | sufficient | sufficient | not tested |
| C2 | sufficient | sufficient | sufficient | not tested |
| C3 | sufficient | sufficient | sufficient | not tested |
| C4 | sufficient | sufficient | sufficient | not tested |

Control OCR regression：`not tested`。没有依据判断 OCR 是否会降低现有可读性。

## 7. Runtime Cost

| Metric | Result |
| --- | --- |
| Problem pages rendered | 0 |
| Control pages rendered | 0 |
| OCR pages processed | 0 |
| OCR Evidence records | 0 |
| OCR runtime | not measured |
| temporary PNG files | 0 |
| Source PDF writes | 0 |

不能在没有实际 engine 的情况下估算 OCR runtime cost。后续应以每页和每 Item 的实际
`ocr_runtime_seconds` 记录成本。

## 8. Text Quality Signal Observations

本次没有新增 OCR 文本，因此没有新的 OCR Unicode metrics。Evidence v0.2 已有观察仍然
有效：字符可打印比例上升并不等价于语义可读性；不能用单一 `private_use`、`control` 或
`printable` 指标自动清除 `garbled`。

本次不冻结 automatic OCR trigger threshold，也不创建编码风险自动分类器。

## 9. Root Cause Refinement

当前最强证据仍支持：

```text
text_extraction_encoding_issue
```

但由于没有完成原始页面 render + Chinese OCR paired comparison，目前不能进一步确认：

- 页面视觉清晰但 text layer 编码损坏；
- 页面本身低清、扫描模糊或变形；
- OCR engine 对该类页面能力不足。

所以本次不把 P1–P4 改判为 visual quality issue 或 OCR engine limitation。

## 10. OCR Fallback Decision

本次没有可执行的中文 OCR Runtime，故不满足：

```text
Problem Set >= 3 / 4 sufficient
Control Set >= 3 / 4 sufficient
```

OCR fallback 的结论为：

```text
OCR Runtime Dependency Missing
Evidence v0.3 strategy: not frozen
```

`pdftotext -layout` 继续保持 `diagnostic-only`，不进入 Evidence v0.3 Production Fallback。

## 11. Evidence v0.3 Proposed Strategy

在依赖具备并通过 `chi_sim + eng` Language Gate 后，候选流程为：

```text
Stage 1: PyMuPDF primary Evidence
Stage 2: text quality assessment
Stage 3: conditional OCR retry for unreadable / insufficient Evidence
Stage 4: final Evidence and provenance review
```

OCR 只能作为 fallback，不对所有 600、767 或 60,454 个文件执行全量 OCR。当前无法可靠
冻结 automatic encoding-risk routing，初始应使用 `insufficient_evidence` / manual review
驱动的 conditional retry。

## 12. Evidence v0.3 Schema Changes

建议增加：

```text
primary_extractor
primary_evidence_status
quality_signal_revision
quality_signals
fallback_required
fallback_reason
fallback_extractor
fallback_status
final_evidence_source
final_evidence_revision
ocr_engine
ocr_engine_version
ocr_languages
render_dpi
ocr_runtime_seconds
```

`fallback_reason` 先使用最小 controlled vocabulary：

```text
encoding_unreadable
insufficient_text
extraction_failure
manual_review
```

历史 v0.1/v0.2 Artifact 不修改。

## 13. Dependency Options and Integration Impact

需要项目 Owner / 环境管理员在下一步决定并提供以下之一：

1. Remote Linux Server 或受控容器中的 Tesseract binary，以及 `chi_sim`、`eng` traineddata；
   影响包括安装/镜像依赖声明、Language Gate、版本和 provenance 记录。
2. 已包含中文 OCR 的隔离 Runtime；影响包括运行环境声明、远程复核和 OCR 输出 provenance，
   不把大型 OCR 框架直接写入当前 Python package。

本次不选择具体方案，不安装依赖，不假设 CUDA/GPU 可用。

## 14. Gate 2B Status

```text
Full 767 Evidence v0.3 rerun: NOT AUTHORIZED
Gate 2B: HOLD
Gate 2C: NOT AUTHORIZED
```

只有在 OCR Dependency Decision 完成、有效 Chinese OCR Probe 达标后，才可考虑复用同一
767-item Sample 进行 Evidence v0.3 Implementation 和 paired Gate 2B Review。Gate threshold
保持：

```text
sufficient >= 18 / 20
insufficient <= 1 / 20
```
