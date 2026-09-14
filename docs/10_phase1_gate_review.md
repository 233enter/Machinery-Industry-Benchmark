# Phase 1 Gate Review

Project: Mechanical Industry General Benchmark
Version: 0.1
Status: Pending Scope Confirmation
Phase: Phase 1 - Corpus Inventory
Current Task: Candidate Source Corpus Scope Confirmation

## 1. Gate Review 结论

| Gate / Review Item | Result |
| --- | --- |
| `cmes_journal` Full Inventory Gate | **PASSED** |
| Phase 1 Inventory Engineering Gate | **PASSED** |
| Project-wide Phase 1 Closeout | **PENDING Candidate Source Corpus Scope Confirmation** |
| Scope Decision | **Case C - NEEDS OWNER CONFIRMATION** |
| Phase 2 Authorization | Not authorized |

当前 `cmes_journal` 的 Inventory 工程工作已经完成并通过验收，但项目级 Phase 1 是否可以
关闭，取决于确认该 Source Root 与项目历史所称 approximately 70k mechanical-industry PDFs
之间的关系。当前不能把 `60454 == complete project Candidate Source Corpus`，也不能把差额
直接解释为一定存在约 10k 个 missing PDFs。

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

这表示当前 Root 的 Full Inventory 已完成，不表示项目级 Complete Candidate Source Corpus 的
范围已经确定。

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

以下目录仅标记为 `Observed Source Candidate`，不代表已经决定属于 MIGB Candidate Source
Corpus。`approx size` 为本轮只读统计到的 regular file bytes。

| Source candidate | Path | Regular files | PDFs | Non-PDF | Approx size | Top-level structure | Current status |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `cmes_journal` | `/mnt/data_nfs/dataset/original/cmes/journal` | 60454 | 60454 | 0 | 241371609617 bytes（约 224.79 GiB） | 20 个一级目录 | Inventoried |
| `books_assemble` | `/mnt/data_nfs/dataset/original/books_assemble` | 1880 | 1629 | 251 | 49462774311 bytes（约 46.07 GiB） | 1880 个直接文件条目；2 个目录：`pdf_rebuild_er7bnzx9`、`pdf_rebuild_lzkz9k_p` | Scope TBD |
| `books_assemble_fail_download_0314` | `/mnt/data_nfs/dataset/original/books_assemble_fail_download_0314` | 257 | 229 | 28 | 13483673117 bytes（约 12.56 GiB） | 平铺文件目录 | Scope TBD |
| `books_blueprint` | `/mnt/data_nfs/dataset/original/books_blueprint` | 230 | 198 | 32 | 9940556714 bytes（约 9.26 GiB） | 平铺文件目录 | Scope TBD |
| `books_blueprint_1` | `/mnt/data_nfs/dataset/original/books_blueprint_1` | 241 | 213 | 28 | 7546306518 bytes（约 7.03 GiB） | 平铺文件目录 | Scope TBD |

四个未纳入当前 `cmes_journal` Inventory 的 `books_*` 目录合计观察到 2269 个 PDF、2608
个 regular files，regular file bytes 合计 `80433310660`（约 74.91 GiB）。该合计只用于
范围核对，不是 Source Selection 结果，也不是项目级 Corpus 总量结论。

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
目录还包含 `.venv`、代码和 pipeline 目录。因此本轮不把整个 `all_pipeline` 作为 Source
Root，也不把其中派生目录的文件数量解释为 Candidate Source Corpus 数量；其 Source Scope
状态保持 `TBD`。没有对这些派生目录做完整递归计数。

## 5. 与历史 approximately 70k 估计的关系

当前证据只能得到：

1. 已确认并完成 Inventory 的 `cmes_journal` 为 60454 PDFs。
2. 另外观察到四个名称上可能相关的 `books_*` 目录，共 2269 PDFs，但尚未确认它们属于
   当前 MIGB 项目范围。
3. 若仅作算术相加，60454 + 2269 = 62723；这仍不能证明项目总量，也不能证明剩余差额
   的来源。
4. `all_pipeline` 是混合 pipeline 工作区，不能把其 `books/`、`papers/` 或 `mineru_out/`
   的潜在文件直接当作新增 Source Root。
5. 历史 approximately 70k 仍可能是近似估计、不同目录集合的估计，或包含尚未注册的其他
   Source Root；目前没有足够证据选择其中任何解释。

因此，本轮确实发现了可能解释部分数量差异的目录，但没有解决项目级范围问题，也没有
证明一定存在约 10k 个缺失 PDF。

## 6. 当前唯一 Gate Issue：Candidate Source Corpus Scope

需要项目负责人确认：

1. `cmes_journal` 是否就是当前 MIGB 项目的完整 Candidate Source Corpus。
2. `books_assemble`、`books_assemble_fail_download_0314`、`books_blueprint`、
   `books_blueprint_1` 是否属于项目范围。
3. `all_pipeline/books` 和 `all_pipeline/papers` 是 Source、派生工作区，还是历史 pipeline
   输出。
4. 历史 approximately 70k 的统计口径、目录范围和是否包含重复 / 非 PDF 文件。
5. 项目级 Candidate Source Corpus 的 authoritative Source Root registry。

在这些问题获得确认前，不进行：

- Benchmark Source Corpus Selection；
- 删除 text_absent、unmatched filename 或 duplicate source；
- document-family / semantic duplicate resolution；
- Domain Taxonomy 映射；
- Phase 2 Taxonomy Calibration；
- Parser、OCR、MinerU 或 LLM workload。

## 7. Scope Decision 与下一步

当前采用 **Case C - Phase 1 Scope Decision: NEEDS OWNER CONFIRMATION**：

- Project-wide Phase 1 Closeout：**PENDING**；
- Phase 1 保持开放；
- `docs/06_progress.md` 保持 `Current Phase: Phase 1 - Corpus Inventory`；
- 当前任务为 `Candidate Source Corpus Scope Confirmation`；
- 不自动进入 Phase 2。

如果后续确认只有 `cmes_journal` 属于当前项目范围，才能将历史 approximately 70k 记录为
近似估计并执行 Project-wide Phase 1 Closeout。若确认存在其他 Candidate Source Root，则
应先分别完成 Intake 与 Inventory，再重新进行项目级 Gate Review。
