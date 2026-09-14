# D3 Scale Test Report

Project: Mechanical Industry General Benchmark  
Phase: Phase 1 - Corpus Inventory  
Milestone: Corpus Inventory v0.1  
Report Status: Remote D3 Completed  
D3 Verdict: **PASS**

## 1. Run Identity

| Field | Value |
| --- | --- |
| Run ID | `d3-20260914T070000Z-ba05b05` |
| D3 Git Commit | `ba05b05f8530b2b3509c62ec1310a416846ba1b9` |
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

The remote project used its project-local `.venv` and `pip install -e .`. No source PDF was copied
into the Git Repository, and no output was written to the Source Corpus.

## 2. D2 Gate Closeout

`D2 Representative Dry-run: Passed` and `D2 Gate: Passed` were recorded before D3 execution.
D3 remained limited to the authorized Scale Test. Full Inventory, Phase 2, MinerU, OCR, LLM and GPU
workloads were not started.

## 3. Sampling Design and Accounting

| Field | Value |
| --- | --- |
| Sampling stage | `d3` |
| Sampling method | `proportional_parent_group_evenly_spaced_v0.1` |
| Target sample count | 1000 |
| Actual sample count | 1000 |
| D1 prior Run | `d1-20260914T060712Z-406473f` |
| D2 prior Run | `d2-20260914T062102Z-18a5aad` |
| D1 items excluded | 20 |
| D2 items excluded | 198 |
| Total prior items excluded | 218 |
| Remaining population after exclusions | 60,236 |
| Unique D3 File Instances | 1000 |
| D1/D2 overlap | 0 |
| D1/D3 overlap | 0 |
| D2/D3 overlap | 0 |

The prior D1 and D2 `sample_manifest.json` files were loaded and validated, including their File
Instance IDs. D3 sampling was independently recomputed from 60,454 discovered PDFs and matched the
persisted sample item order, sample manifest hash and per-group quotas exactly.

`proportional_quota` below is the integer floor of the proportional allocation over the remaining
capacity after `base_quota`; `largest_remainder_award` records the Hamilton remainder unit(s).

## 4. Per-group Population and Quota

| Parent Group | Remaining Population | Base Quota | Proportional Quota | Largest Remainder Award | Final Quota |
| --- | ---: | ---: | ---: | ---: | ---: |
| duanyajishu | 1,062 | 5 | 15 | 1 | 21 |
| hanjie | 1,386 | 5 | 20 | 1 | 26 |
| hanjiexuebao | 7,398 | 5 | 111 | 0 | 116 |
| jinshurechuli | 1,981 | 5 | 29 | 1 | 35 |
| jixiechuandong | 187 | 5 | 2 | 1 | 8 |
| jixiegongchengcailiao | 1,470 | 5 | 22 | 0 | 27 |
| jixiegongchengxuebao | 14,960 | 5 | 225 | 0 | 230 |
| jixiegongchengxuebao2 | 2,083 | 5 | 31 | 0 | 36 |
| jixieqiangdu | 2,489 | 5 | 37 | 0 | 42 |
| lihuajianyan-huaxuefence | 5,548 | 5 | 83 | 1 | 89 |
| lihuajianyan-wulifence | 3,647 | 5 | 54 | 1 | 60 |
| wusunjiance | 4,478 | 5 | 67 | 0 | 72 |
| yeyayuqidong | 4,131 | 5 | 62 | 0 | 67 |
| zhizaojishuyujichuang | 2,124 | 5 | 31 | 1 | 37 |
| zhizaoyezidonghua | 1,401 | 5 | 21 | 0 | 26 |
| zhongguohanjie | 532 | 5 | 7 | 1 | 13 |
| zhongguojixiegongcheng | 2,880 | 5 | 43 | 0 | 48 |
| zhongguozhuzaozhuangbeiyujishu | 1,067 | 5 | 15 | 1 | 21 |
| zhuzao | 1,412 | 5 | 21 | 0 | 26 |
| **Total** | **60,236** | **95** | **891** | **9** | **1,000** |

Within each group, POSIX `relative_path` was sorted and the final quota was selected with the
frozen deterministic evenly-spaced index rule. No runtime random source was used.

## 5. Pre-D3 `zero_page_count` Audit

The three D2 `zero_page_count` files were audited read-only before D3. The audit used the remote
project `.venv` PyMuPDF 1.28.2 and the already-installed `/usr/bin/pdfinfo`; no system package was
installed.

