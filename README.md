# Mechanical Industry General Benchmark

机械工业通用知识大模型评测基准项目。

## 项目简介

该项目用于构建机械工业通用知识大模型 Benchmark，覆盖后续的基准设计、数据规范、评测规范及相关工程化准备工作。

项目目前处于 **Benchmark Design** 阶段。本阶段先建立项目章程、计划和设计文档框架，具体 Benchmark 设计内容将在后续讨论、评审和版本迭代中确定。

## 当前状态

- Current Phase: Phase 0 - Benchmark Design
- Current Milestone: Benchmark Design v0.1
- 当前阶段暂不实现：PDF 解析、模型调用、数据生成、评测代码。

## 项目结构

```text
.
├── README.md
├── docs/
│   ├── 00_project_charter.md
│   ├── 01_project_plan.md
│   ├── 02_benchmark_taxonomy.md
│   ├── 03_data_specification.md
│   ├── 04_evaluation_specification.md
│   ├── 05_system_architecture.md
│   └── 06_progress.md
├── configs/
├── src/
├── scripts/
├── tests/
├── data/
└── reports/
```

## 文档说明

- `docs/00_project_charter.md`：项目章程结构与待确认事项。
- `docs/01_project_plan.md`：项目计划结构与待确认事项。
- `docs/02_benchmark_taxonomy.md`：Benchmark 分类体系文档结构。
- `docs/03_data_specification.md`：数据规范文档结构。
- `docs/04_evaluation_specification.md`：评测规范文档结构。
- `docs/05_system_architecture.md`：系统架构文档结构。
- `docs/06_progress.md`：项目阶段、里程碑和进度记录。

上述文档当前只提供结构和说明，不预先确定 Benchmark 的具体设计结论。

## 范围边界

在 Phase 0 完成正式设计前，不开展 PDF 解析、模型调用、数据生成或评测实现。相关代码目录已预留，待设计内容经确认后再进入实现阶段。
