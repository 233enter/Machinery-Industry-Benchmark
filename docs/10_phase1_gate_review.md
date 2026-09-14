# Phase 1 Gate Review

Project: Mechanical Industry General Benchmark
Version: 0.1
Status: Reviewed - Phase 1 Passed
Phase: Phase 1 - Corpus Inventory
Current Task: Phase 1 Gate Closeout

## 1. Gate Review 结论

| Gate / Review Item | Result |
| --- | --- |
| `cmes_journal` Full Inventory Gate | **PASSED** |
| Phase 1 Inventory Engineering Gate | **PASSED** |
| Candidate Source Corpus Scope Decision | **CONFIRMED - Case A** |
| Project-wide Phase 1 Closeout | **PASSED** |
| Gate 1 | **PASSED** |
| Phase 1 Status | **CLOSED** |
| Phase 2 Authorization | Status transition only; Phase 2 work not started |

项目 Owner 已确认：当前 MIGB 项目的完整 Candidate Source Corpus 只有
`cmes_journal`。历史 `approximately 70k PDFs` 是项目背景中的近似估计，不是 authoritative
corpus count；当前项目的 authoritative Candidate Source Corpus 是
`cmes_journal` 下的 60454 个 PDF。

## 2. 已完成的 Phase 1 工程验收项

| Item | Result |
| --- | --- |
| Environment Intake | **Passed** |
| Source Safety | **Passed** |
| D1 Smoke Test | **Passed** |
| D2 Representative Dry-run | **Passed** |
| D3 Scale Test | **Passed** |
| Checkpoint / Resume | **Passed** |
| Full Inventory | **Passed** |
| Full Artifact Validation | **Passed** |
| Source Snapshot Consistency | **Passed** |
| Historical Artifact Integrity | **Passed** |

Full Canonical Run：`full-20260914T075902Z-faa4565`。

| Full Inventory Metric | Value |
| --- | ---: |
| Selected | 60454 |
| Processed | 60454 |
| Success | 60447 |
| Partial | 7 |
| Failed | 0 |

完整运行指标、Artifact checksum 和错误明细见：
`reports/phase1/full_inventory_report.md`。

## 3. 当前已确认的 Inventory Scope

| Field | Value |
| --- | --- |
| `source_root_id` | `cmes_journal` |
| Source Root | `/mnt/data_nfs/dataset/original/cmes/journal` |
| Authoritative PDF count | `60454` |
| Top-level group count | `20` |
| Total size | `241371609617` bytes（约 224.79 GiB） |
| Current status | Inventoried |

该记录同时是当前项目的 Project-wide Candidate Source Corpus Canonical Record。60454 是
Corpus physical File Instance count，不应替换为 60447 success；其中 60447 success、7
partial、0 failed。

### Phase 1 Canonical Corpus Record

| Field | Value |
| --- | --- |
| Corpus ID / Source Root ID | `cmes_journal` |
| Location | `/mnt/data_nfs/dataset/original/cmes/journal` |
| PDF Count | `60454` |
| Total Bytes | `241371609617` |
| Top-level Source Groups | `20` |
| Inventory Run | `full-20260914T075902Z-faa4565` |
| Inventory Schema | `inventory-v0.2` |

## 4. Read-only Source Scope Discovery

本轮只读检查范围为：

```text
/mnt/data_nfs/dataset/original/cmes
/mnt/data_nfs/dataset/original
```

`/mnt/data_nfs/dataset/original/cmes` 下观察到的结构只有：

```text
cmes/
└── journal/
```

必要的一级目录检查显示：

```text
all_pipeline/
books_assemble/
books_assemble_fail_download_0314/
books_blueprint/
books_blueprint_1/
cmes/
```

统计使用 Python structured traversal，只记录 regular file、PDF / non-PDF 数量和 regular
file bytes；没有执行 SHA-256、PDF page scan、PDF parser、OCR、MinerU 或任何写操作。

### 4.1 Observed Source Candidates

以下目录曾被标记为 `Observed Source Candidate`。根据项目 Owner 的正式 Scope Decision，
四个 `books_*` 目录均不是当前 MIGB Candidate Source Corpus，也不是 Registered MIGB
Candidate Source Root。`approx size` 为本轮只读统计到的 regular file bytes，仅作为审计
记录保留。

