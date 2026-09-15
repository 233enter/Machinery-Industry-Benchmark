# Evidence v0.3 OCR Routing Signal Calibration Report

Project: Mechanical Industry General Benchmark
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Milestone: Source Corpus Calibration v0.1
Report Status: Completed - Annotation-side Retry Contract Frozen
Gate 2B Diagnostic Status: HOLD
Full 767-item Evidence v0.3 Runtime: NOT AUTHORIZED
Trigger Revision: evidence-v0.3-routing-contract-v0.1

## 1. Purpose

本报告记录在既有 Gate 2B 767-item Runtime Artifact 上进行的 OCR routing signal
calibration。目标是判断是否存在足够简单的 deterministic quality signal，可以在不把大量
正常 Evidence 送入 OCR 的情况下，覆盖已知的 garbled Evidence。

本次只完成 signal calculation、有限 threshold enumeration 和 routing contract decision。
没有重新抽取 PDF，没有运行 OCR，没有执行 Taxonomy Annotation、Source Selection、MinerU
或 Gate 2C。

## 2. Input Artifacts

只读取以下既有 canonical Artifact：

~~~
/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565/calibration_sample.parquet
/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565/calibration_evidence.jsonl
~~~

| Artifact | Rows | Size (bytes) | SHA-256 |
| --- | ---: | ---: | --- |
| calibration_sample.parquet | 767 | 217918 | f3d2fbd71c9c66ad3000b470af3116974de62a0ff100c006cac10f4cfd4bd38e |
| calibration_evidence.jsonl | 767 | 9011148 | bc1d25f55651a5a9e7a8c854d53345d7c799bc2a824231bbfd2647cde41ca5cc |

Derived diagnostic Artifact：

~~~
/data/suzhe/migb/phase2/diagnostics/evidence_v03_routing_calibration/quality_signals.parquet
~~~

该 Artifact 有 767 行、大小 157612 bytes，SHA-256 为
730bb935ec32c243df3ef97978883ec0200dcb3d05f12d6eb62cd80198e1cc3b。其中 760 行的
evidence_text 为字符串并完成 signal calculation，7 条 source_quality_exception 为
not_applicable，signal 字段保持 null。

Quality Signals 没有写回 calibration_evidence.jsonl，也没有写入 canonical Run Directory。
输入 Artifact 在校准前后 checksum、size 和 row count 均保持不变。

## 3. Reviewed Labels

使用既有 20-item Main Evidence Review Set 的人工标签，没有重新打分：

| Reference | Definition | Count |
| --- | --- | ---: |
| OCR_REQUIRED_REFERENCE | quality labels contains garbled | 4 |
| OCR_NOT_REQUIRED_REFERENCE | sufficient and no garbled label | 16 |
| Total reviewed references | 既有 Main Review Set | 20 |

4 条 OCR_REQUIRED_REFERENCE 中，3 条原始 sufficiency 为 insufficient，1 条为
borderline。本次没有使用 text_absent Audit Pool 校准 encoding-risk trigger。

Review label snapshot 保存在：

~~~
configs/phase2/evidence_v03_routing_calibration.yaml
~~~

## 4. Signal Definitions

所有 signal 都对保存于 Evidence Artifact 的 Unicode 字符串进行确定性统计；total_chars
是 Python Unicode code-point 长度，包含既有 <<<PAGE:n>>> delimiter。空字符串的 rate
和 ratio 定义为 0.0。没有加入需要语言模型判断的指标。

| Signal | Definition |
| --- | --- |
| total_chars | Stored Evidence 的 Unicode code-point 数量 |
| replacement_char_count | U+FFFD 数量 |
| private_use_char_count | U+E000–U+F8FF、U+F0000–U+FFFFD、U+100000–U+10FFFD 数量 |
| control_char_count | Unicode category Cc 数量，排除 \\t、\\n、\\r |
| printable_char_count | Python str.isprintable() 为 true 的字符数量 |
| ascii_letter_count | ASCII A–Z / a–z 数量 |
| cjk_char_count | CJK Unified Ideographs、Extension A、Compatibility Ideographs 及扩展区字符数量 |
| digit_count | Unicode category Nd 数量 |
| whitespace_count | Python str.isspace() 为 true 的字符数量 |
| suspicious_char_count | replacement + private-use + unexpected Cc control，各类不重叠 |
| *_rate / *_ratio | 对应 count 除以 total_chars |

实际输出还保留了 Evidence identity、pool、status、canonical character count、signal
revision 和可用性字段，便于诊断 Artifact 追溯。

## 5. Signal Distribution Summary

以下统计仅针对 20 条既有 Main Review Set，按 garbled 与 non-garbled reference 分组：

| Signal | Garbled min | Garbled median | Garbled max | Non-garbled min | Non-garbled median | Non-garbled max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| replacement_char_rate | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| private_use_char_rate | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.005147 |
| control_char_rate | 0.000000 | 0.067573 | 0.090440 | 0.000000 | 0.000000 | 0.000000 |
| printable_char_ratio | 0.851579 | 0.877404 | 0.925829 | 0.850467 | 0.924016 | 0.957602 |
| suspicious_char_rate | 0.000000 | 0.067573 | 0.090440 | 0.000000 | 0.000000 | 0.005147 |

关键观察：1 条 garbled reference 在 replacement_char_rate、private_use_char_rate、
control_char_rate 和 suspicious_char_rate 上均为 0；它只能通过较宽松的
printable_char_ratio 阈值被覆盖。该结果不支持用单一 Unicode count signal 可靠判定
garbled。

## 6. Candidate Trigger Evaluation

