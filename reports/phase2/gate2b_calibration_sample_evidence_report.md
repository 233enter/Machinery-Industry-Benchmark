# Gate 2B Calibration Sample & Evidence Report

Project: Mechanical Industry General Benchmark
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Milestone: Source Corpus Calibration v0.1
Report Status: Remote Gate 2B Runtime Completed - Awaiting Artifact Review
Gate 2B Self-check Verdict: **PASS (Candidate for Artifact Review)**

## 1. Scope and Stop Boundary

本次只执行已经冻结的 Gate 2B 范围：

Full Inventory 完整性校验 → deterministic calibration sampling → Audit Pools →
PyMuPDF lightweight Evidence extraction → Artifact validation。

本次没有执行以下工作：

- LLM annotation；
- Taxonomy classification 或 Taxonomy revision；
- Source Selection；
- Benchmark Source Registry；
- OCR、MinerU 或 Full PDF Parsing；
- Question Generation、Ground Truth construction 或 Benchmark Evaluation。

Gate 2B self-check 为 PASS，下一步仅进行 Calibration Sample 和 Evidence Artifact Review。
在 Artifact Review 完成并作出明确决定前，不启动 Taxonomy Annotation 或 Source Selection。

## 2. Run Identity

| Field | Value |
| --- | --- |
| Phase 2 Run ID | p2b-20260915T023641Z-cbde565 |
| Calibration Sample ID | cad63e5e-a9e9-55b8-8357-f2981bc87a4f |
| Remote host | xuelangyun |
| SSH alias | migb |
| Remote repository | /data/suzhe/Machinery-Industry-Benchmark |
| Git commit | cbde56528e50ba78ff98b9390465224ae3bb4e02 |
| Git dirty state | false |
| Source Root | /mnt/data_nfs/dataset/original/cmes/journal |
| MIGB_DATA_ROOT | /data/suzhe/migb |
| Full Inventory Run ID | full-20260914T075902Z-faa4565 |
| Full Inventory Schema | inventory-v0.2 |
| Phase 2 Schema | phase2-calibration-v0.1 |
| Sampling contract | phase2-sampling-v0.1 |
| Evidence revision | evidence-v0.1-gate2b |
| Config fingerprint | b90063f53eaf2703134e50056272338ede2ce7b23fd6cad233526f89d268f2b0 |
| Python | 3.10.12 |
| PyMuPDF | 1.28.2 |
| PyArrow | 21.0.0 |
| PyYAML | 6.0.3 |
| Worker count | 4 |
| Started at | 2026-09-15T02:36:43.825538Z |
| Completed at | 2026-09-15T02:38:05.787530Z |
| Artifact directory | /data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565 |

远程项目仓库在运行前后均保持 clean；Phase 2 Runtime Artifacts 写入 MIGB_DATA_ROOT，
未写入 Git repository 或 Source Corpus。

## 3. Full Inventory Input Integrity

运行前验证了 Full Inventory 的 canonical input：

| Check | Result |
| --- | --- |
| Full Inventory Run ID match | passed |
| inventory-v0.2 | passed |
| run_status = completed | passed |
| Full Inventory verdict = PASS | passed |
| files.parquet row count | 60454 |
| Canonical Artifact checksum validation | passed |
| Schema validation | passed |
| Row accounting | passed |
| Full Inventory artifact validation status | passed |

Full Inventory 的物理输入统计为 60,454 个 File Instance。Phase 2 没有重新遍历全量
Source Corpus 来重建 Inventory；Evidence 阶段只读取最终选中的 Calibration/Audit Items。

## 4. Deterministic Sampling Results

| Metric | Result |
| --- | ---: |
| Physical eligible population | 56961 |
| Duplicate-collapsed eligible population | 56686 |
| Exact duplicate physical records excluded from sampling | 275 |
| Main Sample target | 600 |
| Main Sample actual | 600 |
| Audit Pool actual total | 167 |
| Total unique selected items | 767 |
| Main/Audit overlap | 0 |
| Cross-pool overlap | 0 |
| Deterministic recomputation | passed |
| Main parent-group coverage | 20 / 20 |