| Source candidate | Path | Regular files | PDFs | Non-PDF | Approx size | Top-level structure | Current status |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `cmes_journal` | `/mnt/data_nfs/dataset/original/cmes/journal` | 60454 | 60454 | 0 | 241371609617 bytes（约 224.79 GiB） | 20 个一级目录 | Inventoried |
| `books_assemble` | `/mnt/data_nfs/dataset/original/books_assemble` | 1880 | 1629 | 251 | 49462774311 bytes（约 46.07 GiB） | 1880 个直接文件条目；2 个目录：`pdf_rebuild_er7bnzx9`、`pdf_rebuild_lzkz9k_p` | Excluded from current MIGB scope |
| `books_assemble_fail_download_0314` | `/mnt/data_nfs/dataset/original/books_assemble_fail_download_0314` | 257 | 229 | 28 | 13483673117 bytes（约 12.56 GiB） | 平铺文件目录 | Excluded from current MIGB scope |
| `books_blueprint` | `/mnt/data_nfs/dataset/original/books_blueprint` | 230 | 198 | 32 | 9940556714 bytes（约 9.26 GiB） | 平铺文件目录 | Excluded from current MIGB scope |
| `books_blueprint_1` | `/mnt/data_nfs/dataset/original/books_blueprint_1` | 241 | 213 | 28 | 7546306518 bytes（约 7.03 GiB） | 平铺文件目录 | Excluded from current MIGB scope |

四个未纳入当前 `cmes_journal` Inventory 的 `books_*` 目录合计观察到 2269 个 PDF、2608
个 regular files，regular file bytes 合计 `80433310660`（约 74.91 GiB）。该合计只用于
历史范围核对；根据 Owner Decision，它们不纳入当前 MIGB Candidate Source Corpus，不注册
新的 `source_root_id`，不运行 Intake 或 Inventory，也不进入 Phase 2 Source Selection 输入。

### 4.2 Observed Related Workspace

`/mnt/data_nfs/dataset/original/all_pipeline` 的直接结构为：

```text
.env.example
.venv/
books/
new_pipeline/
papers/
pp/
unified_pipeline_delivery_V9/
```

其中 `books/` 和 `papers/` 进一步观察到 `logs/`、`manifest.json`、`mineru_out/`，同时该
目录还包含 `.venv`、代码和 pipeline 目录。因此 `all_pipeline` 不是当前 MIGB Candidate
Source Corpus，也不注册成 Source Root；其派生目录的文件数量不解释为 Candidate Source
Corpus 数量。本次没有对这些派生目录做完整递归计数。

## 5. 与历史 approximately 70k 估计的关系

Owner Decision 后，当前项目范围结论为：

1. `cmes_journal` 是当前 MIGB 项目的完整 Candidate Source Corpus，authoritative count 为
   60454 PDFs。
2. 四个 `books_*` 目录是 Observed external / adjacent source data，不属于当前 MIGB
   Candidate Source Corpus，也不是 Registered MIGB Candidate Source Roots。
3. `all_pipeline` 是混合 pipeline 工作区，不属于当前 MIGB Candidate Source Corpus，也不
   注册成 Source Root。
4. 历史 approximately 70k 是近似项目背景估计，不覆盖当前 authoritative scope decision。

因此，项目级 Candidate Source Corpus Scope 已由 Owner 确认，不再存在阻塞 Phase 1 Closeout
的范围问题；不需要为历史近似值补充或盘点其他目录。

## 6. Scope Decision Closeout

项目 Owner 正式确认：

```text
Candidate Source Corpus Scope Decision: CONFIRMED
Decision: Case A

source_root_id: cmes_journal
source_root: /mnt/data_nfs/dataset/original/cmes/journal
authoritative PDF count: 60454
```

正式范围说明：

```text
The historical "~70k PDFs" value was an approximate project-background estimate.
It is not the authoritative corpus count.
For the current MIGB project, the authoritative Candidate Source Corpus consists
of the 60,454 PDFs under cmes_journal.
```

`books_*` 目录不注册新的 `source_root_id`，不运行 Intake / Inventory，不纳入 60454 count，
不阻塞 Phase 1 Closeout，也不进入 Phase 2 Source Selection 输入。`all_pipeline` 继续保持
`NOT Candidate Source Corpus`。

## 7. Scope Decision 与下一步

最终采用 **Case A - Phase 1 Scope Decision: CONFIRMED**：

- Project-wide Phase 1 Closeout：**PASSED**；
- `Gate 1: PASSED`；
- `Phase 1 - Corpus Inventory: CLOSED`；
- 项目状态切换到 `Phase 2 - Taxonomy Calibration & Source Selection`；
- 仅完成状态切换，不执行任何 Phase 2 实际工作。

Phase 2 的实际工作仍需后续单独授权和执行。本次不进行 Domain Classification、Source
Selection、Taxonomy Calibration、Parser、OCR、MinerU、LLM 或任何数据处理。
