# Gate 2B Calibration Sample & Evidence Report

Project: Mechanical Industry General Benchmark
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Milestone: Source Corpus Calibration v0.1
Report Status: Evidence Sufficiency Review Completed - Evidence Contract Revision Required
Gate 2B Runtime Self-check Verdict: **PASS**
Gate 2B Formal Verdict: **PASS WITH EVIDENCE REVISION**

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

Gate 2B runtime self-check 为 PASS；本次已完成 post-run Evidence Sufficiency Review。
由于 Evidence Sufficiency 未达到 Gate 2B 的 PASS 阈值，当前不启动 Taxonomy Annotation 或
Source Selection，下一步仅设计 Evidence v0.2 并在获得明确授权后决定是否重新运行。

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

manifest.json 使用既有的 normalized self-hash convention；表中值是 Runtime Artifact
validator 使用的规范化 checksum，而不是对包含自身 checksum 的原始 JSON 文件直接执行
sha256sum 的结果。Review 后重新执行只读 Artifact validator，结果仍为 passed。

Artifact validation summary：

- canonical artifact count: 4；
- checksum validation: passed；
- schema validation: passed；
- row accounting: passed；
- sample rows: 767；
- evidence rows: 767；
- validation status: passed。

这些大规模 Runtime Artifacts 不提交 Git；本地仓库只保留本审查报告和项目进度记录。

## 8. Gate 2B Runtime Review Status and Next Boundary

Runtime 层面的结论为：**Gate 2B self-check PASS**。本次已完成 Evidence Sufficiency
Review，正式 Gate 2B 结论为：**PASS WITH EVIDENCE REVISION**。

Runtime self-check 的依据包括：

1. Full Inventory canonical input 完整且 checksum、Schema、行数校验通过；
2. Main Sample 和 Audit Pools 达到配置目标；
3. Main/Audit 以及 Audit Pool 之间无重叠；
4. duplicate-collapsed population 与 physical population accounting 一致；
5. Evidence rows 与 Sample rows 一一对应；
6. Evidence Schema、Manifest、checksum 和 row accounting 通过；
7. deterministic recomputation 通过；
8. Source PDF 在 Evidence 前后没有检测到 size/mtime 变化；
9. 远程 Git dirty state 为 false。

本次 Evidence Sufficiency Review 发现部分 Parent Group 的 first-three-pages Evidence
无法稳定支持主题理解，因此 Evidence Contract v0.1 不能作为 Gate 2C 的统一输入直接接受。
本报告不构成 Domain Taxonomy 冻结、Benchmark Source Corpus 确定或 Gate 2C / Gate 2D
通过。

## Evidence Sufficiency Review

### 9.1 Review Methodology

本次 Review 只读取既有 Runtime Artifact：

/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565

没有重新抽样、重新运行 Evidence、修改四个 Runtime Artifact 或读取未被选中的 Source PDF。
所有判断只针对 Evidence 是否足以理解文档主题，不判断文档属于哪个 Domain，也不填写
任何 Domain Label。parent_group 仅作为原始 Source Group 标识。

Main Review Set 的选择步骤为：

1. 从已有 Main Sample 按 parent_group、relative_path、file_instance_id 排序；
2. 对每个 Parent Group 取 index = floor((N - 1) / 2) 的中位条目；
3. 20 个 Parent Group 各取 1 条，形成 20-item Main Evidence Review Set。

Risk-focused Review Set 的确定性选择为：

- Short Evidence：Main Sample 中 evidence_char_count 大于 0 的条目按
  evidence_char_count、parent_group、relative_path、file_instance_id 排序，取前 5 条；
- Truncated Evidence：Main Sample 中 evidence_truncated = true 的全部 7 条；
- Encoding / Garbled Risk：从 20-item Main Review Set 中人工确认 4 条明显异常项；
  未发现需要加入第五条的同等明确样本，因此不虚构第五条；
- Mixed Text 和 filename-unmatched：各自按 parent_group、relative_path、
  file_instance_id 排序后取前 5 条。

每个 Review Item 使用允许的 Evidence Quality 标签。sufficient、borderline 和
insufficient 是本次 Review 的结论字段，不是 Domain 分类。