Main Sample 使用已冻结的 non-semantic Eligibility：

inventory_status 为 success、pdf_open_status 为 success、page_count 大于 0，且
text_layer_status 为 text_present 或 mixed_or_uncertain。Exact duplicate collapse
只影响抽样 population 表示，不删除任何 Source PDF，也不改变 Full Inventory。

### Pool Accounting

| Pool | Target | Actual | Evidence success | Not applicable | Zero-text evidence | Truncated |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 600 | 600 | 600 | 0 | 0 | 7 |
| source_quality_exception | 7 | 7 | 0 | 7 | 0 | 0 |
| text_absent | 60 | 60 | 60 | 0 | 60 | 0 |
| mixed_text | 40 | 40 | 40 | 0 | 2 | 0 |
| filename_unmatched | 60 | 60 | 60 | 0 | 4 | 0 |
| **Total** | **767** | **767** | **760** | **7** | **66** | **7** |

Audit Pool priority、Parent Group 配额、Hamilton / Largest Remainder 分配、
POSIX relative_path 排序和 evenly-spaced selection 均按冻结配置执行。各 Pool 与 Main
Sample 在 physical File Instance 层面保持互斥。

## 5. Lightweight Evidence Results

Evidence 使用 PyMuPDF，每个选中项只读取 physical first three pages，即 page indices
0、1、2；文件少于三页时读取所有现有页面。Evidence character cap 为 12,000。
除 CRLF/CR 转换为 LF 外，没有进行文本清洗或语义处理。

| Metric | Result |
| --- | ---: |
| Evidence rows | 767 |
| Evidence success | 760 |
| Evidence partial | 0 |
| Evidence failed | 0 |
| Evidence not applicable | 7 |
| Evidence truncated | 7 |
| Zero-text evidence | 66 |
| Evidence character count minimum | 0 |
| Evidence character count median | 5398 |
| Evidence character count P10 | 1742 |
| Evidence character count P90 | 7050 |
| Evidence character count maximum | 12000 |
| Pre-extraction source mismatch | 0 |
| Post-extraction source change | 0 |

source_quality_exception Pool 的 7 条记录按设计标记为 not_applicable；其余选中项没有
Evidence extraction failure 或 source consistency failure。Evidence 只作为本次 Calibration
前的轻量证据 Artifact，不代表完成 Taxonomy Annotation 或全文语义覆盖。

## 6. Limited Evidence Previews

以下仅展示少量 Evidence preview，用于 Artifact Review。Preview 不包含 Domain Label，
也不对 parent_group 做 Domain 解释；相对路径中的目录名只是 Source Corpus 原始路径信息。
为便于审阅，编码异常片段在 Preview 中以 [encoding fragment] 标记；远程 Evidence Artifact
本身未被修改。

### Preview 1 — main

- Relative path: duanyajishu/【2022-01】2618铝合金支座等温成形锻件的粗晶问题.pdf
- Page indices: 0, 1, 2
- Status: success
- Evidence characters: 5827
- Truncated: false

Evidence preview（前 240 字符）：

> <<<PAGE:0>>> 第４７卷第１期 Ｖｏｌ４７　Ｎｏ１　ＦＯＲＧＩＮＧ＆ＳＴＡＭＰＩＮＧＴＥＣＨＮＯＬＯＧＹ ２０２２年１月　Ｊａｎ２０２２　２６１８铝合金支座等温成形锻件的粗晶问题 李宏伟 １，张子健 ２，３，徐福昌 ２，３，袁　林 ２，３

### Preview 2 — mixed_text

- Relative path: hanjiexuebao/【1987-04】B30_QTS爆炸复合板焊接接头断裂行为的研究.pdf
- Page indices: 0, 1, 2
- Status: success
- Evidence characters: 2929
- Truncated: false