| Relative Path | Size (bytes) | mtime_ns | SHA-256 | PyMuPDF Open | Pages | Encrypted | needs_pass |
| --- | ---: | ---: | --- | --- | ---: | --- | --- |
| `suxinggongchengxuebao/【2026-06】十八辊精密轧机辊系非自稳定行为分析及高效控制策略研究.pdf` | 6,786,832 | 1785382231462548298 | `69453f033f5c19e2c51329c5975b826ec946281a0fda44adb009e7b7bd7a58a4` | success | 0 | false | false |
| `suxinggongchengxuebao/【2026-06】立辊减宽和定宽机减宽对板厚均匀性的影响.pdf` | 1,794,595 | 1785382231886548319 | `f0e43d71436cb1fe5345f1040805df7a98dababa48fa44797277964d1971a4f4` | success | 0 | false | false |
| `suxinggongchengxuebao/【2026-06】铜_铝异质薄壁管冷滚压连接成形锁头截面圆度分析.pdf` | 6,786,832 | 1785382231839548317 | `90316581dc7ece43f5fc5fd84aa4ac8fa102b6d3efe3f8b29f909b7404d74067` | success | 0 | false | false |

All three had PyMuPDF metadata `format=PDF 1.6`; the remaining inspected metadata values were empty
or null. `pdfinfo` was available and returned code 99 for all three, reporting an absent trailer or
invalid XRef entries, `Top-level pages object is wrong type (null)`, and a zero-page range error.
This independently confirms the zero-page condition. The `pdf_status` semantic was not changed:
an openable PDF and a usable page count remain separate signals.

## 6. Checkpoint Design and Controlled Stop

The D3 baseline used `checkpoint_batch_size=100`. Each checkpoint was written through a temporary
file, flush/fsync, close and same-directory atomic rename. File and error checkpoint parts were
written as matched pairs.

| Checkpoint Event | Result |
| --- | --- |
| Initial controlled run | `run_status=interrupted` |
| Initial completed count | 300 |
| Initial checkpoint parts | 3 files parts + 3 errors parts |
| Initial Canonical Artifacts | only `sample_manifest.json` existed; final Parquet/manifest/statistics did not yet exist |
| Resume run | same run ID, sample manifest and configuration accepted |
| Resume count | 1 |
| Checkpoint reused | 300 |
| Checkpoint reprocessed | 0 |
| Final checkpoint parts | 10 files parts + 10 errors parts |
| Final run state | `run_status=completed`, `completed_count=1000` |

The resume path reused the first 300 records after checking `file_instance_id`, `size_bytes` and
`mtime_ns`; it bypassed the file-processing task, so those records were not re-hashed or inspected
again. The final canonical record count is 1000 unique File Instances, not 1300. A completed run is
immutable; the local regression test also verifies that a completed run rejects `--resume`.

## 7. Retry Policy and Result

D3 allowed at most two retries (three total attempts) for bounded transient filesystem/NFS I/O
categories, with 0.5 s and 2 s backoff. Deterministic PDF conditions, `zero_page_count`, filename
unmatched, encrypted PDFs and schema errors were not retryable.

| Metric | Result |
| --- | ---: |
| `retry_attempts_total` | 0 |
| `files_recovered_by_retry` | 0 |

## 8. Status and Error Analysis

| Metric | Count |
| --- | ---: |
| Success | 1000 |
| Partial | 0 |
| Failed | 0 |
| Error rows | 0 |
| PDF open success | 1000 |
| PDF open failed | 0 |
| `pdf_status=valid` | 1000 |
| Encrypted | 0 |
| Exact duplicate groups | 0 |
| Exact duplicate files | 0 |

No D3 error stage/category was observed. The D3 sample had no `zero_page_count`; the three audited
D2 files were not in the D3 sample after prior-run exclusion.

## 9. Text-layer and Filename Distribution

| Text-layer status | Count |
| --- | ---: |
| `text_present` | 938 |
| `text_absent` | 58 |
| `mixed_or_uncertain` | 4 |
| `check_failed` | 0 |

| Filename parse status | Count |
| --- | ---: |
| `matched` | 799 |
| `unmatched` | 201 |
| `error` | 0 |

The frozen Filename Parser was used without expanding its regular expression during D3.

## 10. File-size and Page-count Statistics

| Statistic | File size (bytes) | Page count |
| --- | ---: | ---: |
| Minimum | 65,603 | 1 |
| Median | 1,418,180 | 6 |
| P90 | 6,955,934.6 | 10 |
| Maximum | 187,936,819 | 20 |

## 11. Throughput and D1/D2/D3 Operational Comparison

| Metric | D1 | D2 | D3 |
| --- | ---: | ---: | ---: |
| Sampled files | 20 | 198 | 1000 |
| Total bytes | 89,691,213 | 1,042,656,543 | 4,184,642,835 |
| Wall time (s) | 4.903361 | 18.540100 | 65.000224 |
| Files/s | 4.078835 | 10.679554 | 15.384562 |
| MiB/s | 17.444403 | 53.632655 | 61.396502 |
| Worker count | 4 | 4 | 4 |

