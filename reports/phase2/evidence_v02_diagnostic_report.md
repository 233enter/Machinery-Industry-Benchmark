# Evidence v0.2 Diagnostic Report

Project: Mechanical Industry General Benchmark
Phase: Phase 2 - Taxonomy Calibration & Source Selection
Milestone: Source Corpus Calibration v0.1
Report Status: Diagnostic Completed - Evidence v0.2 Conditional Design Freeze
Gate 2B Diagnostic Status: **HOLD**
Related Design: `docs/12_phase2_evidence_v02_design.md`

## 1. Scope and Stop Boundary

本报告记录对既有 Gate 2B Evidence 的 8-file deterministic diagnostic probe。目标是比较：

```text
existing Evidence v0.1
vs
PyMuPDF first3 + body probes
vs
pdftotext -layout on the same body probes
```

本次只读取：

```text
Runtime Artifact:
/data/suzhe/migb/phase2/runs/p2b-20260915T023641Z-cbde565

Source Root:
/mnt/data_nfs/dataset/original/cmes/journal
```

没有重新抽样，没有重新运行完整 Gate 2B，没有修改以下 immutable Artifact：

```text
calibration_sample.parquet
calibration_evidence.jsonl
manifest.json
statistics.json
```

没有调用 LLM，没有执行 Domain classification、Taxonomy Annotation、Source Selection、
OCR、MinerU 或 Full Evidence v0.2 Runtime。Probe 输出仅通过远程标准输出读取，没有写入
Source Corpus 或 Runtime Artifact。8 个 Source PDF 的 size 和 mtime 在 Probe 前后均未变化。

## 2. Problem Set

Problem Set 直接复用原 Evidence Sufficiency Review 的 4 个问题项：

| Item | `calibration_item_id` | `file_instance_id` | Parent Group | Relative path | Pages | v0.1 pages | v0.1 chars | Quality labels | Sufficiency |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| P1 | `67504202-11fc-51ae-8017-9ad5f4bdefe5` | `73140782-13a3-5089-91f3-830dac4c50bb` | `hanjie` | `hanjie/【2020-12】Ag和Zn对Sn58Bi钎料润湿性及焊点组织的影响.pdf` | 10 | `[0,1,2]` | 4339 | `garbled, needs_more_pages` | insufficient |
| P2 | `8ff31d50-6ffe-5e49-8890-917e51c8e936` | `cbb7bbfc-3ae1-5543-ac19-fd35f0c1ef6c` | `jinshurechuli` | `jinshurechuli/【2024-10】冷轧压下率对IF钢退火热处理织构及成形性的影响.pdf` | 5 | `[0,1,2]` | 5703 | `readable, garbled, needs_more_pages` | borderline |
| P3 | `791f9b84-1b42-54eb-a977-6400614f0285` | `7a88b028-bc38-51f1-b522-2708d361aea6` | `yeyayuqidong` | `yeyayuqidong/【2018-09】多柱塞阀配流往复式容积泵新型流量调节方法研究.pdf` | 5 | `[0,1,2]` | 5617 | `garbled, needs_more_pages` | insufficient |
| P4 | `d2816f50-ace1-5dfd-87b0-6ab4b8df929e` | `db620b26-0f63-566f-ac8c-b5ecc9586cc4` | `zhongguozhuzaozhuangbeiyujishu` | `zhongguozhuzaozhuangbeiyujishu/【2022-5】V法造型密闭式涂料烘干系统的优化设计.pdf` | 3 | `[0,1,2]` | 3749 | `garbled, needs_more_pages` | insufficient |

原 Review note：

- P1：Evidence 主要为不可读编码片段，无法稳定识别标题、摘要和技术对象。
- P2：题目和部分技术词可辨，但乱码贯穿摘要和正文；主题可推断但需要更多页或改进提取。
- P3：Evidence 主要是不可读编码，无法可靠确认主题或技术上下文。
- P4：Evidence 主要为不可读编码和符号，无法可靠确认主题。

## 3. Control Set

Control 从原 Main Review Set 的 16 条 `sufficient` 中确定性选择。由于原 16 条中没有与
问题项相同的 Parent Group，本次使用 page count 距离最小、再按
`parent_group`、`relative_path`、`file_instance_id` 稳定排序的一对一匹配：

