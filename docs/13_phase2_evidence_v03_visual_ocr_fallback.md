# Phase 2 Evidence v0.3 Visual/OCR Fallback

Project: Mechanical Industry General Benchmark
Document: Phase 2 Evidence v0.3 Visual/OCR Fallback
Version: 0.1
Status: Reviewed - Contract Frozen
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Current Task: Gate 2C 20-item Annotation Dry-run Review
Evidence Contract: `evidence-v0.3-adaptive-v0.1`

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
修改 Gate 2B canonical Runtime。该 Runtime 保持 immutable；本次没有生成新的 767-item
Evidence v0.3 Runtime。

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

当前正式冻结为 annotation-side retry：先由 Gate 2C 的两个独立 Annotator 检查 PyMuPDF
Evidence，只有出现 Evidence 不足信号时才触发 RapidOCR fallback。具体的
`evidence_usability`、A/B 重跑和最终 Evidence 规则见第 11 节及
`docs/14_phase2_gate2c_taxonomy_annotation_design.md`。

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
Automatic pre-annotation OCR: REJECTED
Annotation-side OCR retry: ACCEPTED
Evidence Contract: evidence-v0.3-adaptive-v0.1
Gate 2B: PASSED
Gate 2C-A: DESIGN FROZEN; AWAITING REVIEW
Gate 2C-B: DRY-RUN AWAITING AUTHORIZATION
Full 767-item Evidence v0.3 Precomputation: CANCELLED / NOT REQUIRED
```

`pdftotext -layout` 根据 Evidence v0.2 结果保持 `diagnostic-only`，不进入 Evidence
v0.3 fallback。Gate 2B 原始 Runtime Artifact 不修改；Full 767-item Evidence v0.3
Precomputation 因采用 annotation-side retry 而取消，不作为进入 Gate 2C 的前置步骤。

## 11. Evidence v0.3 Frozen Adaptive Contract

当前冻结的 Evidence Contract 为 `evidence-v0.3-adaptive-v0.1`。它不是
pre-annotation automatic OCR trigger，而是由 Annotation output 驱动的 adaptive fallback：

```text
Stage 1  PyMuPDF primary Evidence
Stage 2  Independent Taxonomy Annotation A/B
Stage 3  Evidence insufficiency detection
Stage 4  Conditional RapidOCR fallback
Stage 5  Final Evidence regeneration
Stage 6  Restart Annotation A/B for that item
Stage 7  Agreement / Conflict processing
```

Gate 2C 的 A/B 首轮都使用同一份 Primary Evidence，并且彼此不可见。若任一独立
Annotator 触发 Evidence retry，则两条首轮结果只保留 audit provenance，不参与最终的
agreement、conflict 或 taxonomy metrics。RapidOCR fallback 完成后，必须生成同一份
`final_evidence_revision`，再使用相同的 final Evidence、Taxonomy revision、annotation
prompt revision 和 schema revision 重跑 A/B；A/B 仍然相互独立。

### 11.1 Annotation-side Evidence Usability

在已有 Annotation Schema 中增加独立字段：

```text
evidence_usability:
  usable
  partially_usable
  unreadable
  insufficient
```

`evidence_usability` 与 `taxonomy_fit` 是两个不同维度，前者不能替代后者。若任意一个
独立 Annotator 返回 `evidence_usability` 为 `unreadable` 或 `insufficient`，则：

```text
requires_evidence_retry = true
```

若 `taxonomy_fit = insufficient_evidence`，同样设置
`requires_evidence_retry = true`。`partially_usable` 不单独触发 OCR；如果 Annotator
仍能确定 `primary_domain` 且 `confidence != low`，可以继续进入 Agreement Logic。
`confidence = low` 继续进入 Review Queue，但不单独触发 OCR；OCR 只解决 Evidence
质量问题，不解决分类不确定性。

### 11.2 Same-final-Evidence Guarantee

如果 A 或 B 任意一方触发 retry：

1. 丢弃 `Annotation A1`、`Annotation B1` 的最终判定资格，只保留其审计 provenance；
2. 对该 Item 最多执行一次 RapidOCR fallback；
3. 生成 `final_evidence_revision` 后重新运行 A/B；
4. `Annotation A2`、`Annotation B2` 必须使用相同的 OCR Final Evidence、Taxonomy
   revision、annotation prompt revision 和 schema revision；
5. 只有 A2/B2 进入 Agreement / Conflict processing。

如果 RapidOCR 后仍为 `unreadable` 或 `insufficient`，该 Item 标记为 `deferred` 并进入
Review Queue，不得无限 retry，也不得自动标记为 `sufficient`。因此：

```text
max_evidence_retry_count = 1
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

