# Phase 2 Evidence v0.3 Visual/OCR Fallback

Project: Mechanical Industry General Benchmark
Document: Phase 2 Evidence v0.3 Visual/OCR Fallback
Version: 0.1
Status: Draft - Diagnostic Validation
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2B Evidence Contract Revision

## 1. Background

Evidence v0.2 的 8-file diagnostic 已确认：PyMuPDF 增加正文页和 `pdftotext -layout` 均未
解决 4 个 Problem Item 的主要乱码问题。下一步需要验证原始 PDF 页面是否可以通过视觉
渲染和中文 OCR 恢复可用 Evidence。

本文件是 Evidence v0.3 visual/OCR fallback 的诊断设计草案。当前远程环境没有可用的
中文 OCR Runtime，因此本次只完成 capability check，不冻结可执行的 OCR 生产实现。

## 2. Environment and OCR Engine Availability

远程环境：

```text
SSH alias: migb
hostname: xuelangyun
Python runtime: /data/suzhe/Machinery-Industry-Benchmark/.venv/bin/python
```

只读探测结果：

| Component | Result |
| --- | --- |
| `command -v tesseract` | unavailable；command not found |
| `tesseract --version` | not executable because Tesseract is unavailable |
| `tesseract --list-langs` | not executable because Tesseract is unavailable |
| Tesseract `chi_sim` | unavailable / Language Gate not passed |
| Tesseract `eng` | unavailable / Language Gate not passed |
| `paddleocr` | unavailable；Python module not installed |
| `rapidocr_onnxruntime` | unavailable；Python module not installed |
| `rapidocr` | unavailable；Python module not installed |

未执行 `sudo apt install`、`apt install`、`conda install` 或 `pip install`。当前结论为：