| Control | `calibration_item_id` | `file_instance_id` | Parent Group | Relative path | Pages | v0.1 chars | Quality labels | Sufficiency | Matched problem |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| C1 | `79562004-0aef-5222-afc8-b0e0bcb73cba` | `845edf7c-b950-5e5b-887c-532796b567b0` | `suxinggongchengxuebao` | `suxinggongchengxuebao/【2026-06】组合本构模型对高强钢CTB电池箱体纵梁辊弯回弹预测精度的影响.pdf` | 10 | 8389 | `readable, potentially_sufficient` | sufficient | P1 |
| C2 | `006ef0ba-d56b-5aab-b4d6-f45fbb3922ca` | `a8035ce4-5217-5179-ac86-2ac2f0f3ae51` | `hanjiexuebao` | `hanjiexuebao/【2011-12】基于SYSWELD的穿孔等离子弧焊接温度场有限元分析.pdf` | 5 | 4086 | `readable, potentially_sufficient` | sufficient | P2 |
| C3 | `78ba6d84-c7b6-5dca-9ff9-1838689c8bc1` | `43fef19b-d65e-5a6b-b0f4-5085d21881d2` | `zhuzao` | `zhuzao/【2023-03】厚大断面球墨铸铁齿轮铸件的研制.pdf` | 5 | 3510 | `readable, potentially_sufficient` | sufficient | P3 |
| C4 | `7d1cfa14-757d-56aa-9c0f-9b59c27405aa` | `38c6fc51-b6b8-5086-ba9f-63f367db71b4` | `lihuajianyan-huaxuefence` | `lihuajianyan-huaxuefence/【2015-12】八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素.pdf` | 4 | 5829 | `readable, potentially_sufficient` | sufficient | P4 |

## 4. Diagnostic Method

### 4.1 Probe A: Existing Evidence v0.1

Probe A 不重新抽取 PDF，直接读取既有 `calibration_evidence.jsonl`：

```text
pages = [0, 1, 2]
global_cap = 12000
```

这是 immutable baseline。v0.1 Runtime 没有保存 per-page cap record，因此本报告对 A 只
报告既有 Evidence 的总字符、页面索引、global truncation 和诊断指标。

### 4.2 Probe B: PyMuPDF Body Probe

对于 page count 为 `N` 的 PDF：

```python
base = [0, 1, 2]
middle_probe = floor((N - 1) * 0.50)
late_probe = floor((N - 1) * 0.75)
selected = sorted(unique(i for i in base + [middle_probe, late_probe] if 0 <= i < N))
```

Probe B 使用 PyMuPDF，先对每个 page 独立应用 `per_page_cap=4000`，再使用
`global_cap=20000`。页面实际集合：

| Items | Page count | Selected pages |
| --- | ---: | --- |
| P1, C1 | 10 | `[0,1,2,4,6]` |
| P2, P3, C2, C3 | 5 | `[0,1,2,3]` |
| P4, C4 | 3 / 4 | `[0,1,2]` |

### 4.3 Probe C: Poppler `pdftotext`

远程环境检查结果：

```text
/usr/bin/pdftotext
pdftotext version 22.02.0
```

Probe C 对 Probe B 的完全相同页面集合逐页执行：

```text
pdftotext -layout -f <page+1> -l <page+1> <pdf> -
```

同样使用 `per_page_cap=4000` 和 `global_cap=20000`。没有读取全文，没有安装依赖，
没有修改 Source PDF。

### 4.4 Unicode Quality Metrics

每个策略记录：

```text
total_chars
replacement_char_count
private_use_char_count
control_char_count
printable_char_ratio
```

`control_char_count` 排除 `\n`、`\r`、`\t`；`printable_char_ratio` 的分母也排除这三种
换行类字符。指标只用于诊断观察，不作为自动 `garbled` 判定阈值。

## 5. Problem Item Paired Comparison

### 5.1 Sufficiency and Readability

