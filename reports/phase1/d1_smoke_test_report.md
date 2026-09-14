# D1 Smoke Test Report

Project: Mechanical Industry General Benchmark
Phase: Phase 1 - Corpus Inventory
Milestone: Corpus Inventory v0.1
Report Status: Remote D1 Completed

## 1. Run Identity

| Field | Value |
| --- | --- |
| Run ID | `d1-20260914T060712Z-406473f` |
| Remote Git Commit | `406473f50df711da1f838642839a07f8209072b3` |
| Remote Repository | `/data/suzhe/Machinery-Industry-Benchmark` |
| Remote Host | `xuelangyun` |
| SSH Alias | `migb` |
| Source Root | `/mnt/data_nfs/dataset/original/cmes/journal` |
| MIGB_DATA_ROOT | `/data/suzhe/migb` |

The local implementation was committed in `5f8ecb3` and the report/progress baseline in `406473f`.
The remote checkout contains both commits and was clean before the run. The initial HTTPS clone was
not available because the remote server had no GitHub credentials; the exact local Git checkout was
synchronized to the confirmed remote repository path without using a password.

## 2. Remote Environment and D1 Configuration

| Field | Value |
| --- | --- |
| Sample method | `first_by_sorted_relative_path_per_parent_group` |
| Sample count | 20 PDFs |
| Worker count | 4 |
| PDF baseline | PyMuPDF lightweight inspection |
| Remote Python | 3.10.12 |
| PyMuPDF | 1.28.2 |
| PyArrow | 21.0.0 |
| PyYAML | 6.0.3 |
| Discovered PDF count | 60,454 |
| Source access policy | read-only |
| `/data` filesystem | ext4 |
| `/data` available at preflight | 2,952,689,577,984 bytes |

Configuration was loaded from `configs/environments/xuelangyun.yaml`. The run used the configured
`MIGB_DATA_ROOT` and `worker_count=4`.

## 3. Local Validation

- `pytest`: 29 passed.
- Local tests use only synthetic/tiny PDFs under pytest temporary directories.
- Local end-to-end coverage wrote all six D1 artifact types and verified explicit Parquet schemas,
  including zero-row `errors.parquet` and `duplicate_groups.parquet` cases.
- Local tests covered source/output path overlap rejection and source file list preservation.

## 4. Remote Status Results

| `inventory_status` | Count |
| --- | ---: |
| `success` | 20 |
| `partial` | 0 |
| `failed` | 0 |

`processed_count=20` and `sampled_count=20`. All sampled records had
`source_changed_during_run=false`.

## 5. Errors, PDF, Text-layer, and Filename Results

| Result | Distribution |
| --- | --- |
| Error count | 0 |
| Error categories | None |
| `pdf_status` | `valid`: 20; `encrypted`: 0 |
| `pdf_open_status` | `success`: 20; `failed`: 0 |
| `text_layer_status` | `text_present`: 15; `text_absent`: 5; `mixed_or_uncertain`: 0; `check_failed`: 0 |
| `filename_parse_status` | `matched`: 16; `unmatched`: 4; `error`: 0 |
| Exact duplicate groups | 0 |
| Exact duplicate files | 0 |

`errors.parquet` and `duplicate_groups.parquet` both contain zero rows with their fixed schemas.
`text_absent` records were treated as observed Corpus signals, not as Pipeline failures.

## 6. Throughput

| Metric | Value |
| --- | ---: |
| Total bytes | 89,691,213 |
| Wall time | 4.903361081145704 s |
| Files/sec | 4.0788348377816925 |
| MiB/sec | 17.444402896275435 |

## 7. Source Safety and Consistency

- Output Path Safety Check passed before any output directory was created.
- `/data/suzhe` was writable and `/data/suzhe/migb` was created only after the safety check.
- Source Root remained `/mnt/data_nfs/dataset/original/cmes/journal` with read-only operational policy.
- No Source PDF was renamed, moved, OCR'd, parsed by MinerU, or written to by this run.
- Current size/mtime of all 20 sampled files matched the recorded pre-task values; external mismatch
  count was 0.

## 8. Artifact Validation

Artifact directory:

```text
/data/suzhe/migb/inventory/runs/d1-20260914T060712Z-406473f
```

All six required Artifacts exist and are readable:

| Artifact | Validation |
| --- | --- |
| `files.parquet` | 20 rows; explicit Schema passed |
| `duplicate_groups.parquet` | 0 rows; explicit Schema passed |
| `errors.parquet` | 0 rows; explicit Schema passed |
| `sample_manifest.json` | JSON valid; 20 items; sampling method passed |
| `manifest.json` | Required fields passed; `dirty=false`; host and commit passed |
| `statistics.json` | Counts and throughput fields passed |

The manifest records `hostname=xuelangyun`, `git_commit=406473f...`, `dirty=false`,
`source_safety_check=passed`, and `worker_count=4`. The full six-Artifact directory was copied to a
Mac temporary directory for review and was not added to Git.

## 9. Issues and Required Fixes

No D1 correctness, safety, accounting, schema, provenance, or Source Consistency issue was found.
The CLI was invoked with `PYTHONPATH=src` because the remote `.venv` contains dependencies but does
not install the package as a site-package; this is an operational invocation note, not an Artifact
failure. Before D2, package installation or the invocation convention should be standardized.

No blocking fix is required before D1 acceptance. D2 remains unauthorized in this task.

## 10. D1 Verdict

**PASS**