Threshold search 仅使用 20 条 reviewed reference 中的 observed signal values，采用有限、
确定性的 one-sided threshold。Two-signal 只测试不同 signal 的 A OR B 组合。不使用
logistic regression、random forest、SVM、neural classifier，也不使用 filename、
parent_group、publication year 或人工 Problem ID。
本次共评估 533 个不同 signal 的 two-signal OR candidate。

下表对每个 signal 选择其在当前 reference set 上达到 100% garbled recall 时路由量最低的
候选；count signal 的 >= 0 是当前数据下唯一能覆盖全部 4 条的退化阈值。

| Trigger | Garbled Recall | Reviewed False Positives | Main Triggered Count | Main Triggered Rate |
| --- | ---: | ---: | ---: | ---: |
| replacement_char_rate >= 0 | 100% (4/4) | 16 | 600 | 100.0% |
| private_use_char_rate >= 0 | 100% (4/4) | 16 | 600 | 100.0% |
| control_char_rate >= 0 | 100% (4/4) | 16 | 600 | 100.0% |
| printable_char_ratio <= 0.9258285113098369 | 100% (4/4) | 9 | 288 | 48.0% |
| suspicious_char_rate >= 0 | 100% (4/4) | 16 | 600 | 100.0% |
| control_char_rate >= 0.065084022405974926 OR printable_char_ratio <= 0.9258285113098369 | 100% (4/4) | 9 | 288 | 48.0% |

### 6.1 Best Single Signal

~~~
Best Single Signal:
printable_char_ratio <= 0.9258285113098369
Garbled Recall: 100% (4/4)
Reviewed False Positives: 9/16
Main Triggered: 288/600 = 48.0%
~~~

它超过 preferred triggered rate <= 15%，也超过更优目标 <= 10%，因此不冻结为
automatic trigger。

### 6.2 Best Two-signal OR Rule

当前有限枚举中的最优双信号 OR 结果与最优单信号并列：

~~~
control_char_rate >= 0.065084022405974926
OR printable_char_ratio <= 0.9258285113098369
~~~

该规则仍为 100% garbled recall、9 个 reviewed false positives、288/600 Main triggered，
没有降低路由量，因此同样不满足 automatic trigger 的工程范围要求。

## 7. Routing Decision

### Selected Routing Strategy

采用 annotation-side retry routing（Case B）：

~~~
PyMuPDF primary Evidence
    ↓
Gate 2C Annotator
    ↓
insufficient_evidence / unreadable
    ↓
RapidOCR fallback
    ↓
re-annotation + provenance + review queue
~~~

当前不冻结 Automatic OCR Trigger v0.1，因为没有简单规则同时满足：

~~~
Garbled Recall = 100%
AND
Main Triggered Rate <= 15%
~~~

这不是失败，而是对当前 20-item calibration set 采用更诚实的 adaptive routing contract。
后续如取得更大、已人工标注的 extraction-quality calibration set，可另行评估是否需要
重新校准；不得把本次候选阈值直接视为永久生产规则。

## 8. Evidence v0.3 Final Routing Contract

当前冻结的 Evidence v0.3 fallback contract 为：

1. Primary extractor 使用 PyMuPDF，保持既有 Evidence page selection 和 provenance。
2. 不执行 pre-annotation automatic OCR trigger；quality signals 仅作为 diagnostic data。
3. Gate 2C Annotator 首次检查 Primary Evidence。
4. 只有 Annotator 输出 insufficient_evidence 或 unreadable 时，才触发 RapidOCR fallback。
5. RapidOCR 使用已验证的 3.9.2，ONNX Runtime 1.23.2、CPUExecutionProvider、
   ch+en、200 DPI，以及既有 page/global cap 和 page delimiter contract。
6. OCR 后重新 annotation，并保存 fallback reason、engine/version、render DPI、page
   indices、raw/stored chars、runtime 和最终 Evidence source。
7. OCR 仍不充分的记录进入 review queue，不得自动标记为 sufficient。

## 9. Pool-specific Handling

### text_absent

当前 60 条 text_absent Audit Pool 不进入本 encoding-risk trigger。它们保留独立的
text_absent routing policy，不能因为本次 RapidOCR 能力可用就自动纳入 OCR。

### source_quality_exception

7 条 source_quality_exception 保持 not_applicable，不进入本 trigger，也不执行本次
quality signal 的文本计算。

## 10. Full Runtime Authorization Decision

~~~
Automatic OCR Trigger Frozen: NO
Selected Strategy: annotation-side retry
Full 767-item Evidence v0.3 Runtime: NOT AUTHORIZED
Gate 2B: HOLD
Gate 2C: NOT AUTHORIZED
~~~

由于采用 Case B，不能在本次任务中自动进入 Gate 2C 或执行完整 767-item Runtime。下一步
需要 Project Owner / Gate Decision 明确是否接受：

~~~
PyMuPDF primary Evidence
+ validated RapidOCR fallback capability
+ Gate 2C insufficient-evidence / unreadable retry contract
~~~

在该决策完成前，不运行完整 767-item OCR Evidence，不修改 Sampling，不执行 Taxonomy
Annotation、Source Selection 或 Benchmark Source Registry。

## 11. Reproducibility and Verification

本次校准实现位于：

~~~
src/migb/phase2/quality_signals.py
scripts/phase2_evidence_v03_routing_calibration.py
~~~

标签配置为：

~~~
configs/phase2/evidence_v03_routing_calibration.yaml
~~~

执行结果：

~~~
pytest: 68 passed
git diff --check: passed
~~~

脚本只读取 Parquet/JSONL 输入，不访问 Source PDF；Quality Signals 为独立诊断 Artifact，
不属于 Gate 2B canonical Artifact。