### 9.2 Main Evidence Review Set

| No. | Parent Group | Relative path | Pages | Chars | Truncated | Quality labels | Title/topic | Abstract/summary | Technical context | Sufficiency | Review note |
| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | duanyajishu | duanyajishu/【2024-03】铝合金开闭机构舱门超塑气胀工艺.pdf | 13 | 5934 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要和关键词明确，前三页还包含工艺参数与结果。 |
| 2 | hanjie | hanjie/【2020-12】Ag和Zn对Sn58Bi钎料润湿性及焊点组织的影响.pdf | 10 | 4339 | false | garbled, needs_more_pages | no | no | no | insufficient | Evidence 主要为不可读编码片段，无法稳定识别标题、摘要和技术对象。 |
| 3 | hanjiexuebao | hanjiexuebao/【2011-12】基于SYSWELD的穿孔等离子弧焊接温度场有限元分析.pdf | 5 | 4086 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、关键词和引言均可理解，研究对象与分析方法清楚。 |
| 4 | jinshurechuli | jinshurechuli/【2024-10】冷轧压下率对IF钢退火热处理织构及成形性的影响.pdf | 5 | 5703 | false | readable, garbled, needs_more_pages | yes | no | partial | borderline | 题目和部分技术词可辨，但乱码贯穿摘要和正文；主题可推断但需要更多页或改进提取。 |
| 5 | jixiechuandong | jixiechuandong/【2026-02】基于改进Lazy-PRM算法的双臂巡检机器人避障路径规划.pdf | 8 | 5912 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、算法流程和指标清晰。 |
| 6 | jixiegongchengcailiao | jixiegongchengcailiao/【2022-8】淬火冷却速率对Zr-4合金显微组织和耐腐蚀性能的影响.pdf | 6 | 6796 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、材料、冷却速率和腐蚀结果清晰。 |
| 7 | jixiegongchengxuebao | jixiegongchengxuebao/【2016-10】基于T-S模糊故障树的多态系统性能可靠性.pdf | 8 | 6769 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要及模型和可靠性分析对象清晰。 |
| 8 | jixiegongchengxuebao2 | jixiegongchengxuebao2/【2016-6】离子注入碳化硅实现低温下外延合成石墨烯.pdf | 1 | 1368 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 单页摘要完整，研究对象、方法、参数和结论均在现有 Evidence 中。 |
| 9 | jixieqiangdu | jixieqiangdu/【2020-05】TBM驱动系统在不确定地质下的动力学分析.pdf | 8 | 5919 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | Evidence 内题目与 relative_path 文件名主题不一致，但 Evidence 本身的题目、摘要和技术内容清晰。 |
| 10 | lihuajianyan-huaxuefence | lihuajianyan-huaxuefence/【2015-12】八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素.pdf | 4 | 5829 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、测定方法和定量性能指标清晰。 |
| 11 | lihuajianyan-wulifence | lihuajianyan-wulifence/【2018-09】凝结水泵轴断裂原因分析.pdf | 4 | 4142 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、断裂原因和测试方法清晰。 |
| 12 | suxinggongchengxuebao | suxinggongchengxuebao/【2026-06】组合本构模型对高强钢CTB电池箱体纵梁辊弯回弹预测精度的影响.pdf | 10 | 8389 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、模型、实验/仿真方法和结果清晰。 |
| 13 | wusunjiance | wusunjiance/【2017-04】基于电磁感应的磁悬液浓度快速测试技术.pdf | 6 | 4930 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、测量原理、标定方法和结果清晰。 |
| 14 | yeyayuqidong | yeyayuqidong/【2018-09】多柱塞阀配流往复式容积泵新型流量调节方法研究.pdf | 5 | 5617 | false | garbled, needs_more_pages | no | no | no | insufficient | Evidence 主要为不可读编码，无法可靠确认主题或技术上下文。 |
| 15 | zhizaojishuyujichuang | zhizaojishuyujichuang/【2024-02】工艺参数对30CrMnSiA高强钢铣削力及铣削温度的影响.pdf | 6 | 5902 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、工艺参数、铣削力和温度指标清晰。 |
| 16 | zhizaoyezidonghua | zhizaoyezidonghua/【2024-09】有限缓冲区柔性流水车间调度优化问题求解.pdf | 11 | 4954 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、优化目标和算法方法清晰。 |
| 17 | zhongguohanjie | zhongguohanjie/【2020-01】Deformation analysis of a friction stir-welded thin sheet aluminum alloy joint.pdf | 7 | 11663 | true | readable, potentially_sufficient | yes | yes | yes | sufficient | 截断发生在后续正文，但 cap 前的标题、摘要、关键词和技术上下文已明确。 |
| 18 | zhongguojixiegongcheng | zhongguojixiegongcheng/【2022-07】脆性材料机械加工表面粗糙度模型的研究进展.pdf | 12 | 6050 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、研究对象及模型方法清晰。 |
| 19 | zhongguozhuzaozhuangbeiyujishu | zhongguozhuzaozhuangbeiyujishu/【2022-5】V法造型密闭式涂料烘干系统的优化设计.pdf | 3 | 3749 | false | garbled, needs_more_pages | no | no | no | insufficient | Evidence 主要为不可读编码和符号，无法可靠确认主题。 |
| 20 | zhuzao | zhuzao/【2023-03】厚大断面球墨铸铁齿轮铸件的研制.pdf | 5 | 3510 | false | readable, potentially_sufficient | yes | yes | yes | sufficient | 题目、摘要、铸件对象、工艺和检验要求清晰。 |