未来 v0.3 Evidence Record 和 annotation routing record 建议增加以下字段。最后两项是
Annotation-side 字段，不是 PyMuPDF 或 RapidOCR extractor 的原始输出：

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
| `final_evidence_revision` | 记录最终 Evidence Contract 版本；当前为 `evidence-v0.3-adaptive-v0.1` |
| `ocr_engine` | OCR engine 名称 |
| `ocr_engine_version` | OCR engine 版本 |
| `ocr_languages` | 记录 `ch+en` |
| `render_dpi` | 页面渲染 DPI |
| `ocr_runtime_seconds` | 单 item OCR 成本 |
| `evidence_usability` | Annotator 对 Evidence 可用性的判断：`usable` / `partially_usable` / `unreadable` / `insufficient` |
| `requires_evidence_retry` | 基于任一 Annotator 的 Evidence 不足输出得到的 routing flag |

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

## 14. Gate 2B Closeout and Next Boundary

本次 OCR routing signal calibration 和 Owner Gate Decision 已完成。Gate 2B Closeout 的
最终依据为：

| Check | Result |
| --- | --- |
| Sampling / Artifact Pipeline | PASS |
| PyMuPDF primary Evidence | 16 / 20 sufficient |
| Validated RapidOCR fallback | 4 / 4 Problem items sufficient |
| Control regression | 4 / 4 sufficient |
| RapidOCR | 3.9.2 |
| ONNX Runtime | 1.23.2 |
| Execution Provider | `CPUExecutionProvider` |
| Default OCR render DPI | 200 |
| Reviewed Main items with a primary or validated fallback Evidence path | 20 / 20 |

因此：

```text
Evidence Contract: evidence-v0.3-adaptive-v0.1
Gate 2B: PASSED
```

Gate 2B 原始 Runtime Artifact 必须保持 immutable。当前仍保持以下边界：

- 不执行 Full 767-item Evidence v0.3 Precomputation；
- 不对全部 767 条预先运行 OCR；
- 不执行 LLM Taxonomy Annotation；
- 不执行 Source Selection；
- 不执行 MinerU 或大规模 OCR；
- 不重新解析全部 PDF；
- 不修改 Sampling。

Owner 已正式决定：

```text
Annotation-side Retry: ACCEPTED
Automatic pre-annotation OCR trigger: REJECTED
```

`Automatic pre-annotation OCR trigger` 在技术上可以达到当前 4/4 garbled recall，但最佳
候选会触发 288 / 600 Main（48.0%），作为 fallback 路径过宽，因此不冻结为生产规则。
这表示 Gate 2C-A 已完成设计冻结，但 Gate 2C-B 仍需 Review 和单独授权，不表示可以直接执行
20-item dry-run 或 600 条 Annotation。

Gate 2C-A 的执行设计已完成；完成 Review 并获得 Gate 2C-B 单独授权后，才可进行复用原
Gate 2B 20-item Main Evidence Review Set 的 dry-run；在 dry-run 通过前，不执行完整
600-item 双模型 Annotation。具体执行骨架见
`docs/14_phase2_gate2c_taxonomy_annotation_design.md`。

```text
Gate 2C-A: DESIGN FROZEN; AWAITING REVIEW
Gate 2C-B: DRY-RUN AWAITING AUTHORIZATION
Full 767-item Evidence v0.3 Precomputation: CANCELLED / NOT REQUIRED
```

当前下一任务：

```text
Review Gate 2C-A annotator configuration, prompt, schema, provider adapters and dry-run protocol,
then authorize the 20-item dual-annotator dry-run
```
