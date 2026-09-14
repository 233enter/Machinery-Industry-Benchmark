# D2 Representative Dry-run Report

Project: Mechanical Industry General Benchmark
Phase: Phase 1 - Corpus Inventory
Milestone: Corpus Inventory v0.1
Report Status: Remote D2 Completed

## 1. Run Identity

| Field | Value |
| --- | --- |
| Run ID | `d2-20260914T062102Z-18a5aad` |
| D2 Git Commit | `18a5aada4e752d0a86839bdcc4331b21e557ce44` |
| Remote Repository | `/data/suzhe/Machinery-Industry-Benchmark` |
| Remote Host | `xuelangyun` |
| SSH Alias | `migb` |
| Source Root | `/mnt/data_nfs/dataset/original/cmes/journal` |
| MIGB_DATA_ROOT | `/data/suzhe/migb` |
| Remote Python | 3.10.12 |
| PyMuPDF | 1.28.2 |
| PyArrow | 21.0.0 |
| PyYAML | 6.0.3 |
| Worker count | 4 |
| Git dirty state | `false` |

The D2 run used the clean D2 implementation commit. The project package was installed in the
remote project-local `.venv` with `pip install -e .`; `python -m migb.inventory.cli` ran without
`PYTHONPATH=src`.

## 2. Packaging Standardization and Regression Gates

- Local editable install passed and `import migb` resolved to the project `src/migb` package.
- Remote editable install passed and `import migb` resolved to
  `/data/suzhe/Machinery-Industry-Benchmark/src/migb/__init__.py`.
- Local pytest: 33 passed.
- Remote pytest: 33 passed.
- The `.venv/` and editable-install `*.egg-info/` outputs are ignored by Git.

## 3. Sampling Design and Accounting

| Field | Value |
| --- | --- |
| Sampling stage | `d2` |
| Sampling method | `evenly_spaced_sorted_relative_path_per_parent_group_excluding_d1` |
| Target per group | 10 PDFs |
| Target sample count | 200 PDFs |
| Actual sample count | 198 PDFs |
| D1 prior Run | `d1-20260914T060712Z-406473f` |
| D1 items excluded | 20 found; 0 missing |
| D1/D2 sample overlap | 0 |
| Deterministic re-computation | Passed |

For each Source Group, D2 sorted POSIX `relative_path`, excluded the D1 File Instance IDs, and
selected evenly spaced indexes including the first and last remaining records. The input snapshot,
algorithm, and output list were independently recomputed and matched exactly.

The target of 200 was not force-filled. `suxinggongchengxuebao` had only 8 eligible PDFs after D1
exclusion, so the actual total was 198. All other 19 groups contributed 10 PDFs.

## 4. Per-group Sample and Signal Distribution

| Parent Group | Sample | Text Present | Text Absent | Mixed | Check Failed | Filename Matched | Filename Unmatched | Filename Error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| duanyajishu | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| hanjie | 10 | 10 | 0 | 0 | 0 | 9 | 1 | 0 |
| hanjiexuebao | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| jinshurechuli | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| jixiechuandong | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| jixiegongchengcailiao | 10 | 10 | 0 | 0 | 0 | 3 | 7 | 0 |
| jixiegongchengxuebao | 10 | 8 | 2 | 0 | 0 | 6 | 4 | 0 |
| jixiegongchengxuebao2 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| jixieqiangdu | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| lihuajianyan-huaxuefence | 10 | 9 | 1 | 0 | 0 | 10 | 0 | 0 |
| lihuajianyan-wulifence | 10 | 8 | 2 | 0 | 0 | 10 | 0 | 0 |
| suxinggongchengxuebao | 8 | 5 | 0 | 0 | 3 | 8 | 0 | 0 |
| wusunjiance | 10 | 8 | 2 | 0 | 0 | 10 | 0 | 0 |
| yeyayuqidong | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |
| zhizaojishuyujichuang | 10 | 5 | 5 | 0 | 0 | 9 | 1 | 0 |
| zhizaoyezidonghua | 10 | 6 | 4 | 0 | 0 | 10 | 0 | 0 |
| zhongguohanjie | 10 | 9 | 1 | 0 | 0 | 8 | 2 | 0 |
| zhongguojixiegongcheng | 10 | 10 | 0 | 0 | 0 | 9 | 1 | 0 |
| zhongguozhuzaozhuangbeiyujishu | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| zhuzao | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 |

Aggregate distribution:

```text
text_present: 178
text_absent: 17
mixed_or_uncertain: 0
check_failed: 3

filename_matched: 162
filename_unmatched: 36
filename_error: 0
```

## 5. Error Analysis

`errors.parquet` contains 3 rows. All three are in `suxinggongchengxuebao` and have the same
controlled condition:

| File Instance ID | Relative Path | Stage | Error Category | Interpretation |
| --- | --- | --- | --- | --- |
| `9f08077a-5387-570b-bec4-c183964c7041` | `suxinggongchengxuebao/【2026-06】十八辊精密轧机辊系非自稳定行为分析及高效控制策略研究.pdf` | `text_sample` | `zero_page_count` | PDF opened, but had no readable pages for the text check |
| `362a1eda-97e2-5000-92d3-58cbc32bbe99` | `suxinggongchengxuebao/【2026-06】立辊减宽和定宽机减宽对板厚均匀性的影响.pdf` | `text_sample` | `zero_page_count` | PDF opened, but had no readable pages for the text check |
| `96e2b8db-a59c-56fa-a891-764b2b770962` | `suxinggongchengxuebao/【2026-06】铜_铝异质薄壁管冷滚压连接成形锁头截面圆度分析.pdf` | `text_sample` | `zero_page_count` | PDF opened, but had no readable pages for the text check |