### 9.3 Main Group Coverage Summary

| Parent Group | Reviewed | Sufficient | Borderline | Insufficient |
| --- | ---: | ---: | ---: | ---: |
| duanyajishu | 1 | 1 | 0 | 0 |
| hanjie | 1 | 0 | 0 | 1 |
| hanjiexuebao | 1 | 1 | 0 | 0 |
| jinshurechuli | 1 | 0 | 1 | 0 |
| jixiechuandong | 1 | 1 | 0 | 0 |
| jixiegongchengcailiao | 1 | 1 | 0 | 0 |
| jixiegongchengxuebao | 1 | 1 | 0 | 0 |
| jixiegongchengxuebao2 | 1 | 1 | 0 | 0 |
| jixieqiangdu | 1 | 1 | 0 | 0 |
| lihuajianyan-huaxuefence | 1 | 1 | 0 | 0 |
| lihuajianyan-wulifence | 1 | 1 | 0 | 0 |
| suxinggongchengxuebao | 1 | 1 | 0 | 0 |
| wusunjiance | 1 | 1 | 0 | 0 |
| yeyayuqidong | 1 | 0 | 0 | 1 |
| zhizaojishuyujichuang | 1 | 1 | 0 | 0 |
| zhizaoyezidonghua | 1 | 1 | 0 | 0 |
| zhongguohanjie | 1 | 1 | 0 | 0 |
| zhongguojixiegongcheng | 1 | 1 | 0 | 0 |
| zhongguozhuzaozhuangbeiyujishu | 1 | 0 | 0 | 1 |
| zhuzao | 1 | 1 | 0 | 0 |
| **Total** | **20** | **16** | **1** | **3** |

### 9.4 Risk-focused Review

#### Short Evidence Review

以下 5 条按 evidence_char_count 从低到高确定。Short 不自动等于不足；重点是现有
标题、摘要或技术上下文是否已经足以理解主题。

