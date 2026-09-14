# 项目进度

Current Phase: Phase 1 - Corpus Inventory

Current Milestone: Corpus Inventory v0.1

Current Task: Minimal Corpus Inventory Pipeline Design v0.1

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
- Current Task: Minimal Corpus Inventory Pipeline Design v0.1

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
- 完成设计文档结构和说明占位。
- 暂未实现 PDF 解析、模型调用、数据生成或评测代码。

## Next Task

Review Minimal Corpus Inventory Pipeline Design, then implement D1 Smoke Test only.

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
