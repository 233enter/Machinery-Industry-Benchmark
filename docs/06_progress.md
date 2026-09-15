# 项目进度

Current Phase: Phase 2 - Taxonomy Calibration & Source Selection

Current Milestone: Source Corpus Calibration v0.1

Current Task: Gate 2C 20-item Annotation Dry-run Review

Next Task: Review Gate 2C-A annotator configuration, prompt, schema, provider adapters and dry-run protocol, then authorize the 20-item dual-annotator dry-run.

## Current Status

- Repository Baseline: Completed
- Project Charter v0.1: Completed
- Project Plan v0.1: Completed
- Benchmark Taxonomy v0.1: Completed
- Data Specification v0.1: Completed
- Evaluation Specification v0.1: Completed
- System Architecture v0.1: Completed
- Pilot Design v0.1: Completed
- Current Phase: Phase 2 - Taxonomy Calibration & Source Selection
- Current Milestone: Source Corpus Calibration v0.1
- D3 Scale Test: Passed。
- D3 Gate: Passed。
- Full Inventory Gate: Passed，已授权执行 Full Corpus Inventory。
- Full Corpus Inventory: Completed，Run ID 为 `full-20260914T075902Z-faa4565`，60454/60454 文件完成处理，Full Verdict: PASS。
- Full Inventory Artifact Validation: Passed；Source Snapshot 一致，D1/D2/D3 历史 Artifact 保持不变。
- `cmes_journal` Full Inventory Gate: Passed。
- Phase 1 Inventory Engineering Gate: Passed。
- Project-wide Phase 1 Closeout: Passed；Gate 1: Passed；Phase 1 - Corpus Inventory: Closed。
- Candidate Source Corpus Scope: Confirmed as `cmes_journal` only；authoritative count `60454 PDFs`。
- Full Inventory: PASS。
- Current Phase: Phase 2 - Taxonomy Calibration & Source Selection
- Current Milestone: Source Corpus Calibration v0.1
- Current Task: Gate 2C 20-item Annotation Dry-run Review
- Gate 2A: Passed；这是 Phase 2 Design Gate，不代表 Phase 2 complete。
- Gate 2B Runtime Self-check: Passed；Run ID 为 p2b-20260915T023641Z-cbde565，Main Sample 600、Audit Pools 167、Unique selected items 767，Artifact validation passed。
- Gate 2B Evidence Sufficiency Review: Completed；20-item Main Review Set 中 16 sufficient、1 borderline、3 insufficient，sufficient rate 80.0%。
- Gate 2B Initial Evidence Sufficiency Verdict: PASS WITH EVIDENCE REVISION；该历史 Review 结论保留。
- Gate 2B Evidence v0.2 Diagnostic Probe: Completed；Problem Set 4、Control Set 4，Probe B/C 均未将问题项提升到 sufficient，8 个 Source PDF size/mtime 均未变化。
- Evidence v0.2 Diagnostic Design: Completed；仅为诊断设计，不授权 Full Gate 2B rerun；`pdftotext` 保持 diagnostic-only。
- Evidence v0.3 OCR Runtime Capability Check: Completed；远程 `.venv` 已验证 `rapidocr==3.9.2`、`onnxruntime==1.23.2` 和 `CPUExecutionProvider`。
- Evidence v0.3 OCR Diagnostic: Completed；固定 8-item Diagnostic Set 已完成原始 PDF render + RapidOCR OCR，Problem 4/4 sufficient、Control 4/4 sufficient。
- Evidence v0.3 Fallback Strategy: Frozen；默认 render DPI 为 200，Automatic pre-annotation OCR trigger rejected，采用 annotation-side retry。
- Evidence v0.3 Routing Signal Calibration: Completed；最佳 100% garbled recall 规则会触发 288/600 Main（48.0%），因 fallback 路径过宽而不采用 automatic trigger。
- Evidence Contract: `evidence-v0.3-adaptive-v0.1`。
- Gate 2B Final Verdict: PASSED；20/20 reviewed Main items 存在 primary 或 validated fallback Evidence 路径。
- Full 767-item Evidence v0.3 Precomputation: CANCELLED / NOT REQUIRED；Gate 2B canonical Runtime 保持 immutable。
- Gate 2C-A Design Freeze: Completed；等待 Review。Gate 2C-B 20-item dry-run 尚未授权。

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
- D2 Representative Dry-run: Passed；D2 Gate: Passed。
- 完成 D3 实现与 Local/Remote Unit Test：38 passed；D3 commit 为 `ba05b05`。
- 完成 D2 三个 `zero_page_count` PDF 的只读 Audit；PyMuPDF 结果可重复，未修改 PDF 或 D2 Artifact。
- 完成 Remote D3 Scale Test：目标 1000、实际 1000，1000 success、0 partial、0 failed；worker count=4、`dirty=false`。
- D3 受控停止与 resume 通过：初次 `completed_count=300`，同一 Run ID resume 后 `checkpoint_reused_count=300`，最终 `run_status=completed`。
- D3 六个 Canonical Artifact、Schema、Source Provenance、D1/D2 排除、Source Consistency 和 Artifact checksum 校验通过；D3 Verdict: PASS；报告见 `reports/phase1/d3_scale_test_report.md`。
- 完成 Remote Full Corpus Inventory：60,454 个文件全量选择并处理，60447 success、7 partial、0 failed；报告见 `reports/phase1/full_inventory_report.md`。
- Full Run 完成 Artifact Validation；MinerU、OCR、LLM 或 GPU workload 仍未执行。
- 完成只读 Source Scope Discovery：`/mnt/data_nfs/dataset/original/cmes` 下仅观察到 `journal`；在 `/mnt/data_nfs/dataset/original` 下观察到四个 `books_*` Source Candidate 及一个混合 `all_pipeline` 工作区。
- 经项目 Owner 确认，四个 `books_*` 目录属于 Observed external / adjacent source data，不属于当前 MIGB Candidate Source Corpus；`all_pipeline` 继续不是 Candidate Source Corpus。
- 完成 Phase 1 Gate Review：Candidate Source Corpus Scope Confirmed as `cmes_journal` only；Gate 1: Passed；Phase 1 - Corpus Inventory: Closed。
- 项目状态切换至 Phase 2 - Taxonomy Calibration & Source Selection；切换时未执行任何 Phase 2 runtime 工作。
- 完成 Phase 2 Taxonomy Calibration & Source Selection Design v0.1 评审修订并通过 Gate 2A；文档状态为 `Reviewed - Baseline`，文档见 `docs/11_phase2_taxonomy_calibration_and_source_selection.md`。
- Gate 2A 之后仍未创建 Calibration Sample，未读取批量 PDF，未调用 LLM，未执行 Taxonomy Annotation、Source Selection、MinerU、OCR 或 Benchmark Item Generation。
- 完成 Gate 2B Calibration Sample & Evidence Runtime：Full Inventory 完整性校验通过，deterministic sample / Audit Pools / PyMuPDF lightweight Evidence 完成，767 个 unique selected items，self-check verdict: PASS；报告见 reports/phase2/gate2b_calibration_sample_evidence_report.md。
- 完成 Gate 2B Evidence Sufficiency Review：Main Review Set 20 条，16 sufficient、1 borderline、3 insufficient；发现 4 条明确 garbled 风险，Formal Verdict 为 PASS WITH EVIDENCE REVISION。
- 完成 8-file Evidence v0.2 Diagnostic Probe：固定复用 4 个 Problem Item，并从原 16 个 sufficient 中确定性选择 4 个 Control；pdftotext 22.02.0 可用，Probe B/C 均未解决问题项。
- Evidence v0.2 仅完成 diagnostic design；当时 Gate 2B 保持 HOLD，`pdftotext` 为 diagnostic-only；随后通过 Evidence v0.3 fallback diagnostic 和 Routing Contract Gate Decision 完成 Gate 2B Closeout。
- 完成 Evidence v0.3 OCR Runtime Capability Check：远程 `.venv` 安装并验证 `rapidocr==3.9.2`、`onnxruntime==1.23.2`，三个 ONNX Runtime session 均使用 `CPUExecutionProvider`；合成图中文/英文/数字识别通过。
- 完成 Evidence v0.3 OCR Diagnostic：固定复用 P1–P4/C1–C4，P1/P2 完成 200/300 DPI 对照，最终 200 DPI 下 Problem 4/4、Control 4/4 sufficient；Evidence v0.3 fallback strategy 冻结。
- 完成 Evidence v0.3 OCR Routing Signal Calibration：直接读取既有 767-item Evidence，生成独立 `quality_signals.parquet`；20-item Review Set 中 4 条 `OCR_REQUIRED_REFERENCE`、16 条 `OCR_NOT_REQUIRED_REFERENCE`，无简单规则同时满足 100% garbled recall 与 15% 路由指导线；Owner 接受 annotation-side retry、拒绝 automatic pre-annotation OCR trigger。
- 完成 Gate 2B Adaptive Evidence Closeout：Gate 2B Final Verdict 为 `PASSED`；Evidence Contract 冻结为 `evidence-v0.3-adaptive-v0.1`；Full 767-item Evidence v0.3 Precomputation 为 `CANCELLED / NOT REQUIRED`；Gate 2B canonical Runtime 保持 immutable。
- 完成 Gate 2C-A Design Freeze：冻结 annotator 配置、prompt、schema、provider adapter、retry semantics、Artifact 设计和 20-item dry-run protocol；当前不调用 LLM、不执行 20-item 或 600-item Annotation。
- 未实现完整 PDF Parser、模型调用、数据生成或评测代码。