| No. | Relative path | Chars | Quality labels | Title/topic | Abstract/summary | Technical context | Sufficiency | Review note |
| ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | hanjiexuebao/【1980-01】发刊词.pdf | 739 | readable, potentially_sufficient | yes | not_applicable | partial | sufficient | 文本虽短，但已清楚说明焊接学报创刊目的和所覆盖的焊接技术范围。 |
| 2 | zhizaojishuyujichuang/【2020-05】刀具磨削系统中磨削路径自由规划.pdf | 1215 | readable, too_short, needs_more_pages | yes | no | partial | borderline | 前两页无有效文本，第三页出现砂轮坐标系和位姿路径；能理解局部主题，但缺少标题/摘要上下文。 |
| 3 | jixiegongchengxuebao2/【2016-6】离子注入碳化硅实现低温下外延合成石墨烯.pdf | 1368 | readable, potentially_sufficient | yes | yes | yes | sufficient | 单页摘要已经给出材料、离子注入条件、检测方法和主要结论。 |
| 4 | suxinggongchengxuebao/【2026-06】《塑性工程学报》征稿简则.pdf | 1742 | readable, potentially_sufficient | yes | not_applicable | partial | sufficient | 文档用途、征稿范围和技术领域清楚；它是期刊说明而非研究论文，主题判断不依赖摘要。 |
| 5 | wusunjiance/【2021-10】第二十六届中国国际质量控制与测试工业设备展览会即将召开.pdf | 1861 | readable, potentially_sufficient | yes | not_applicable | partial | sufficient | 展会主题、无损检测/测试设备范围和会议内容清楚。 |

Short Evidence 结果：4 条 sufficient、1 条 borderline、0 条 insufficient；too_short
为 1 条，needs_more_pages 为 1 条。结论是短 Evidence 本身不是主要阻塞因素。

#### Truncated Evidence Review

Main Sample 中全部 7 条 evidence_truncated = true 的条目均被 Review。截断发生在
12,000 字符 cap 后，不把截断本身作为质量失败；重点判断 cap 之前主题是否已经明确。

| No. | Relative path | Chars | Quality labels | Title/topic | Abstract/summary | Technical context | Sufficiency | Review note |
| ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | zhongguohanjie/【2018-01】A survey on future research about electron beam welding for aerospace applications.pdf | 12000 | garbled, needs_more_pages | no | no | no | insufficient | 前三页及 cap 前内容主要为不可读编码，无法稳定理解主题；问题不只是截断。 |
| 2 | zhongguohanjie/【2019-02】Lap joining Al5052 to Ti6Al4V by GTAW with AlSi5 filler wire.pdf | 12000 | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、材料、焊接参数和强度结果在截断前已清晰。 |
| 3 | zhongguohanjie/【2022-01】Research progress on solder thermal interface materials.pdf | 12000 | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要和综述对象在 cap 前明确，后续内容不影响主题识别。 |
| 4 | zhongguohanjie/【2022-04】From statistical analysis to process optimization during cladding using a Nd_YAG laser.pdf | 12000 | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、工艺参数和优化目标在 cap 前已明确。 |
| 5 | zhongguohanjie/【2023-04】Investigation on influence of alloying on phase transitions of duplex stainless steel based on thermochemical calculation.pdf | 12000 | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题和摘要已经说明合金元素、相变及热化学计算主题。 |
| 6 | zhongguohanjie/【2024-03】Impact of welding equipment on power quality.pdf | 12000 | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、焊接设备和电能质量问题在 cap 前已明确。 |
| 7 | zhongguohanjie/【2025-04】Wear performance and microstructures of Fe-Cr-C alloy cladding on heterogeneous welded joints of NM450_ER70-G_ZG30SiMn.pdf | 12000 | readable, potentially_sufficient | yes | yes | yes | sufficient | 标题、摘要、材料体系和磨损/显微组织目标在 cap 前已明确。 |

Truncated Evidence 结果：6 条 sufficient、0 条 borderline、1 条 insufficient；7 条均保留
truncated 标记。该结果支持“主题已明确后，12,000 字符 cap 通常可接受”，但不支持
对编码不可读样本直接放行。

#### Encoding / Garbled Risk Review

从 20-item Main Review Set 中确认 4 条明确的异常样本。未发现第五条具有同等明确的
异常证据，因此不人为扩充样本。

| Relative path | Quality labels | Sufficiency | Review note |
| --- | --- | --- | --- |
| hanjie/【2020-12】Ag和Zn对Sn58Bi钎料润湿性及焊点组织的影响.pdf | garbled, needs_more_pages | insufficient | 标题、摘要和正文无法从 Evidence 中稳定辨认。 |
| jinshurechuli/【2024-10】冷轧压下率对IF钢退火热处理织构及成形性的影响.pdf | readable, garbled, needs_more_pages | borderline | 题目和局部技术词可辨，但乱码明显影响摘要和正文理解。 |
| yeyayuqidong/【2018-09】多柱塞阀配流往复式容积泵新型流量调节方法研究.pdf | garbled, needs_more_pages | insufficient | Evidence 主要是异常编码，缺少可靠标题和技术上下文。 |
| zhongguozhuzaozhuangbeiyujishu/【2022-5】V法造型密闭式涂料烘干系统的优化设计.pdf | garbled, needs_more_pages | insufficient | Evidence 主要为不可读编码和符号，无法稳定确认主题。 |