| Item | Strategy | Pages | Stored chars | Global truncated | Readability / quality observation | Sufficiency |
| --- | --- | --- | ---: | --- | --- | --- |
| P1 | v0.1 Artifact | `[0,1,2]` | 4339 | no | garbled；标题、摘要和技术上下文不可稳定理解 | insufficient |
| P1 | PyMuPDF Probe B | `[0,1,2,4,6]` | 7038 | no | 增加正文页后仍是相同类型乱码 | insufficient |
| P1 | pdftotext Probe C | `[0,1,2,4,6]` | 20000 | yes | printable ratio 上升，但标题和技术上下文仍不可稳定理解 | insufficient |
| P2 | v0.1 Artifact | `[0,1,2]` | 5703 | no | readable 片段与 garbled 并存；题目可辨，摘要和正文不稳定 | borderline |
| P2 | PyMuPDF Probe B | `[0,1,2,3]` | 7426 | no | page 3 增加正文/图示片段，但未消除字符映射问题 | borderline |
| P2 | pdftotext Probe C | `[0,1,2,3]` | 16055 | no | layout 结构略有改善，但 glyph mapping 仍不足以升为 sufficient | borderline |
| P3 | v0.1 Artifact | `[0,1,2]` | 5617 | no | 主要为异常编码，无法可靠确认主题 | insufficient |
| P3 | PyMuPDF Probe B | `[0,1,2,3]` | 6627 | no | 增加 page 3 后仍为异常编码 | insufficient |
| P3 | pdftotext Probe C | `[0,1,2,3]` | 11882 | no | 可打印比例上升，但主题仍不能稳定理解 | insufficient |
| P4 | v0.1 Artifact | `[0,1,2]` | 3749 | no | 全部 3 页受异常编码影响 | insufficient |
| P4 | PyMuPDF Probe B | `[0,1,2]` | 3749 | no | 文件只有 3 页，无法增加正文页；乱码保持不变 | insufficient |
| P4 | pdftotext Probe C | `[0,1,2]` | 7121 | no | 字符量增加，但语义仍不可稳定识别 | insufficient |

### 5.2 Problem Item Previews

以下 preview 均为策略输出开头的短片段，每个策略少于 300 字符，不复制完整 Evidence。

#### P1 — `hanjie`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:0>>> !"#$%&" '&$()*" !"#$ !"!"!" #!# ! !"#$%&'()*+,-./0` |
| PyMuPDF B | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:4>>> !"#$%&" '&$()*" !"#$ !"!"!" #!# )*!&'Q»¼½×¤Ï!#CQ»¼½<ç§£ÅÎ` |
| pdftotext C | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:0>>> !"#$%&" '&$()*" !"#$ ... )* !&'Q»¼½×¤Ï!#CQ»¼½<ç§£ÅÎ` |

#### P2 — `jinshurechuli`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | yes / no / partial | `readable, garbled, needs_more_pages` | `组织与性能 冷轧压下率对1M钢退火热处理织构及成形性的影响 ... 摘要 通过试验研究了不同冷轧压下率` |
| PyMuPDF B | yes / no / partial | `readable, garbled, needs_more_pages` | `图!#不同冷轧压下率的_/钢在 E%% @退火 ;%% T后的.]/图 ... 织构` |
| pdftotext C | yes / no / partial | `readable, garbled, needs_more_pages` | `第!" 卷 ... 图不 同冷轧 压下率` |

#### P3 — `yeyayuqidong`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:0>>> $%&'( !"#$ !" % # !"#&#"'##$(! )*'+,,-'#"""./$0$'!"#$` |
| PyMuPDF B | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:3>>> !"#$ !" % # $%&'( [ /0 43J/1; L7/X;M¾Ó}±*´ó]^` |
| pdftotext C | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:3>>> !"#$ !" % #                            $%&'(                              #"#` |

#### P4 — `zhongguozhuzaozhuangbeiyujishu`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:0>>> ! ! " " #$ ! !"#$%&'( )*+,&- ./012 )"3456 7/282` |
| PyMuPDF B | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:0>>> ! ! " " #$ ! !"#$%&'( )*+,&- ./012 )"3456 7/282` |
| pdftotext C | no / no / no | `garbled, needs_more_pages` | `<<<PAGE:0>>> ! !*  ! ! " ... $%$$  )  +;09 !* D;9 !` |

## 6. Control Item Regression Review

### 6.1 Sufficiency Result

