# D1 Smoke Test Report

Project: Mechanical Industry General Benchmark
Phase: Phase 1 - Corpus Inventory
Milestone: Corpus Inventory v0.1
Report Status: Remote D1 Not Run - Awaiting Repository Path

## 1. Run Identity

| Field | Value |
| --- | --- |
| Run ID | Not generated; Remote D1 was not started |
| Local Git Commit | `5f8ecb3` |
| Remote Host | `xuelangyun` |
| SSH Alias | `migb` |
| Source Root | `/mnt/data_nfs/dataset/original/cmes/journal` |
| MIGB_DATA_ROOT | `/data/suzhe/migb` |

The local implementation and tests were completed from commit `5f8ecb3`. The remote SSH Gate
returned `xuelangyun`. A project checkout was not found in the inspected remote locations, and no
safe target directory for cloning was provided or established. Therefore no remote run was started.

## 2. Intended D1 Configuration

| Field | Value |
| --- | --- |
| Sample method | `first_by_sorted_relative_path_per_parent_group` |
| Intended sample count | 20 PDFs |
| Worker count | 4 |
| PDF baseline | PyMuPDF lightweight inspection |
| Source access policy | read-only |

The intended values come from `configs/environments/xuelangyun.yaml`. They are not remote run
results.

## 3. Local Validation

- `pytest`: 29 passed.
- Local tests use only synthetic/tiny PDFs under pytest temporary directories.
- Local end-to-end coverage wrote all six D1 artifact types and verified explicit Parquet schemas,
  including zero-row `errors.parquet` and `duplicate_groups.parquet` cases.
- Local tests covered source/output path overlap rejection and source file list preservation.

## 4. Remote D1 Results

The following fields are not applicable because Remote D1 did not run:

- Sample Count: N/A
- Success / Partial / Failure: N/A
- Errors: N/A
- Throughput and Total Bytes: N/A
- PDF Status and Text-layer Distribution: N/A
- Filename Parse Distribution: N/A
- Exact Duplicates: N/A
- Remote Artifact Validation: N/A
- Source Consistency Result: N/A

No `/data/suzhe/migb` directory was created, and no remote Artifact Directory exists for this
attempt.

## 5. Blocker and Required Action

The remote server does not currently expose a confirmed checkout of this project in the inspected
locations. The repository path must be confirmed before the local commit can be synchronized and
the D1 CLI can be run. The implementation does not guess a clone target and does not place the Git
checkout under `MIGB_DATA_ROOT` without an explicit path decision.

Required before Remote D1:

1. Confirm the remote Git Repository checkout path, or explicitly authorize a target directory for
   cloning from the configured Git remote.
2. Synchronize/checkout commit `5f8ecb3` in that repository.
3. Verify the project-local Python environment and dependencies.
4. Re-run the Output Path Safety Check and confirm `/data/suzhe` is writable.
5. Run only D1 with 20 sampled PDFs and 4 workers, then validate all six artifacts.

## 6. D1 Verdict

**NOT RUN — BLOCKED BY UNCONFIRMED REMOTE REPOSITORY PATH**

This is an execution blocker, not a judgment on the D1 implementation or the real Candidate Source
Corpus. Current project progress remains `D1 Smoke Test Implementation`.