Encoding-risk 结果：0 条 sufficient、1 条 borderline、3 条 insufficient；4 条均有
garbled 标签，4 条均有 needs_more_pages 标签。

### 9.5 Audit Pool Review

#### Mixed Text Audit

按 parent_group、relative_path、file_instance_id 排序选取 5 条。Mixed Text 不是 Main
Calibration 输入失败指标；本节只判断当前 Evidence 是否可用，以及是否需要特殊 routing。

| No. | Relative path | Chars | Quality labels | Sufficiency | Routing conclusion | Review note |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | hanjiexuebao/【1987-04】B30_QTS爆炸复合板焊接接头断裂行为的研究.pdf | 2929 | readable, potentially_sufficient, garbled | sufficient | usable with current Evidence | 标题、摘要和断裂试验上下文可辨，局部字符异常不阻碍主题理解。 |
| 2 | hanjiexuebao/【2000-04】LCL型谐振式弧焊电源稳态数学分析.pdf | 9924 | garbled, needs_more_pages | insufficient | requires special routing | 前页无有效文本，后续中英文内容编码异常明显，无法稳定确认完整主题。 |
| 3 | hanjiexuebao/【2000-04】奥-贝球铁焊接研究进展.pdf | 2412 | readable, potentially_sufficient | sufficient | usable with current Evidence | 前两页无有效文本，但第三页包含清晰的主题术语、组织和热处理上下文。 |
| 4 | hanjiexuebao/【2000-04】拘束焊对接接头的平面外拘束力.pdf | 4006 | readable, potentially_sufficient | sufficient | usable with current Evidence | 前页无有效文本，后两页的公式、拘束力和焊接接头技术上下文清楚。 |
| 5 | hanjiexuebao/【2000-04】相变超塑性焊接(TSW)过程的有限元分析.pdf | 4072 | readable, potentially_sufficient | sufficient | usable with current Evidence | 前页无有效文本，但现有后续页已明确相变超塑性焊接和有限元分析主题。 |

Mixed Text Audit 结果：4 / 5 条 usable with current Evidence，1 / 5 条 requires special
routing。没有因此修改 Main Sample，也没有修改 Filename Parser 或 Runtime Artifact。

#### Filename-unmatched Audit

按 parent_group、relative_path、file_instance_id 排序选取 5 条。Filename Parser unmatched
只表示规则未匹配，不自动表示 Evidence 不可用。

| No. | Relative path | Chars | Quality labels | Sufficiency | Routing conclusion | Review note |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | hanjie/振动削减铝合金焊接残余应力的细观模拟.pdf | 4253 | garbled, needs_more_pages | insufficient | requires special routing | Evidence 编码异常明显，Filename Parser 状态与 Evidence 不可用同时出现。 |
| 2 | jixiegongchengcailiao/【2019-3】316L奥氏体不锈钢稳定辊轴头断裂的原因.pdf | 4960 | readable, potentially_sufficient | sufficient | usable with current Evidence | 标题、摘要、失效原因和分析方法清楚。 |
| 3 | jixiegongchengcailiao/【2020-8】基于损伤力学的蒸汽转化炉热壁集气管蠕变损伤有限元分析.pdf | 6566 | readable, potentially_sufficient | sufficient | usable with current Evidence | 标题、摘要、模型和蠕变损伤上下文清楚。 |
| 4 | jixiegongchengcailiao/【2022-2】微米尺度压痕测试设备的研发及其可靠性.pdf | 6287 | readable, potentially_sufficient | sufficient | usable with current Evidence | 标题、摘要、设备、测试方法和性能结果清楚。 |
| 5 | jixiegongchengcailiao/【2023-6】热氧化对锂基磁流变脂分子结构和磁流变性能的影响.pdf | 6956 | readable, potentially_sufficient | sufficient | usable with current Evidence | 标题、摘要、材料、热氧化条件和性能结果清楚。 |