| Control | v0.1 | PyMuPDF Probe B | pdftotext Probe C | Regression |
| --- | --- | --- | --- | --- |
| C1 | sufficient | sufficient | sufficient | no meaningful regression |
| C2 | sufficient | sufficient | sufficient | no meaningful regression |
| C3 | sufficient | sufficient | sufficient | no meaningful regression |
| C4 | sufficient | sufficient | sufficient | no meaningful regression |

### 6.2 Control Previews

#### C1 — `suxinggongchengxuebao`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | yes / yes / yes | `readable, potentially_sufficient` | `第33 卷 第6期 2026年6月 塑性工程学报 JOURNAL OF PLASTICITY ENGINEERING 引文格式: 组合本构模型对高强钢CTB` |
| PyMuPDF B | yes / yes / yes | `readable, potentially_sufficient` | `第33 卷 第6期 2026年6月 塑性工程学报 ... 组合本构模型对高强钢CTB 电池箱体纵梁辊弯回弹预测精度` |
| pdftotext C | yes / yes / yes | `readable, potentially_sufficient` | `第 33 卷 第 6 期 塑性工程学报 ... 组合本构模型对高强钢 CTB 电池箱体纵梁` |

#### C2 — `hanjiexuebao`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | yes / yes / yes | `readable, potentially_sufficient` | `第32 卷第12 期 2011 年12 月 焊接学报 基于SYSWELD 的穿孔等离子弧焊接温度场有限元分析` |
| PyMuPDF B | yes / yes / yes | `readable, potentially_sufficient` | `第32 卷第12 期 ... 基于SYSWELD 的穿孔等离子弧焊接温度场有限元分析 ... 摘要` |
| pdftotext C | yes / yes / yes | `readable, potentially_sufficient` | `第 32 卷 第 12 期 焊接学报 ... 基于 SYSWELD 的穿孔等离子弧焊接温度场有限元分析` |

#### C3 — `zhuzao`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | yes / yes / yes | `readable, potentially_sufficient` | `315 工艺技术 2023年 第3期/第72卷 厚大断面球墨铸铁齿轮铸件的研制 摘要：为获得厚大断面球墨铸铁齿轮铸件` |
| PyMuPDF B | yes / yes / yes | `readable, potentially_sufficient` | `315 工艺技术 2023年 第3期/第72卷 厚大断面球墨铸铁齿轮铸件的研制 ... 关键词：球墨铸铁` |
| pdftotext C | yes / yes / yes | `readable, potentially_sufficient` | `2023年 第3期/第72卷 工艺技术 厚大断面球墨铸铁齿轮铸件的研制 ... 摘要` |

#### C4 — `lihuajianyan-huaxuefence`

| Strategy | Title / summary / context visibility | Quality labels | Preview |
| --- | --- | --- | --- |
| v0.1 | yes / yes / yes | `readable, potentially_sufficient` | `八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素 ... 摘要：采用电感耦合等离子体质谱法` |
| PyMuPDF B | yes / yes / yes | `readable, potentially_sufficient` | `八极杆碰撞反应池-电感耦合等离子体质谱法测定食用香精中多元素 ... 关键词` |
| pdftotext C | yes / yes / yes | `readable, potentially_sufficient` | `八极杆碰撞反应池-电感耦合等离子体质谱法 测定食用香精中多元素 ... 摘要` |

## 7. Page-level Character Accounting

页面记录格式为 `page_index:raw_char_count→stored_char_count`；末尾 `*` 表示该页
`page_truncated=true`。Probe A 的 v0.1 Artifact 没有保存此级别记录，见 Section 4.1。