D3 `wall_time_seconds`, `files_per_second` and `mib_per_second` are the final resume/finalization
invocation statistics, while its initial controlled invocation took 24.185209 s. Therefore the
observed end-to-end elapsed time across both D3 invocations was approximately 89.185433 s. The
checkpoint write time accumulated across both invocations was 7.460928 s and resume startup time
was 2.648134 s. These are operational observations for this sample composition, not a claim about
NFS maximum throughput.

## 12. Source Safety and Source Consistency

- Output Path Safety Check passed immediately before D3.
- Source Root remained `/mnt/data_nfs/dataset/original/cmes/journal` and was treated as read-only.
- `source_changed_during_run=false` for D1, D2 and all 1000 D3 records.
- No Source PDF was renamed, moved, deleted, OCR'd, processed by MinerU or written to.
- D3 output remained under `/data/suzhe/migb`, physically/logically separate from the Source Root.
- The `/data/suzhe/migb` path was not added to Git.

## 13. D1/D2 Artifact Integrity

The six D1 and six D2 Artifact SHA-256 values were captured before D3 and matched after D3. All
entries below are `unchanged=true`:

| Prior Run | Result |
| --- | --- |
| `d1-20260914T060712Z-406473f` | 6/6 unchanged |
| `d2-20260914T062102Z-18a5aad` | 6/6 unchanged |

## 14. D3 Canonical Artifact Checksums

Canonical artifact directory:

```text
/data/suzhe/migb/inventory/runs/d3-20260914T070000Z-ba05b05
```

The manifest records `path`, `size_bytes` and `sha256` for all six Canonical Artifacts. The five
non-manifest artifact checksums match their raw file SHA-256 values. Because a file cannot contain
the raw SHA-256 of its own final bytes, the `manifest.json` descriptor uses the explicitly recorded
normalization `manifest.json with its own sha256 normalized to 64 zeroes`.

| Artifact | Raw SHA-256 observed after completion |
| --- | --- |
| `files.parquet` | `178b241e7f6636149f0969415ddff3fc0d7fa1ffdc49c111832b87d240d7e55c` |
| `duplicate_groups.parquet` | `4cc6430cb3b1e7a3ada72a27583f43cbf488a0d07cedb4957e69c7bfc1a6a1ba` |
| `errors.parquet` | `ebb37e490423542c5b410447ffe8e6fb24e910169229e38e36024e291d54958f` |
| `sample_manifest.json` | `f6a4c127661377e8578d4dd3d517091915f00c74ba0a55941d9ddae3d12e78e0` |
| `manifest.json` | `07b6a4064f6be64bf54ab985336a8fd6fa28bc1f3aafa29b3a6054332fb629de` |
| `statistics.json` | `d754d7ce3b4afee3993321970bdcb275fecd442c886637ca5cfb63ad3edcb229` |

Independent verification returned `size_matches=true` and checksum verification true for all
non-manifest artifacts; the normalized manifest checksum also passed.

## 15. Artifact Validation

- `files.parquet`: 1000 rows; explicit compatible Schema passed.
- `duplicate_groups.parquet`: 0 rows; explicit Schema passed.
- `errors.parquet`: 0 rows; explicit Schema passed.
- `sample_manifest.json`: 1000 items; target/actual and per-group quota accounting passed.
- `manifest.json`: required provenance, D3 sampling, retry, resume and checksum fields passed;
  `dirty=false`.
- `statistics.json`: status, text-layer, filename, duplicate, retry and throughput fields passed.
- Checkpoint files: 1000 rows across 10 parts; checkpoint error parts were valid zero-row Parquet.

## 16. Issues and Required Fixes

No D3 correctness, sampling, exclusion, restartability, Source Safety, Schema, provenance or
Artifact accounting failure was found.

The following remain observations for later review rather than D3 blockers:

1. D2's three zero-page PDFs remain `pdf_status=valid` with `inventory_status=partial` and
   `text_layer_status=check_failed`; the semantic question was intentionally not changed in D3.
2. D3's throughput fields describe the final resume invocation; the initial controlled-stop timing
   is recorded separately above.
3. The remote HTTPS Git operation still lacks usable credentials; the approved local push plus
   remote checkout synchronization procedure was used, without storing a password or key.

## 17. D3 Verdict

**PASS**

D3 satisfied the authorized Scale Test conditions: 1000 deterministic samples, valid D1/D2
exclusion, reproducible quotas, clean remote provenance, four-worker execution, durable paired
checkpoints, successful controlled interruption and resume with 300 reused records, valid six
Canonical Artifacts, matching checksums, no Source Consistency changes and no unexplained Pipeline
failure.

Stop here for Full Inventory Gate Review. Do not start Full Inventory automatically.