Filename-unmatched Audit 结果：4 / 5 条 usable with current Evidence，1 / 5 条 requires
special routing。总体上 Filename Parser unmatched 不影响正文主题理解，但不应掩盖同一条
记录中的编码风险；本次不修改 Filename Regex。

#### Text-absent and Source-quality Exception Behavior

- Text-absent Audit Pool 的 60 条均完成页面读取流程，Evidence status 为 success，但
  zero-text evidence 为 60；这与 text_absent routing expectation 一致。本节不对其进行
  textual Domain sufficiency 判断。
- Source Quality Exception Pool 的 7 条均为 not_applicable，没有执行页面 Evidence
  extraction；行为符合设计。

### 9.6 Quality Label and Sufficiency Summary

Gate 判定以 20-item Main Group Review Set 为主分母；Risk-focused Review Set 允许与其
重复，因此单独报告，不把各集合简单相加。

| Review set | Count | Sufficient | Rate | Borderline | Rate | Insufficient | Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Main Group Review Set | 20 | 16 | 80.0% | 1 | 5.0% | 3 | 15.0% |
| Short Evidence Review | 5 | 4 | 80.0% | 1 | 20.0% | 0 | 0.0% |
| Truncated Evidence Review | 7 | 6 | 85.7% | 0 | 0.0% | 1 | 14.3% |
| Encoding / Garbled Risk Review | 4 | 0 | 0.0% | 1 | 25.0% | 3 | 75.0% |

Main Group Review Set Quality Label counts：

| Quality label | Count |
| --- | ---: |
| front_matter_heavy | 0 |
| too_short | 0 |
| garbled | 4 |
| empty | 0 |
| needs_more_pages | 4 |
| readable | 16 |
| potentially_sufficient | 16 |

Risk-focused Quality Label counts：

| Review set | front_matter_heavy | too_short | garbled | empty | needs_more_pages |
| --- | ---: | ---: | ---: | ---: | ---: |
| Short Evidence Review | 0 | 1 | 0 | 0 | 1 |
| Truncated Evidence Review | 0 | 0 | 1 | 0 | 1 |
| Encoding / Garbled Risk Review | 0 | 0 | 4 | 0 | 4 |

### 9.7 Evidence Sufficiency Statistics and Gate Decision

20-item Main Group Review Set 的 sufficient rate 为 80.0%，低于 Gate 2B 要求的至少
90%；insufficient rate 为 15.0%，高于不超过 5% 的要求。另有 1 条 borderline。
因此满足 PASS WITH EVIDENCE REVISION 条件，不满足 PASS 条件。

本次没有发现 Pipeline、Artifact、Sample mapping、Source Provenance 或 checksum 问题，
所以不判定为 FAIL。问题集中在部分 first-three-pages Evidence 的可读性和主题信息不足，
尤其是明确的编码异常，而不是 Runtime Artifact 完整性问题。

#### Evidence Contract Decision

结论：

Evidence Contract v0.1：**Not Accepted as a Universal Gate 2C Input**

Formal Gate 2B Verdict：**PASS WITH EVIDENCE REVISION**

建议的 Evidence v0.2 方向（本次只提出，不执行）：

1. 对当前 readable 且 potentially_sufficient 的条目保留 first three pages 基线；
2. 对 too_short、needs_more_pages 或 front_matter_heavy 条目，评估 first five pages
   或 first three pages 加一个 deterministic middle page；
3. 对 garbled 条目单独设计 extraction/routing 规则；增加页面不一定能解决编码问题；
4. 保留当前 Evidence Quality 标签、review queue 和 provenance，不修改本次 Runtime
   Artifact；
5. 在 Evidence v0.2 设计获得批准前，不重新运行 Evidence，也不进入 Gate 2C Annotation。

本次 Formal Gate 2B 不是 Gate 2C 通过，不允许直接启动 LLM Taxonomy Annotation。