| Item | Strategy | Selected pages | Page records |
| --- | --- | --- | --- |
| P1 | PyMuPDF B | `[0,1,2,4,6]` | `0:1767→1767; 1:1666→1666; 2:865→865; 4:1323→1323; 6:1348→1348` |
| P1 | pdftotext C | `[0,1,2,4,6]` | `0:5827→4000*; 1:6565→4000*; 2:6075→4000*; 4:4766→4000*; 6:4656→4000*` |
| P2 | PyMuPDF B | `[0,1,2,3]` | `0:2870→2870; 1:1467→1467; 2:1325→1325; 3:1709→1709` |
| P2 | pdftotext C | `[0,1,2,3]` | `0:22812→4000*; 1:5663→4000*; 2:4514→4000*; 3:9685→4000*` |
| P3 | PyMuPDF B | `[0,1,2,3]` | `0:2666→2666; 1:2155→2155; 2:755→755; 3:996→996` |
| P3 | pdftotext C | `[0,1,2,3]` | `0:11804→4000*; 1:3532→3532; 2:1103→1103; 3:3192→3192` |
| P4 | PyMuPDF B | `[0,1,2]` | `0:1252→1252; 1:939→939; 2:1517→1517` |
| P4 | pdftotext C | `[0,1,2]` | `0:2729→2729; 1:1769→1769; 2:2582→2582` |
| C1 | PyMuPDF B | `[0,1,2,4,6]` | `0:3858→3858; 1:2531→2531; 2:1959→1959; 4:1225→1225; 6:1335→1335` |
| C1 | pdftotext C | `[0,1,2,4,6]` | `0:3769→3769; 1:4758→4000*; 2:4587→4000*; 4:3598→3598; 6:3278→3278` |
| C2 | PyMuPDF B | `[0,1,2,3]` | `0:1664→1664; 1:1409→1409; 2:972→972; 3:2578→2578` |
| C2 | pdftotext C | `[0,1,2,3]` | `0:4501→4000*; 1:2761→2761; 2:1796→1796; 3:5447→4000*` |
| C3 | PyMuPDF B | `[0,1,2,3]` | `0:1405→1405; 1:1733→1733; 2:331→331; 3:1077→1077` |
| C3 | pdftotext C | `[0,1,2,3]` | `0:2361→2361; 1:4296→4000*; 2:587→587; 3:2228→2228` |
| C4 | PyMuPDF B | `[0,1,2]` | `0:1901→1901; 1:1802→1802; 2:2085→2085` |
| C4 | pdftotext C | `[0,1,2]` | `0:9502→4000*; 1:11181→4000*; 2:11774→4000*` |

## 8. Unicode Quality Metrics

表中 `Co` 为 private-use characters，`Cc` 为排除 `\n`、`\r`、`\t` 后的 control
characters。Probe A/B/C 的指标均包含 assembled Evidence 的 page delimiter。

| Item | Strategy | Total chars | U+FFFD | Co | Cc | Printable ratio | Global truncated |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P1 | v0.1 A | 4339 | 0 | 0 | 304 | 0.920758 | no |
| P1 | PyMuPDF B | 7038 | 0 | 0 | 532 | 0.915342 | no |
| P1 | pdftotext C | 20000 | 0 | 0 | 394 | 0.979423 | yes |
| P2 | v0.1 A | 5703 | 0 | 0 | 0 | 1.000000 | no |
| P2 | PyMuPDF B | 7426 | 0 | 0 | 0 | 1.000000 | no |
| P2 | pdftotext C | 16055 | 0 | 0 | 0 | 1.000000 | no |
| P3 | v0.1 A | 5617 | 0 | 0 | 508 | 0.900442 | no |
| P3 | PyMuPDF B | 6627 | 0 | 0 | 652 | 0.891570 | no |
| P3 | pdftotext C | 11882 | 0 | 0 | 646 | 0.941908 | no |
| P4 | v0.1 A | 3749 | 0 | 0 | 244 | 0.928531 | no |
| P4 | PyMuPDF B | 3749 | 0 | 0 | 244 | 0.928531 | no |
| P4 | pdftotext C | 7121 | 0 | 0 | 234 | 0.965795 | no |
| C1 | v0.1 A | 8389 | 0 | 0 | 0 | 0.997160 | no |
| C1 | PyMuPDF B | 10977 | 0 | 0 | 0 | 0.995285 | no |
| C1 | pdftotext C | 18714 | 0 | 0 | 3 | 0.999837 | no |
| C2 | v0.1 A | 4086 | 0 | 20 | 0 | 0.994737 | no |
| C2 | PyMuPDF B | 6678 | 0 | 20 | 0 | 0.996823 | no |
| C2 | pdftotext C | 12612 | 0 | 18 | 2 | 0.998385 | no |
| C3 | v0.1 A | 3510 | 0 | 0 | 0 | 0.994289 | no |
| C3 | PyMuPDF B | 4601 | 0 | 0 | 0 | 0.988996 | no |
| C3 | pdftotext C | 9231 | 0 | 0 | 3 | 0.999669 | no |
| C4 | v0.1 A | 5829 | 0 | 30 | 0 | 0.987433 | no |
| C4 | PyMuPDF B | 5829 | 0 | 30 | 0 | 0.987433 | no |
| C4 | pdftotext C | 12041 | 0 | 19 | 0 | 0.998385 | no |