```text
OCR Runtime Dependency Missing
Chinese OCR unavailable
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

如果 Chinese OCR Runtime 被提供，页面必须从原始 PDF 直接使用 PyMuPDF render，不得对
乱码文本截图或做 OCR。页面集合继续复用 Evidence v0.2：

```text
first 3 pages + floor((N - 1) * 0.50) + floor((N - 1) * 0.75)
```

本次计划比较：

```text
200 DPI
300 DPI
```

由于当前没有任何可用 OCR engine，200/300 DPI render comparison 本次未执行，也没有
创建 PNG 或其他临时图片。未来每个 DPI 只对固定 8-file Diagnostic Set 的 selected pages
执行，输出只能进入 `/data/suzhe/migb/phase2/diagnostics/` 或系统 temp，不得写入 Source
Root 或历史 Runtime Artifact。

## 5. OCR Configuration

优先候选路径为 PyMuPDF/Tesseract OCR：

```python
page.get_textpage_ocr(
    language="chi_sim+eng",
    dpi=300,
    full=True,
)
```

如果该 API 在实际环境不可用，可使用“PyMuPDF render page → Tesseract CLI”的等价只读
路径。无论实现方式，OCR Evidence 必须：

- 使用原始 PDF 页面图像；
- 继续使用相同 `selected_page_indices`；
- 每页最多保存 4,000 Unicode chars；
- 全局最多保存 20,000 chars；
- 保留 `<<<PAGE:n>>>` delimiter；
- 记录 page-level raw/stored count 和 truncation；
- 不把 OCR 应用于全部 600、767 或 60,454 个文件。

本次未执行 OCR API、CLI 或任何 OCR engine。

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

当前由于 OCR 未运行，Problem Set 的 OCR sufficient rate 和 Control Regression 均为
`not tested`，不能记为 0/4。

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

本次结果：

| Metric | Result |
| --- | --- |
| OCR pages processed | 0 |
| PNG/temp images created | 0 |
| OCR runtime seconds | not measured |
| OCR Evidence rows | 0 |
| Source PDF modifications | 0；本次未打开写入路径 |

## 8. Text Quality Signals

OCR Probe 仍应保留：

```text
replacement_char_count
private_use_char_count
control_char_count
printable_char_ratio
evidence_char_count
```

这些指标只能作为观察信号。当前没有足够证据冻结 automatic OCR trigger threshold；尤其不
允许以单一 Unicode 指标直接决定 `garbled` 或绕过人工 Review。

## 9. Root Cause Refinement

现有 v0.2 Probe 已支持：

```text
primary suspected cause = text_extraction_encoding_issue
```

但在 OCR Runtime 缺失时，尚不能进一步区分：

- 原始页面视觉清晰、但 text layer / extractor 的编码映射损坏；
- 原始页面本身低清、扫描模糊或版面变形；
- OCR engine 能力不足。

因此本次不把任何问题项改判为 `visual_quality_issue` 或 `ocr_engine_limitation`。

## 10. OCR Fallback Decision

当前决策为：

```text
OCR Runtime Dependency Missing
Evidence v0.3 OCR Probe: Not Run
Evidence v0.3 Contract: Not Frozen
Gate 2B: HOLD
Gate 2C: NOT AUTHORIZED
```

`pdftotext -layout` 根据 Evidence v0.2 结果保持 `diagnostic-only`，不进入 Evidence
v0.3 Production Fallback。

## 11. Evidence v0.3 Proposed Contract

在中文 OCR Runtime 可用且通过 Language Gate 后，候选架构为：

```text
Stage 1: Primary PyMuPDF Evidence
Stage 2: Text quality assessment
Stage 3: Conditional OCR retry for unreadable / insufficient Evidence
Stage 4: Final Evidence + provenance + review queue
```

OCR 必须是 fallback，不是对所有 Main Sample、Audit Pool 或 Candidate Source Corpus 的
全量 OCR。当前没有可靠 automatic encoding-risk classifier，因此初始 trigger 应采用
`insufficient_evidence` / manual review 驱动的 conditional retry；只有更大样本证明质量
信号可稳定区分后，才考虑自动 trigger。

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
| `fallback_extractor` | 记录 OCR engine |
| `fallback_status` | 记录 OCR fallback 结果 |
| `final_evidence_source` | `pymupdf` 或 `ocr` |
| `final_evidence_revision` | 记录最终 Evidence Contract 版本 |
| `ocr_engine` | OCR engine 名称 |
| `ocr_engine_version` | OCR engine 版本 |
| `ocr_languages` | 语言包，例如 `chi_sim+eng` |
| `render_dpi` | 页面渲染 DPI |
| `ocr_runtime_seconds` | 单 item OCR 成本 |

历史 v0.1/v0.2 Artifact 不修改，不回写这些字段。

## 13. Dependency Decision and Integration Impact

当前需要项目 Owner 或环境管理员决定并提供最小中文 OCR 能力，候选方案为：

1. 在 Remote Linux Server 或受控容器中提供 Tesseract binary 以及 `chi_sim`、`eng`
   traineddata；集成影响为增加环境依赖、语言包校验和 OCR provenance 记录。
2. 提供已经包含中文 OCR 的隔离 Runtime；集成影响为增加运行镜像/环境声明和远程执行
   复核，但不将大型 OCR 框架直接写入当前 Python package。

本项目当前不选择具体方案，不安装依赖，也不估算未经环境确认的 GPU/CUDA 资源。

## 14. Gate 2B Status and Next Boundary

在完成一次有效的 Chinese OCR Probe 前：

- 不授权 Full Evidence v0.3 Runtime；
- 不重跑 767 条；
- 不执行 LLM Taxonomy Annotation；
- 不执行 Source Selection；
- 不关闭 Gate 2B。

如果 OCR Probe 后 Problem/Control 条件满足，才可进入同一 767-item Sample 的条件性
Evidence v0.3 Implementation 和 paired Gate 2B Review。Gate threshold 仍为：

```text
sufficient >= 18 / 20
insufficient <= 1 / 20
```