## Next Task

Review Gate 2C-A annotator configuration, prompt, schema, provider adapters and dry-run protocol, then authorize the 20-item dual-annotator dry-run.

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
| 2026-09-14 | D2 Representative Dry-run 和 D2 Gate 通过；下一任务为 D3 Scale Test |
| 2026-09-14 | D3 Scale Test 完成并通过：目标/实际 1000，受控停止与 resume 通过，复用 300 个 checkpoint 记录；D3 Verdict: PASS；下一任务为 D3 Scale Test Artifact Review |
| 2026-09-14 | D3 Scale Test 和 D3 Gate 通过；Full Inventory Gate: Passed，已授权执行 Full Corpus Inventory；下一任务为 Full Corpus Inventory |
| 2026-09-14 | Full Corpus Inventory 完成并通过 Artifact Validation：60454/60454 processed，60447 success、7 partial、0 failed，Full Verdict: PASS；下一任务为 Full Corpus Inventory Artifact Review |
| 2026-09-14 | `cmes_journal` Full Inventory Gate 和 Phase 1 Inventory Engineering Gate 通过；只读 Source Scope Discovery 发现四个 `books_*` 目录及一个混合 `all_pipeline` 工作区，项目级 Phase 1 Closeout Pending Scope Confirmation；下一任务为 Candidate Source Corpus Scope Confirmation |
| 2026-09-14 | 项目 Owner 确认 `cmes_journal` / 60454 PDFs 是当前 MIGB 完整 Candidate Source Corpus；`books_*` 不纳入，`all_pipeline` 不是 Candidate Source Corpus；Gate 1: Passed，Phase 1 Closed；项目切换至 Phase 2 Taxonomy Calibration & Source Selection，下一任务为 Phase 2 Taxonomy Calibration Design |
| 2026-09-15 | 完成 Phase 2 Taxonomy Calibration & Source Selection Design v0.1 初稿；仅完成设计，未创建 Calibration Sample 或执行任何 Phase 2 Pipeline；下一任务为 Phase 2 Taxonomy Calibration Design Review |
| 2026-09-15 | Phase 2 Design v0.1 完成评审修订并通过 Gate 2A；仅冻结设计，不代表 Phase 2 complete；下一任务为 Gate 2B Calibration Sample & Evidence Implementation |
| 2026-09-15 | Gate 2B Runtime Self-check 完成并通过：Main Sample 600、Audit Pools 167、Unique selected items 767，Full Inventory / Artifact validation / deterministic recomputation 均通过；下一任务为 Gate 2B Calibration Sample & Evidence Artifact Review |
| 2026-09-15 | Gate 2B Evidence Sufficiency Review 完成：20 条 Main Review，16 sufficient、1 borderline、3 insufficient，sufficient rate 80.0%；Formal Verdict 为 PASS WITH EVIDENCE REVISION；下一任务为 Gate 2B Evidence Contract Revision |
| 2026-09-15 | 完成 8-file Evidence v0.2 Diagnostic Probe 和 diagnostic design：4 Problem + 4 Control；Probe B/C 均未将问题项提升到 sufficient；Gate 2B 保持 HOLD；下一任务为 Evidence v0.3 visual/OCR fallback 设计 |
| 2026-09-15 | 完成 Evidence v0.3 OCR Runtime Capability Check：Tesseract 与已检查的 Python OCR engines 均不可用；未执行 render/OCR；Gate 2B 保持 HOLD；下一任务为决定并提供最小中文 OCR dependency |
| 2026-09-15 | 完成 Evidence v0.3 OCR Runtime 与固定 8-item Diagnostic：远程 `.venv` 使用 RapidOCR 3.9.2 + ONNX Runtime 1.23.2 CPU，Problem 4/4、Control 4/4 sufficient；选择并冻结 200 DPI fallback strategy；Gate 2B 仍 HOLD；下一任务为同一 767-item sample 上的 Evidence v0.3 Implementation |
| 2026-09-15 | 完成 Evidence v0.3 OCR Routing Signal Calibration：读取既有 767-item canonical Evidence，生成独立 Quality Signals Artifact；最佳 100% garbled recall 规则的 Main Triggered Rate 为 48.0%，不满足 15% 工程指导线；冻结 annotation-side retry contract，Automatic OCR Trigger 未冻结，Full 767-item Runtime 暂不授权；下一任务为 Gate 2B Routing Contract Gate Decision |
| 2026-09-15 | Project Owner 接受 Annotation-side Retry、拒绝 Automatic pre-annotation OCR trigger；Gate 2B Adaptive Evidence Closeout 完成并通过，Evidence Contract 冻结为 `evidence-v0.3-adaptive-v0.1`；Full 767-item Evidence v0.3 Precomputation 取消且不再需要；下一任务为 Gate 2C Taxonomy Annotation Execution Design |
| 2026-09-15 | 建立 `docs/14_phase2_gate2c_taxonomy_annotation_design.md`：仅冻结 Gate 2C-A/B/C/D 执行骨架、A/B same-final-Evidence、retry semantics 和 20-item dry-run protocol；未调用 LLM，未执行 600-item Annotation；下一任务为 Gate 2C annotator configuration、prompt contract、annotation artifacts 和 dry-run protocol 评审冻结 |
| 2026-09-15 | 完成 Gate 2C-A Design Freeze：确定 Annotator A=`openai/gpt-5.6-sol`、Annotator B=`glm/glm-5.2`，建立 Taxonomy/Prompt/Schema snapshot、offline provider adapter、Retry/Agreement/Artifact contract 和 unit tests；未调用 LLM，等待 20-item dual-annotator dry-run 授权 |