重要观察：P1/P3 的 `control_char_count` 仍然很高，P4 的 printable ratio 也不能反映
语义可读性；反过来，部分 control 的 `Co` 并未阻止人工理解。因而本次不设置或冻结任何
Unicode threshold，也不使用字符指标自动清除 `garbled` 标签。

## 9. Root Cause Classification

| Item | Primary root cause | Secondary observation | Evidence |
| --- | --- | --- | --- |
| P1 | `text_extraction_encoding_issue` | 增加正文页没有改善；Poppler 仍为乱码片段 | B/C 均 insufficient |
| P2 | `text_extraction_encoding_issue` | page 3 增加了一些上下文，但未消除摘要/正文的字符映射问题 | A/B/C 均未达到 sufficient |
| P3 | `text_extraction_encoding_issue` | 增加 page 3 没有改善；Poppler 只提高可打印比例 | B/C 均 insufficient |
| P4 | `text_extraction_encoding_issue` | 文件只有 3 页，且所有页面均受编码异常影响 | B 与 A 相同，C 仍 insufficient |

总体主要根因：

```text
text_extraction_encoding_issue
```

4/4 Problem Items 均归入该类别；没有证据表明 page coverage 单独能够解决当前问题。

## 10. Probe Results and Evidence v0.2 Decision

### Probe A Result

Probe A 成功作为既有 v0.1 baseline 读取；4 个问题项保持原 Review 结论。

### Probe B Result

Probe B 成功按确定性页面公式提取，4 个 control 均保持 sufficient，但 4 个问题项中：

```text
0 / 4 improved to sufficient
```

因此增加正文页不能单独解决本次问题。

### Probe C Result

Probe C 可用，使用 `/usr/bin/pdftotext 22.02.0` 和 `-layout`。部分样本的 printable ratio
上升，但 4 个问题项中：

```text
0 / 4 improved to sufficient
```

因此 Poppler fallback 也没有形成当前问题项的充分语义恢复。

### Evidence v0.2 Chosen Strategy

结果属于 Case D。Evidence v0.2 只冻结一个 **conditional text-only design**：

```text
Stage 1: PyMuPDF first3 + deterministic middle/late body probes
Stage 2: per-page/global bounded assembly and quality signals
Stage 3: conditional pdftotext -layout fallback for quality-risk items
Stage 4: unresolved review queue for items still garbled
```

这不是 Gate 2C 可直接接受的 universal Evidence Contract。对于当前 Probe 无法解决的
乱码样本，Evidence v0.3 必须另行设计 visual/OCR fallback；本次不执行 OCR 或全量双重抽取。

## 11. Gate 2B Status

```text
Evidence v0.2 Contract: Conditional Design Freeze
Evidence v0.2: Not accepted as a universal Gate 2C input
Gate 2B operational status: HOLD
Gate 2C: NOT AUTHORIZED
```

后续若要重新运行，必须：

- 复用同一个 `calibration_sample_id`；
- 复用同一 767 个 `calibration_item_id`、`file_instance_id` 和 pool membership；
- 不覆盖 Evidence v0.1 Runtime Artifact；
- 使用本次完全相同的 20-item Main Review Set；
- 保持 `sufficient >= 18 / 20` 且 `insufficient <= 1 / 20`，不得降低阈值。

## 12. Final Stop Boundary

本次完成：

1. 4 个 Problem Set Item 的固定复核；
2. 4 个 deterministic Control Set Item 的回归复核；
3. Probe A、B、C；
4. Unicode quality metrics observation；
5. 每个问题项的 root cause classification；
6. Evidence v0.2 conditional design decision。

本次未完成且不得在本任务执行：

- Full 767-item Evidence v0.2 Runtime；
- OCR / MinerU / visual fallback；
- LLM Taxonomy Annotation；
- Source Selection；
- Gate 2C。