Evidence preview（前 240 字符）：

> <<<PAGE:0>>> 第 卷 第4 期 1 7 年1 2 )] 焊 接 学 报 1 IA N I X U L B A O V o . N o . 4 [encoding fragment] 爆炸复合板焊接接头 断裂行为的研究，张初冬副教授 武春芝讲师 周志良助教

### Preview 3 — text_absent

- Relative path: hanjiexuebao/【2000-04】YDCrMoV CO2气保护堆焊药芯焊丝的磨粒磨损性能.pdf
- Page indices: 0, 1, 2
- Status: success
- Evidence characters: 41
- Truncated: false

Evidence preview：

> <<<PAGE:0>>>  <<<PAGE:1>>>  <<<PAGE:2>>>

该条记录保留在 text_absent Audit Pool；Evidence 成功表示页面读取流程完成，不表示已经
获得可用文本内容。

### Preview 4 — filename_unmatched

- Relative path: hanjie/振动削减铝合金焊接残余应力的细观模拟.pdf
- Page indices: 0, 1, 2
- Status: success
- Evidence characters: 4253
- Truncated: false

Evidence preview（前 240 字符）：

> <<<PAGE:0>>> ResearchPaper 等非标准文本与部分编码异常片段；原始 Evidence 未做语义修正或自动改写。该样本只用于观察 filename metadata pattern 和 Evidence 可用性。

### Preview 5 — source_quality_exception

- Relative path: jixiegongchengxuebao/【2023-13】基于QP改进模型的离心泵性能预测方法.pdf
- Page indices: none
- Status: not_applicable
- Evidence characters: 0
- Truncated: false

该条记录来自 source_quality_exception Pool，按照设计不执行页面 Evidence extraction。

## 7. Canonical Artifact Review Information

Gate 2B 只生成四个 canonical Artifact，均位于远程 Artifact directory：

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| calibration_sample.parquet | 217918 | f3d2fbd71c9c66ad3000b470af3116974de62a0ff100c006cac10f4cfd4bd38e |
| calibration_evidence.jsonl | 9011148 | bc1d25f55651a5a9e7a8c854d53345d7c799bc2a824231bbfd2647cde41ca5cc |
| manifest.json | 4457 | 9a382177a1f4b5df34615e525d2acc8fcf992c979de78b1907b45038b0f50cde |
| statistics.json | 30904 | 73b4ddb0aebb01b1fc81011f3f82f730d83682ceea92794cf79ba85598d9c6c6 |

Artifact validation summary：

- canonical artifact count: 4；
- checksum validation: passed；
- schema validation: passed；
- row accounting: passed；
- sample rows: 767；
- evidence rows: 767；
- validation status: passed。

这些大规模 Runtime Artifacts 不提交 Git；本地仓库只保留本审查报告和项目进度记录。

## 8. Gate 2B Review Status and Next Boundary

当前结论为：**Gate 2B self-check PASS，待 Artifact Review。**

通过 self-check 的依据包括：

1. Full Inventory canonical input 完整且 checksum、Schema、行数校验通过；
2. Main Sample 和 Audit Pools 达到配置目标；
3. Main/Audit 以及 Audit Pool 之间无重叠；
4. duplicate-collapsed population 与 physical population accounting 一致；
5. Evidence rows 与 Sample rows 一一对应；
6. Evidence Schema、Manifest、checksum 和 row accounting 通过；
7. deterministic recomputation 通过；
8. Source PDF 在 Evidence 前后没有检测到 size/mtime 变化；
9. 远程 Git dirty state 为 false。

Artifact Review 需要重点确认 Evidence Contract 是否可以进入下一阶段。无论 Review 结论
如何，本报告不构成 Domain Taxonomy 冻结、Benchmark Source Corpus 确定或 Gate 2C / Gate
2D 通过。