These records were retained as `inventory_status=partial` and `text_layer_status=check_failed`.
There were no hash, PDF open, worker, or Source Consistency errors. This is treated as an observed
Corpus/PDF condition, not a silent skip or an unexplained Pipeline failure.

## 6. PDF, Filename, and File-size Results

```text
pdf_open_status: success=198, failed=0
pdf_status: valid=198, encrypted=0

file size bytes:
  min: 102,970
  median: 2,202,836
  p90: 11,145,930.3
  max: 227,688,028

page_count:
  min: 0
  median: 6
  p90: 10
  max: 17
```

The three zero-page records account for the `page_count=min=0` and `check_failed=3` observations.

Unmatched filename examples (sampled for pattern review; the parser was not expanded):

| Parent Group | Filename |
| --- | --- |
| hanjie | `预热温度对U75V激光熔覆成形性能的影响.pdf` |
| jixiegongchengcailiao | `【2020-8】激光选区熔化成形TC4钛合金显微组织与性能的研究进展.pdf` |
| jixiegongchengcailiao | `【2021-5】铜合金镶嵌石墨材料的摩擦磨损性能.pdf` |
| jixiegongchengcailiao | `【2022-3】某火电机组三连杆恒力弹簧支吊架弹簧拉杆断裂原因.pdf` |
| jixiegongchengcailiao | `【2023-1】均匀化退火对Mg-4Zn-4Y合金显微组织和力学性能的影响.pdf` |
| jixiegongchengcailiao | `【2024-8】火焰喷涂纯锌和Zn-Al合金涂层的耐腐蚀性能.pdf` |
| jixiegongchengcailiao | `【2025-6】退火时间对C-Mn-Nb-Ti系深冲双相钢组织与性能的影响.pdf` |
| jixiegongchengcailiao | `【2026-5】高铬双金属耐磨板堆焊层的组织与滑动摩擦磨损性能.pdf` |
| jixiegongchengxuebao | `【2005-6】湿型砂质量参数智能测试车的研制.pdf` |
| jixiegongchengxuebao | `【2016-7】复杂零件结构设计的概念单元方法.pdf` |

The examples include one-digit issue values such as `2020-8`, which correctly remain unmatched by
the frozen `YYYY-MM` pattern. No Regex change was made during D2.

## 7. Duplicate Result

```text
exact_duplicate_group_count: 0
exact_duplicate_file_count: 0
```

`duplicate_groups.parquet` was still produced with its compatible explicit Schema and zero rows.

## 8. Throughput and D1 Comparison

| Metric | D1 | D2 |
| --- | ---: | ---: |
| Sampled files | 20 | 198 |
| Total bytes | 89,691,213 | 1,042,656,543 |
| Wall time | 4.903361081145704 s | 18.54009956214577 s |
| Files/sec | 4.0788348377816925 | 10.679554299927618 |
| MiB/sec | 17.444402896275435 | 53.63265512997847 |
| Worker count | 4 | 4 |

This is an operational comparison only. D1 and D2 use different file compositions and sample sizes,
so the values are not a strict performance benchmark and do not justify increasing workers before
D3 review.

## 9. Source Safety and Consistency

- Output Path Safety Check passed before creating the D2 Run Directory.
- D2 output is under `/data/suzhe/migb`; the Source Root remained read-only by project policy.
- All 198 records have `source_changed_during_run=false`.
- Current size/mtime comparison for all 198 sampled files produced 0 mismatches.
- D1 Run Directory was not modified; all six pre-D2 D1 Artifact SHA-256 values remained unchanged.
- No Source PDF was renamed, moved, OCR'd, processed by MinerU, or written to.

## 10. Artifact Validation

Artifact directory:

```text
/data/suzhe/migb/inventory/runs/d2-20260914T062102Z-18a5aad
```

All six Artifacts exist and are readable:

| Artifact | Validation |
| --- | --- |
| `files.parquet` | 198 rows; `files.parquet` rows equal actual sample count; explicit compatible Schema passed |
| `duplicate_groups.parquet` | 0 rows; explicit Schema passed |
| `errors.parquet` | 3 rows; explicit Schema passed |
| `sample_manifest.json` | JSON valid; target/actual/per-group counts and D1 exclusion passed |
| `manifest.json` | Required provenance and D2 sampling fields passed; `dirty=false` |
| `statistics.json` | Status, text, filename, duplicate, and throughput counts passed |

The runtime used the unchanged compatible `inventory_schema_version=d1-v0.1`. A copy of the six
Artifacts was pulled to the Mac temporary directory
`/tmp/migb-d2-review.TY3uJl/d2-20260914T062102Z-18a5aad` for review and was not added to Git.

## 11. Issues and Required Fixes

Observed non-blocking conditions:

1. Actual sample count is 198 rather than the target 200 because one Source Group had only 8
   eligible PDFs after D1 exclusion.
2. Three PDFs produced the recorded `zero_page_count` text-sampling condition and were retained as
   partial records.
3. The remote HTTPS GitHub clone/pull path has no credentials. This run used the confirmed local
   Git checkout synchronization method; no password was used.

No D2 Pipeline correctness, safety, determinism, accounting, Schema, provenance, or Source
Consistency fix is required before D2 acceptance. The first two conditions should be considered in
D3 planning; Git authentication or the approved repository synchronization procedure should be
standardized for future remote updates.

## 12. D2 Verdict

**PASS**

D2 is complete. Stop here for D2 Gate Review; do not start D3 until explicitly authorized.
