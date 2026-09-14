# 项目进度

Current Phase: Phase 1 - Corpus Inventory

Current Milestone: Corpus Inventory v0.1

Current Task: D2 Representative Dry-run Artifact Review

## Current Status

- Repository Baseline: Completed
- Project Charter v0.1: Completed
- Project Plan v0.1: Completed
- Benchmark Taxonomy v0.1: Completed
- Data Specification v0.1: Completed
- Evaluation Specification v0.1: Completed
- System Architecture v0.1: Completed
- Pilot Design v0.1: Completed
- Current Phase: Phase 1 - Corpus Inventory
- Current Milestone: Corpus Inventory v0.1
- Current Task: D2 Representative Dry-run Artifact Review

## 当前进展

- 完成项目目录骨架初始化。
- 完成 Project Charter v0.1 首次评审及小范围修订。
- 完成 Project Plan v0.1 首次评审后的小范围修订。
- 完成 Benchmark Taxonomy v0.1 首次正式评审后的结构性小修。
- 完成 Data Specification v0.1 首次正式评审后的结构性小修。
- 完成 Evaluation Specification v0.1 首次正式评审后的结构性小修。
- 完成 System Architecture v0.1 正式评审后的小范围修订，状态为 Reviewed - Baseline。
- 完成 Pilot Design v0.1 正式评审后的方法学小修，状态为 Reviewed - Baseline。
- 完成 Phase 0 Cross-document Consistency Review，未发现阻塞性问题，Gate 0: Passed。
- 完成 `cmes_journal` Source Root 的 Environment & Candidate Source Corpus Intake Closeout：60454 个 PDF、20 个一级目录、0 个非 PDF、0 个软链接、0 个 zero-byte PDF、0 个不可读 PDF。
- 确认 Candidate Source Corpus 位于 NFS4 `rw` mount，但按项目策略作为 read-only input；`/data` 可写，`/data-ssd` 不可写。
- 完成 Minimal Corpus Inventory Pipeline Design v0.1 Design Freeze，冻结 D1 的 PyMuPDF、UUIDv5、采样、Text-layer Heuristic、Status Semantics、Source Consistency、Duplicate Representation 和 4 workers 基线。
- 完成设计文档结构和说明占位。
- 完成 D1 最小实现、Local synthetic/tiny PDF Unit Tests，以及本地 D1 Artifact 写入验证。
- Local Unit Test 结果：29 passed；本地 commit：`5f8ecb3`。
- 已确认并建立远程 Git Repository：`/data/suzhe/Machinery-Industry-Benchmark`；Remote HEAD 为 `406473f`，正式运行前 `dirty=false`。
- Remote SSH Gate 已通过，hostname 为 `xuelangyun`；Output Path Safety Check 通过后创建 `/data/suzhe/migb`。
- 完成 Remote D1：Run ID 为 `d1-20260914T060712Z-406473f`，20/20 success、0 partial、0 failed，errors=0，source consistency 全部通过。
- 完成六个 D1 Artifact 的远程校验及 Mac 临时复核，D1 Verdict: PASS；报告见 `reports/phase1/d1_smoke_test_report.md`。
- 完成 D1 Gate Closeout，并将 Python package 标准化为可 editable install；Local/Remote pytest 均通过（33 passed）。
- 完成 Remote D2：Run ID 为 `d2-20260914T062102Z-18a5aad`，目标 200、实际 198，195 success、3 partial、0 failed；D1 样本 20 个全部排除。
- 完成 D2 六个 Artifact 的远程校验及 Mac 临时复核；确定性采样、Schema、Manifest、Source Consistency 及 D1 Artifact 不变性均通过，D2 Verdict: PASS；报告见 `reports/phase1/d2_representative_dryrun_report.md`。
- 未执行 D3、Full Inventory、MinerU、OCR、LLM 或 GPU workload。
- 未实现完整 PDF Parser、模型调用、数据生成或评测代码。

## Next Task

Review D2 results and decide D3 Scale Test configuration.

## 变更记录

| 日期 | 说明 |
| --- | --- |
| 2026-09-11 | 初始化 Phase 0 项目骨架 |
| 2026-09-11 | Repository Baseline 和 Project Charter v0.1 完成，下一任务为 Project Plan v0.1 |
| 2026-09-11 | Project Plan v0.1 完成，下一任务为 Benchmark Taxonomy v0.1 |
| 2026-09-11 | Benchmark Taxonomy v0.1 完成，下一任务为 Data Specification v0.1 |
| 2026-09-11 | Data Specification v0.1 完成，下一任务为 Evaluation Specification v0.1 |
| 2026-09-11 | Evaluation Specification v0.1 完成，下一任务为 System Architecture v0.1 |
| 2026-09-11 | System Architecture v0.1 完成并通过正式评审，下一任务为 Pilot Design v0.1 |
| 2026-09-14 | Pilot Design v0.1 完成并通过正式评审，Phase 0 Cross-document Consistency Review 无阻塞问题，Gate 0: Passed；下一任务为 Phase 1 Environment & Corpus Intake |
| 2026-09-14 | Environment & Candidate Source Corpus Intake Closeout 完成；下一任务为 Minimal Corpus Inventory Pipeline Design v0.1 |
| 2026-09-14 | Minimal Corpus Inventory Pipeline Design v0.1 完成初稿；下一任务为评审设计并仅实现 D1 Smoke Test |
| 2026-09-14 | Minimal Corpus Inventory Pipeline Design v0.1 完成 Design Freeze；下一任务为 D1 Smoke Test Implementation |
| 2026-09-14 | D1 本地实现与 29 项 Unit Tests 完成并提交；SSH Gate 通过，但远程 Repository checkout 路径未确认，Remote D1 暂缓 |
| 2026-09-14 | Remote D1 Smoke Test 完成并通过 Artifact Review：20/20 success、0 errors、source consistency 通过；下一任务为 D1 Smoke Test Artifact Review |
| 2026-09-14 | D1 Gate Closeout 完成；package editable install 标准化；下一任务为 D2 Representative Dry-run |
| 2026-09-14 | Remote D2 Representative Dry-run 完成并通过 Artifact Review：目标 200、实际 198，195 success、3 partial、0 failed；下一任务为 D2 Representative Dry-run Artifact Review |
