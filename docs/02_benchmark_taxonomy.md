# Mechanical Industry General Benchmark Taxonomy v0.1

## 文档信息

| 项目 | 内容 |
| --- | --- |
| Project | Mechanical Industry General Benchmark |
| Document | Benchmark Taxonomy |
| Version | 0.1 |
| Status | Reviewed - Baseline |
| Phase | Phase 0 - Benchmark Design |
| Current Task | Benchmark Taxonomy v0.1 |

> Taxonomy v0.1 是 Phase 0 的理论设计版本，当前状态为 Reviewed - Baseline。Phase 1 获得 Corpus Inventory 后，Phase 2 将结合真实数据对本 Taxonomy 进行校准，形成 Benchmark Taxonomy v0.2。本文件不处理 Candidate Source Corpus 的 70k PDF，不生成 Benchmark 问题，不实现评测代码，也不根据未知 Corpus 分布调整题目比例。

## 1. Taxonomy 的核心原则

### 1.1 采用多轴 Taxonomy

本项目不把 Benchmark Taxonomy 做成单纯的学科目录，例如：

~~~text
机械设计 → 齿轮 → 轴承 → 轴
~~~

一条 Benchmark Item 至少从以下相互独立的维度描述：

1. Domain；
2. Benchmark Track；
3. Fine-grained Capability；
4. Task；
5. Input Modality / Visual Type；
6. Difficulty；
7. Answer Type。

核心区分是：

- Domain 描述“问题关于什么机械知识”；
- Capability / Task 描述“模型需要做什么”。

两者应尽量正交。例如：

~~~text
Domain:
Mechanical Design & Machine Elements → Bearings

Capability:
Engineering Calculation

Task:
Bearing Life Calculation
~~~

### 1.2 Taxonomy 与 Sampling Strategy 分离

Taxonomy 定义“有哪些领域和能力需要测”；Sampling Strategy 决定“各测多少”。Taxonomy 不负责最终确定 Knowledge / Calculation / Multimodal 的题量比例。

Project Charter 当前规定的：

- Knowledge：40%；
- Calculation：30%；
- Multimodal：30%；

属于 Benchmark Track 的 V0.1 初始 Sampling Target，不是 Taxonomy 的权重定义，也不是不可调整的最终决定。

### 1.3 一个 Item 的概念分类元组

在最终 Data Specification 确定字段名称前，Taxonomy v0.1 使用以下概念元组描述一个 Item：

~~~text
Item =
(
  primary_domain,
  optional_secondary_domain,
  primary_benchmark_track,
  fine_grained_capability,
  task,
  primary_modality,
  optional_visual_type,
  design_difficulty,
  answer_type
)
~~~

该元组是理论分类模型，不直接等同于最终数据 Schema。多标签、字段必选性和具体 ID 规则由 Data Specification 决定。

## 2. Axis A：Domain Taxonomy v0.1

### 2.1 Domain 层级约束

第一版 Domain 只设计两级：

~~~text
Domain Level 1 → Domain Level 2
~~~

Domain Level 1 表示机械工业知识对象的较大范围；Domain Level 2 表示该范围内的可识别知识对象。v0.1 不继续设计第三级，以便在 Corpus Inventory 后校准粒度。

### 2.2 D01 Engineering Fundamentals & Mechanics

工程基础与力学。

Level 2 candidates：

- Statics；
- Dynamics；
- Strength of Materials / Mechanics of Materials；
- Vibration；
- Friction & Tribology Fundamentals；
- Basic Engineering Mathematics / Physical Relations。

这里只收录直接服务机械工业问题的工程基础，不把整个数学或物理学科纳入 Benchmark。

### 2.3 D02 Engineering Materials & Heat Treatment

工程材料与热处理。

Level 2 candidates：

- Ferrous Materials；
- Non-ferrous Materials；
- Polymers / Composites（如果 Corpus 支持）；
- Material Properties；
- Material Applications & Selection Principles；
- Heat Treatment；
- Surface Treatment；
- Material Failure Fundamentals。

### 2.4 D03 Mechanical Design & Machine Elements

机械设计与机械零部件。

Level 2 candidates：

- Shafts；
- Bearings；
- Gears；
- Fasteners；
- Springs；
- Couplings；
- Keys / Splines；
- Belt / Chain Drives；
- Seals；
- Lubrication；
- Structural Design Fundamentals。

### 2.5 D04 Mechanisms & Mechanical Transmission

机构与机械传动。

Level 2 candidates：

- Linkage Mechanisms；
- Cam Mechanisms；
- Gear Trains；
- Motion / Force Transmission；
- Speed / Torque Relations；
- Kinematics of Mechanisms。

D03 与 D04 在 v0.1 中暂时分开，但二者边界需要在 Phase 2 根据 Corpus Inventory、题目可构建性和知识对象边界进一步评估。

### 2.6 D05 Manufacturing Processes & Machine Tools

机械制造工艺与机床。

Level 2 candidates：

- Turning；
- Milling；
- Drilling；
- Grinding；
- Casting；
- Forging；
- Welding；
- Sheet Metal / Forming；
- Additive Manufacturing；
- Machining Parameters；
- Process Planning；
- Machine Tools；
- Cutting Tools。

### 2.7 D06 Tolerance, Metrology & Quality

公差、测量与质量。

Level 2 candidates：

- Dimensional Tolerance；
- Fits；
- Geometric Tolerance / GD&T；
- Surface Roughness；
- Measurement Instruments；
- Measurement Methods；
- Error / Uncertainty Fundamentals；
- Inspection；
- Quality Control。

### 2.8 D07 Engineering Drawing & Digital Design Representation

工程制图与数字化设计表达。

Level 2 candidates：

- Projection；
- Views；
- Section Views；
- Dimensioning；
- Drawing Symbols；
- Part Drawing；
- Assembly Drawing；
- BOM / Title Block；
- CAD Representation Fundamentals。

CAD 文件直接生成质量评测仍属于 Project Charter 的 Out of Scope / Not Priority for V1。D07 只评估工程设计表达的理解，不评估 CAD 文件生成质量。

### 2.9 D08 Hydraulics, Pneumatics & Fluid Power

液压、气动与流体传动。

Level 2 candidates：

- Hydraulic Components；
- Pneumatic Components；
- Pumps / Actuators；
- Valves；
- Circuits；
- Pressure / Flow Relations；
- Fluid Power System Architecture & Applications；
- Operating Characteristics & Principles。

### 2.10 D09 Thermo-fluid & Energy Systems

热流体与动力系统基础。

Level 2 candidates：

- Thermodynamics Fundamentals；
- Heat Transfer；
- Fluid Mechanics；
- Pumps / Fans / Compressors；
- Thermal Equipment；
- Energy / Power Relations。

只保留与机械工业和机械设备高度相关的内容。

### 2.11 D10 Mechatronics, Sensors, Control & Automation

机电、传感与控制。

Level 2 candidates：

- Sensors；
- Actuators；
- Motors；
- Drives；
- Basic Control；
- PLC / Industrial Control Fundamentals；
- Motion Control；
- Mechatronic Systems。

本 Domain 不扩展为完整电子、计算机或 AI Benchmark。

### 2.12 D11 Equipment Operation, Maintenance & Reliability

设备运行、维护与可靠性。

Level 2 candidates：

- Installation；
- Commissioning；
- Operation；
- Maintenance；
- Lubrication Practice；
- Wear；
- Failure Modes；
- Reliability；
- Condition Monitoring。

Fault Diagnosis 更主要作为 Capability / Task，不把所有 Diagnosis 问题固定归属于 D11。例如：

~~~text
Bearing failure diagnosis

Domain = D03 Bearing
Capability = K7 Fault Diagnosis & Troubleshooting
~~~

### 2.13 D12 Standards, Safety & Engineering Practice

标准、安全与工程实践。

Level 2 candidates：

- Engineering Standards；
- Technical Specifications；
- Safety Requirements；
- Compliance；
- Engineering Conventions；
- Industrial Terminology；
- General Engineering Practice。

D12 在 v0.1 保留，但具有 Cross-domain 特征。Phase 2 需要判断它最终是否继续作为独立 Domain，还是更多转为 Capability / Metadata。

### 2.14 Domain Assignment Principle

Domain 应根据题目真正考查的机械专业知识对象确定，而不能根据输入形式、图片类型、PDF 所属章节或 Question wording 机械式决定。特别是，Domain 不等于 Modality：同一类视觉输入可能考查不同的机械知识对象，也不应因为输入是图纸就自动归入 D07。

典型案例：

- 轴承装配图中的定位方式：知识对象是轴承及其装配关系，归入 D03 Mechanical Design & Machine Elements → Bearings；Primary Track 为 T3 Multimodal Understanding，Capability 为 M8 Assembly & Spatial Relationship，Modality 为 assembly_drawing。
- 三视图投影关系：知识对象是工程制图中的投影关系，归入 D07 Engineering Drawing & Digital Design Representation → Projection。
- 图纸中的 H7/g6 配合：知识对象是配合与公差，归入 D06 Tolerance, Metrology & Quality → Fits / Dimensional Tolerance；即使输入仍为 mechanical_drawing，也不因此改变 Domain。

### 2.15 Level 2 命名原则

Domain Level 2 的命名应优先使用以下类型的知识对象化表达：

- knowledge object；
- engineering subject；
- component family；
- physical / engineering phenomenon；
- technical area。

应避免把 selection、diagnosis、comparison、calculation、judgment 等纯 Capability 动作直接作为 Domain Level 2 名称。相关动作由 Fine-grained Capability 和 Task 表达；Level 2 名称应保持对机械知识对象或技术领域的指向。

### 2.16 Domain Taxonomy 的设计约束

1. Domain 表示知识对象，不表示认知能力。
2. 一个 Item 必须有一个 Primary Domain。
3. 可允许 Secondary Domain，但是否进入最终 Schema 由 Data Specification 决定。
4. Domain v0.1 不应根据当前未知的 Candidate Source Corpus 数量决定权重。
5. Candidate Source Corpus 缺少某领域资料，不意味着该领域没有 Benchmark 价值。
6. Candidate Source Corpus 某领域资料特别多，也不意味着该领域应该获得更高 Benchmark 权重。
7. Phase 2 根据 Corpus Inventory 校准 Domain，但不能让 Corpus 分布完全决定 Benchmark 能力目标。

## 3. Axis B：Benchmark Track

为避免与 Fine-grained Capability 混淆，Project Charter 的三个一级能力在 Taxonomy 中统一称为 Benchmark Track：

~~~text
T1 Mechanical Knowledge
T2 Engineering Calculation
T3 Multimodal Understanding
~~~

Benchmark Track 是最终报告中的三个一级分项；Fine-grained Capability 是 Track 内部进一步测试的能力。

### 3.1 Benchmark Track Assignment Principle

Benchmark Track 定义为 Primary Evaluation Bucket / 主评测分区，用于：

- Pilot Sampling；
- Benchmark 一级分项；
- Leaderboard 一级报告；
- Knowledge 40% / Calculation 30% / Multimodal 30% 的 Sampling Target。

每个 Benchmark Item 原则上必须且只能有一个 `primary_benchmark_track`。其他跨 Track 能力可以在后续 Data Specification 中讨论如何记录，但不改变该 Item 的主评测分区。

Track Assignment Rule：

~~~text
Does the item require visual evidence to answer correctly?
        |
        +-- Yes --> T3 Multimodal Understanding
        |
        +-- No -->
                 Is quantitative engineering calculation
                 the primary evaluation objective?
                         |
                         +-- Yes --> T2 Engineering Calculation
                         |
                         +-- No --> T1 Mechanical Knowledge
~~~

具体解释如下：

- 如果正确作答必须读取 drawing、image、visual table、visual chart、schematic、multi-view 或 equipment image 等视觉证据，则归入 T3 Multimodal Understanding。
- T3 具有视觉依赖优先级：即使题目同时包含计算，只要视觉信息是完成题目不可缺少的 evidence，仍归入 T3。
- 如果不需要视觉信息，且主要评测目标是定量工程求解，则归入 T2 Engineering Calculation。
- 如果既不要求必要视觉信息，也不以数值计算为主要目标，则归入 T1 Mechanical Knowledge。T1 不等于只考记忆，也包括 fact、principle、comparison、selection、diagnosis、reasoning 和 judgment。

### 3.1.1 Mixed-task Examples

- 文字给出功率和转速，求轴扭矩：`primary_benchmark_track = T2 Engineering Calculation`。
- 图纸读取直径和公差：`primary_benchmark_track = T3 Multimodal Understanding`。
- 图纸读取尺寸后计算装配间隙：`primary_benchmark_track = T3 Multimodal Understanding`。虽然包含 calculation，但视觉信息是完成问题不可缺少的 evidence。
- 文字描述轴承温升、噪声和振动后判断故障：`primary_benchmark_track = T1 Mechanical Knowledge`，Capability = K7 Fault Diagnosis & Troubleshooting。

### 3.2 T1 Mechanical Knowledge

评估机械领域事实、术语、概念、原理、标准、应用知识和工程判断。

Knowledge 不等于纯背诵，应允许理解、比较、选择、解释和判断等任务。

### 3.3 T2 Engineering Calculation

评估公式理解、参数使用、单位处理、数值计算、多步骤工程计算和工程量估算。

核心要求是尽可能具备客观、可程序验证的 Ground Truth。

### 3.4 T3 Multimodal Understanding

评估模型利用机械工业视觉信息完成识别、读取、推理、计算和判断的能力。

视觉对象不限于工程图，还可以包括：

- table；
- chart；
- curve；
- schematic；
- process diagram；
- equipment image；
- technical illustration；
- CAD screenshot / rendered view；
- multi-view drawing。

Multimodal Track 的题目必须真正依赖视觉信息。

## 4. Axis C：Fine-grained Capability

Fine-grained Capability 说明模型在某个 Benchmark Track 中需要完成的相对稳定的能力动作。它不等同于 Domain，也不等同于具体 Task。

### 4.1 T1 Mechanical Knowledge Capabilities

| ID | Fine-grained Capability | 定义 |
| --- | --- | --- |
| K1 | Fact & Terminology | 识别和理解事实、定义、术语、符号等基础知识 |
| K2 | Concept & Principle Understanding | 理解机械原理、工作机制和物理意义 |
| K3 | Classification & Comparison | 进行分类、区别、优缺点比较和适用场景比较 |
| K4 | Standards & Specification Interpretation | 理解标准、规范、公差、技术要求和符号含义 |
| K5 | Engineering Application & Selection | 根据工况进行材料、零件、工艺、参数或设备选择 |
| K6 | Cause-effect & Engineering Reasoning | 根据机械原理分析条件、原因、结果、行为或性能 |
| K7 | Fault Diagnosis & Troubleshooting | 根据现象、条件和设备状态判断故障模式、原因或处理行动 |
| K8 | Consistency / Compliance Judgment | 判断技术说法、工艺、参数或结构是否合理、合规 |

### 4.2 T2 Engineering Calculation Capabilities

| ID | Fine-grained Capability | 定义 |
| --- | --- | --- |
| C1 | Direct Formula Application | 已知公式关系，完成单步骤或简单代入 |
| C2 | Unit & Quantity Conversion | 进行单位转换、量纲一致性和工程单位处理 |
| C3 | Multi-step Calculation | 使用多个计算步骤或中间变量完成计算 |
| C4 | Formula Selection | 从问题条件中判断应使用的工程关系或公式 |
| C5 | Table / Data Lookup + Calculation | 从表格、参数表或技术数据提取信息后计算 |
| C6 | Engineering Sizing / Parameter Determination | 根据设计条件求尺寸、参数、容量、允许载荷、功率、转速、扭矩或安全系数 |
| C7 | Constraint-aware Calculation | 在计算中处理上下限、公差、安全系数、工况或多约束判断 |
| C8 | Quantitative Comparison / Estimation | 对多个方案进行定量比较或工程估算 |

### 4.3 T3 Multimodal Capabilities

参考机械图纸 Benchmark 的 Recognition / Reasoning / Judging 思路，但扩展到更广泛的工业视觉内容。

| ID | Fine-grained Capability | 定义 |
| --- | --- | --- |
| M1 | Identification & Counting | 识别零件、元件、符号、设备、视图或数量 |
| M2 | Dimension, Symbol & Annotation Reading | 读取尺寸、公差、GD&T、表面粗糙度、标注和技术符号 |
| M3 | Text / Table / BOM Understanding | 理解 Title Block、BOM、技术表格、参数表和图中文字 |
| M4 | Localization | 定位指定的零件、标注、区域、结构或符号 |
| M5 | Chart / Curve Interpretation | 理解性能曲线、应力应变图、特性曲线、工艺曲线或实验图表 |
| M6 | Structure Understanding | 理解零件形状、内部结构和组件关系 |
| M7 | Projection & Multi-view Reasoning | 理解三视图、剖视、投影关系和不同视图的对应关系 |
| M8 | Assembly & Spatial Relationship | 判断装配、定位、配合和空间约束关系 |
| M9 | Geometric / Quantitative Visual Reasoning | 根据图纸或视觉数据完成几何、尺寸链、数量或参数计算 |
| M10 | Anomaly / Defect Detection | 发现异常、缺失、不合理结构、加工/装配问题或图纸问题 |
| M11 | Consistency / Compliance Judgment | 判断不同视图、表格、尺寸和技术要求之间是否一致、合理或合规 |

## 5. Axis D：Task Taxonomy

### 5.1 Capability 与 Task 的关系

Capability 是较稳定的能力类别；Task 是具体可构题、可记录和可扩展的任务。

例如：

~~~text
Domain:
D03 Mechanical Design & Machine Elements → Bearings

Track:
T2 Engineering Calculation

Capability:
C3 Multi-step Calculation

Task:
Bearing Life Calculation
~~~

Task 不需要在 v0.1 枚举机械工业的所有任务。Task Taxonomy 应设计为可扩展 Controlled Vocabulary，而不是一次性封死。

正式 Task ID 规则由 Data Specification 再确认。以下 ID 为 v0.1 的候选示例：

~~~text
K5.material_selection
K5.bearing_selection
C3.multi_stage_transmission
M7.view_correspondence
~~~

### 5.2 T1 Mechanical Knowledge Task Examples

| Capability | Task 定义 | 典型 Task 示例 |
| --- | --- | --- |
| K1 Fact & Terminology | 测试术语、定义、事实或符号的直接理解 | term_definition；symbol_meaning；fact_identification；basic_property_recall |
| K2 Concept & Principle Understanding | 测试工作原理、机制和物理意义的解释或判断 | principle_explanation；mechanism_interpretation；operating_principle；physical_meaning |
| K3 Classification & Comparison | 测试对象分类、差异、优缺点和适用条件比较 | component_classification；method_comparison；advantage_tradeoff；application_scenario_comparison |
| K4 Standards & Specification Interpretation | 测试标准、规范、技术要求和符号的理解 | standard_clause_interpretation；fit_or_tolerance_interpretation；drawing_symbol_interpretation；technical_requirement_compliance |
| K5 Engineering Application & Selection | 测试基于工况的工程选型和应用判断 | material_selection；bearing_selection；machining_process_selection；lubricant_selection；fit_selection |
| K6 Cause-effect & Engineering Reasoning | 测试条件、原因、结果和性能变化之间的工程推理 | cause_effect_analysis；condition_behavior_reasoning；performance_change_reasoning；design_tradeoff_reasoning |
| K7 Fault Diagnosis & Troubleshooting | 测试从现象到故障模式、可能原因和处理行动的判断 | failure_mode_identification；root_cause_hypothesis；troubleshooting_action_selection；maintenance_priority_judgment |
| K8 Consistency / Compliance Judgment | 测试技术说法、工艺、参数和结构的合理性或合规性判断 | technical_claim_check；process_principle_check；parameter_compliance_check；structural_issue_judgment |

### 5.3 T2 Engineering Calculation Task Examples

| Capability | Task 定义 | 典型 Task 示例 |
| --- | --- | --- |
| C1 Direct Formula Application | 使用已给出的工程公式完成直接计算 | shaft_torque_calculation；power_speed_conversion；stress_calculation；basic_ratio_calculation |
| C2 Unit & Quantity Conversion | 处理工程单位、量纲和数值表达的一致性 | unit_conversion；dimensional_consistency_check；engineering_unit_normalization |
| C3 Multi-step Calculation | 通过多个计算步骤或中间量完成工程求解 | multi_stage_transmission；load_path_calculation；thermal_or_fluid_multi_step；combined_stress_calculation |
| C4 Formula Selection | 根据条件选择合适的公式、关系或计算模型 | formula_selection；model_relation_selection；calculation_method_selection |
| C5 Table / Data Lookup + Calculation | 从技术表格或数据中查找参数并参与计算 | table_lookup_calculation；property_table_lookup；catalog_parameter_lookup；chart_data_lookup_calculation |
| C6 Engineering Sizing / Parameter Determination | 根据设计条件确定尺寸、容量、功率或其他工程参数 | shaft_diameter_sizing；bearing_selection_by_load；power_capacity_determination；allowable_load_determination；safety_factor_sizing |
| C7 Constraint-aware Calculation | 在计算中结合边界、工况、公差或安全约束进行判断 | tolerance_aware_calculation；safety_factor_check；boundary_condition_check；multi_constraint_feasibility |
| C8 Quantitative Comparison / Estimation | 对方案、性能或容量进行定量比较和估算 | design_option_quantitative_comparison；engineering_estimation；capacity_margin_comparison；sensitivity_estimation |

### 5.4 T3 Multimodal Task Examples

| Capability | Task 定义 | 典型 Task 示例 |
| --- | --- | --- |
| M1 Identification & Counting | 从视觉输入识别对象或统计数量 | part_identification；component_counting；symbol_identification；view_identification |
| M2 Dimension, Symbol & Annotation Reading | 从图像或图纸读取尺寸、符号和技术标注 | dimension_reading；tolerance_reading；gdt_reading；roughness_symbol_reading；annotation_interpretation |
| M3 Text / Table / BOM Understanding | 从视觉表格、BOM、标题栏或图中文字提取并理解信息 | title_block_reading；bom_understanding；technical_table_lookup；parameter_table_interpretation；drawing_text_understanding |
| M4 Localization | 在视觉区域中定位指定对象、标注或结构 | region_localization；component_localization；annotation_localization；symbol_localization |
| M5 Chart / Curve Interpretation | 从曲线或图表读取趋势、关系和比较信息 | performance_curve_interpretation；stress_strain_curve_interpretation；process_curve_interpretation；chart_comparison |
| M6 Structure Understanding | 理解零件形状、内部结构、特征和组件关系 | part_shape_understanding；internal_structure_understanding；component_relation_understanding；feature_relation_reasoning |
| M7 Projection & Multi-view Reasoning | 根据多个视图、投影或剖视建立空间对应关系 | orthographic_view_correspondence；section_view_interpretation；projection_relation_reasoning；multi_view_geometry |
| M8 Assembly & Spatial Relationship | 从装配图或结构图判断组件、定位、配合和空间关系 | assembly_relation_reasoning；locating_relation_identification；fit_relation_from_drawing；spatial_constraint_reasoning |
| M9 Geometric / Quantitative Visual Reasoning | 根据视觉尺寸或几何关系完成定量推理 | visual_geometry_calculation；dimension_chain_calculation；quantity_counting_from_visual；parameter_calculation_from_drawing |
| M10 Anomaly / Defect Detection | 发现视觉输入中的缺失、异常、缺陷或图纸问题 | visual_anomaly_detection；missing_feature_detection；structural_issue_detection；drawing_error_detection；process_assembly_defect_detection |
| M11 Consistency / Compliance Judgment | 比较不同视觉区域或技术要求并判断一致性和合规性 | cross_view_consistency_check；table_drawing_consistency_check；dimension_requirement_consistency；visual_compliance_judgment |

### 5.5 Task 设计约束

- 每个 Fine-grained Capability 应具有 Task 定义和 2～5 个典型 Task 示例。
- Task 应描述可构题、可标注、可验证的模型行为。
- Task 不应重复承担 Domain 的职责。
- Task ID 应成为可扩展 Controlled Vocabulary 的候选项。
- 新增、重命名或废弃 Task 时，必须遵循 Taxonomy Governance 的版本和兼容性规则。

## 6. Axis E：Input Modality / Visual Type

### 6.1 Text-only

至少包括：

- text。

### 6.2 Text + Structured Technical Content

至少包括：

- text_formula；
- text_table。

这类输入仍可能属于 T1 Mechanical Knowledge 或 T2 Engineering Calculation。Modality 不决定 Benchmark Track。

### 6.3 Visual

Visual Type 至少包括：

- mechanical_drawing；
- part_drawing；
- assembly_drawing；
- schematic_diagram；
- process_diagram；
- table_image；
- chart_curve；
- technical_illustration；
- equipment_photo；
- cad_render_or_screenshot；
- multi_image / multi_view。

一个 Item 可以包含多个 modality，但应指定 primary_modality。具体字段、枚举值和必选性由 Data Specification 决定。

## 7. Multimodal ≠ Modality

Multimodal 是 Benchmark Track；Modality 是输入内容的形式。两者不能混为一层，也不能用 Modality 代替 Capability。

| 场景 | Benchmark Track | Modality | Capability |
| --- | --- | --- | --- |
| 一张图纸上的尺寸读取 | T3 Multimodal Understanding | mechanical_drawing | M2 Dimension, Symbol & Annotation Reading |
| PDF 文本中的轴承寿命计算 | T2 Engineering Calculation | text_formula | C3 Multi-step Calculation |
| 图纸读取尺寸后再计算 | 以主要目标定义为 T3 Multimodal Understanding | mechanical_drawing | M9 Geometric / Quantitative Visual Reasoning |

如果一个 Item 同时具有视觉读取和工程计算成分，应按 Benchmark Track Assignment Principle 处理：需要视觉证据时优先归入 T3，即使包含计算。是否记录 secondary capability、cross-cutting skill 或 multi-label metadata，由 Data Specification 后续决定。

## 8. Axis F：Difficulty Framework

### 8.1 Design Difficulty 与 Empirical Difficulty

Taxonomy v0.1 区分两个概念：

- Design Difficulty：构题阶段根据规则给出的预期难度，字段候选名为 design_difficulty；
- Empirical Difficulty：Pilot Benchmark 多模型运行后，根据真实模型表现得到的难度，字段候选名为 empirical_difficulty。

Phase 0 只正式定义 Design Difficulty。Empirical Difficulty 的计算方法留给 Evaluation Specification / Phase 6 决定。

### 8.2 Design Difficulty v0.1

#### Easy

典型特征：

- 单一知识点；
- 直接事实或定义；
- 一步公式；
- 信息明确；
- 视觉目标明显；
- 无明显跨区域整合。

#### Medium

典型特征：

- 2～3 个知识关系；
- 需要选择适用原理或公式；
- 多步骤计算；
- 查表 + 应用；
- 视觉信息需要跨区域整合；
- 需要简单工程判断。

#### Hard

典型特征：

- 多知识点组合；
- 三步以上推理；
- 多约束条件；
- 标准 + 工程知识联合；
- 多视图 / 空间关系推理；
- 视觉信息 + 专业知识 + 计算联合；
- 需要排除多个合理候选解释。

Easy / Medium / Hard 是 heuristic indicators，而不是 hard threshold。一步推理不一定是 Easy，三步推理也不一定是 Hard；`reasoning_steps` 只是多个 Difficulty Dimensions 之一，不能单独决定最终难度。Design Difficulty 应综合考虑 `knowledge_depth`、`reasoning_steps`、`mathematical_complexity`、`constraint_complexity`、`visual_complexity` 和 `information_integration_complexity`。

歧义、缺失信息和 Ground Truth 不可靠不能作为 Hard 的定义：

~~~text
Bad Question ≠ Hard Question
~~~

### 8.3 Difficulty Dimensions

除最终 Easy / Medium / Hard 外，Taxonomy v0.1 记录以下难度来源概念：

- knowledge_depth；
- reasoning_steps；
- mathematical_complexity；
- constraint_complexity；
- visual_complexity；
- information_integration_complexity。

这些概念是否全部进入最终 Data Schema，由 Data Specification 决定。

## 9. Axis G：Answer Type

### 9.1 初始 Answer Type

Taxonomy v0.1 定义以下初始 Answer Type：

- single_choice；
- multiple_choice；
- true_false；
- numeric；
- short_answer；
- structured_answer。

V1 应优先使用具有稳定 Ground Truth 的 Answer Type。开放式长答案不能作为 Benchmark 的主要形式；具体评分方法留给 Evaluation Specification。

### 9.2 Question Type 与 Answer Type 的区分

Question Type、Benchmark Track、Task、Modality 和 Answer Type 必须独立记录。

例如：

| 场景 | Benchmark Track | Answer Type |
| --- | --- | --- |
| 机械计算题 | Engineering Calculation | numeric |
| 图纸尺寸读取题 | Multimodal Understanding | numeric |
| 标准判断题 | Mechanical Knowledge | single_choice / true_false |

同一个 Answer Type 可以出现在不同 Track 中，不能通过 Answer Type 反推 Track 或 Capability。

## 10. Benchmark Item 分类示例

以下示例用于说明多轴分类方式，不代表已经生成题目，也不构成最终数据集。

### Example 1：Fit Definition

问题：什么是过盈配合？

| 维度 | 分类 |
| --- | --- |
| Domain | D06 Tolerance, Metrology & Quality → Fits |
| Track | T1 Mechanical Knowledge |
| Capability | K1 Fact & Terminology |
| Task | fit_definition |
| Modality | text |
| Design Difficulty | Easy |
| Answer Type | short_answer |

### Example 2：Shaft Torque Calculation

问题：给定功率和转速计算轴扭矩。

| 维度 | 分类 |
| --- | --- |
| Domain | D03 Mechanical Design & Machine Elements → Shafts |
| Track | T2 Engineering Calculation |
| Capability | C1 Direct Formula Application |
| Task | shaft_torque_calculation |
| Modality | text_formula |
| Design Difficulty | Easy |
| Answer Type | numeric |

### Example 3：Material Selection

问题：根据载荷、工作环境和制造条件选择候选材料。

| 维度 | 分类 |
| --- | --- |
| Domain | D02 Engineering Materials & Heat Treatment → Material Applications & Selection Principles |
| Track | T1 Mechanical Knowledge |
| Capability | K5 Engineering Application & Selection |
| Task | material_selection |
| Modality | text |
| Design Difficulty | Medium |
| Answer Type | single_choice |

### Example 4：Manufacturing Process Selection

问题：根据零件形状、材料和精度要求选择合适的制造工艺。

| 维度 | 分类 |
| --- | --- |
| Domain | D05 Manufacturing Processes & Machine Tools → Process Planning |
| Track | T1 Mechanical Knowledge |
| Capability | K5 Engineering Application & Selection |
| Task | machining_process_selection |
| Modality | text |
| Design Difficulty | Medium |
| Answer Type | single_choice |

### Example 5：Fault Diagnosis

问题：根据轴承运行温升、噪声和振动现象判断可能的故障模式及排查行动。

| 维度 | 分类 |
| --- | --- |
| Domain | D03 Mechanical Design & Machine Elements → Bearings |
| Track | T1 Mechanical Knowledge |
| Capability | K7 Fault Diagnosis & Troubleshooting |
| Task | bearing_failure_diagnosis |
| Modality | text |
| Design Difficulty | Hard |
| Answer Type | structured_answer |

### Example 6：Table + Calculation

问题：从材料性能表中读取参数，并计算给定工况下的允许载荷。

| 维度 | 分类 |
| --- | --- |
| Domain | D02 Engineering Materials & Heat Treatment → Material Properties |
| Track | T2 Engineering Calculation |
| Capability | C5 Table / Data Lookup + Calculation |
| Task | property_table_lookup |
| Modality | text_table |
| Design Difficulty | Medium |
| Answer Type | numeric |

### Example 7：Drawing Dimension Reading

问题：读取机械图纸中指定孔的直径和公差。

| 维度 | 分类 |
| --- | --- |
| Domain | D07 Engineering Drawing & Digital Design Representation → Dimensioning |
| Track | T3 Multimodal Understanding |
| Capability | M2 Dimension, Symbol & Annotation Reading |
| Task | dimension_reading |
| Modality | mechanical_drawing / part_drawing |
| Visual Type | mechanical_drawing |
| Design Difficulty | Easy |
| Answer Type | numeric |

### Example 8：Multi-view Reasoning

问题：根据三视图和剖视图判断指定结构在不同视图中的对应关系。

| 维度 | 分类 |
| --- | --- |
| Domain | D07 Engineering Drawing & Digital Design Representation → Projection |
| Track | T3 Multimodal Understanding |
| Capability | M7 Projection & Multi-view Reasoning |
| Task | view_correspondence |
| Modality | multi_image / multi_view |
| Visual Type | multi-view drawing |
| Design Difficulty | Hard |
| Answer Type | single_choice |

### Example 9：Assembly / Visual Calculation

问题：根据装配图中的尺寸和组件关系计算指定装配间隙。

| 维度 | 分类 |
| --- | --- |
| Domain | D03 Mechanical Design & Machine Elements → Structural Design Fundamentals |
| Track | T3 Multimodal Understanding |
| Capability | M9 Geometric / Quantitative Visual Reasoning |
| Secondary Capability | M8 Assembly & Spatial Relationship（是否允许由 Data Specification 决定） |
| Task | parameter_calculation_from_drawing |
| Modality | assembly_drawing |
| Visual Type | assembly_drawing |
| Design Difficulty | Hard |
| Answer Type | numeric |

## 11. Coverage Matrix：Domain × Benchmark Track

### 11.1 状态含义

Coverage Matrix 只表达 v0.1 的覆盖预期，不表达题量比例或最终 Sampling Target：

- Required：该 Domain 应有该 Track 的代表性覆盖；
- Recommended：该 Track 对该 Domain 有较高价值，建议覆盖；
- Optional：可以覆盖，但不是该 Domain 的主要 Track；
- Not Typical：通常不是该 Domain 的典型评测方式。

### 11.2 v0.1 Coverage Matrix

| Domain | T1 Mechanical Knowledge | T2 Engineering Calculation | T3 Multimodal Understanding |
| --- | --- | --- | --- |
| D01 Engineering Fundamentals & Mechanics | Required | Required | Recommended |
| D02 Engineering Materials & Heat Treatment | Required | Recommended | Recommended |
| D03 Mechanical Design & Machine Elements | Required | Required | Required |
| D04 Mechanisms & Mechanical Transmission | Required | Required | Recommended |
| D05 Manufacturing Processes & Machine Tools | Required | Recommended | Required |
| D06 Tolerance, Metrology & Quality | Required | Recommended | Required |
| D07 Engineering Drawing & Digital Design Representation | Required | Optional | Required |
| D08 Hydraulics, Pneumatics & Fluid Power | Required | Required | Required |
| D09 Thermo-fluid & Energy Systems | Required | Required | Recommended |
| D10 Mechatronics, Sensors, Control & Automation | Required | Recommended | Recommended |
| D11 Equipment Operation, Maintenance & Reliability | Required | Recommended | Recommended |
| D12 Standards, Safety & Engineering Practice | Required | Optional | Recommended |

### 11.3 Coverage Matrix 约束

- 该矩阵是 v0.1 coverage expectation，不是最终题量权重。
- 不根据矩阵直接推导 40% / 30% / 30% 的题量分配。
- Phase 2 应根据 Corpus Inventory 检查各格的实际资料覆盖和可构题性。
- 某个格缺少资料时，不自动删除对应能力目标；应记录为 Calibration 或 Source Selection 问题。
- Calculation + Multimodal 混合题按 Benchmark Track Assignment Principle 归类；secondary capability、cross-cutting skill 和 multi-label metadata 的表达方式仍属于 Open Questions。

## 12. Source Type 不属于 Taxonomy

以下内容属于 Metadata / Data Governance，不混入 Domain Taxonomy：

- textbook；
- handbook；
- standard；
- paper；
- manual；
- specification；
- training material。

Source Type 用于描述资料来源类型；Source Provenance 用于支持资料追溯和治理。二者都不用于替代 Domain、Benchmark Track 或 Fine-grained Capability。具体字段由 Data Specification 定义。

## 13. Taxonomy Governance

### 13.1 节点最小定义

每个 Domain、Capability 和 Task 应具有：

- stable identifier；
- display name；
- definition；
- inclusion criteria；
- exclusion criteria；
- examples。

上述信息是 Taxonomy 节点的最小治理记录，不代表最终 Data Schema 的字段名称。

### 13.2 变更规则

未来新增 Taxonomy 节点时，应记录：

- version；
- reason；
- impact；
- migration / compatibility。

删除或重命名节点时，应避免直接破坏历史 Benchmark Item。若必须变更，应保留旧 ID 的映射、兼容说明和历史解释路径。

### 13.3 评审责任

- Phase 0 负责形成理论设计和跨文档约束；
- Phase 1 提供 Corpus Inventory 事实依据；
- Phase 2 负责 Taxonomy Calibration 和 Source Selection；
- Data Specification 负责确认字段、ID、标签和 Schema 的最终表达；
- Taxonomy 相关未决事项必须显式记录，不得由单次自动分类结果直接决定。

## 14. Coverage Gap Watchlist

以下项目是 Coverage Gap Watchlist，仅用于提醒 Phase 2 Calibration 检查潜在覆盖缺口，不是 Taxonomy v0.1 的正式 Domain 或 Level 2 节点。所有项目当前均为 Watchlist / TBD；只有 Phase 2 在 Corpus Inventory、资料质量和可构题性等方面获得足够依据后，才允许讨论新增或扩展。

| Candidate Area / Question | Status | Resolution Boundary |
| --- | --- | --- |
| CAE / Engineering Simulation / FEA | Watchlist / TBD | Phase 2 根据资料覆盖和可客观评测性判断是否需要纳入 |
| Production / Manufacturing Systems | Watchlist / TBD | Phase 2 根据工业生产系统资料和能力覆盖判断 |
| Vehicle / Mobile Machinery | Watchlist / TBD | Phase 2 根据候选资料范围和 V1 目标相关性判断 |
| Robotics | Watchlist / TBD | Phase 2 根据候选资料覆盖和与机械工业的边界判断 |
| Electrical Fundamentals for Mechanical Systems | Watchlist / TBD | Phase 2 判断是否需要作为机械系统相关知识范围扩展 |
| Tribology 是否需独立 | Watchlist / TBD | Phase 2 根据现有 D01 / D03 覆盖和资料粒度判断 |
| Reliability 是否需扩展 | Watchlist / TBD | Phase 2 根据 D11 覆盖、题目可构建性和评测价值判断 |

## 15. Phase 2 Calibration

Taxonomy v0.1 不是最终 Taxonomy。Phase 1 获得 Corpus Inventory 后，Phase 2 至少检查：

- Domain 是否缺失；
- Domain 是否过度细分；
- D03 / D04 是否需要调整；
- D12 是否应该继续作为独立 Domain；
- Candidate Source Corpus 实际覆盖情况；
- 哪些 Capability 缺少可靠数据源；
- 哪些 Multimodal visual types 实际可获得；
- 是否存在大量尚未覆盖的重要机械工业知识；
- Taxonomy 是否偏向教材学科结构而忽略工业实践。

Phase 2 的产出目标是：

> Benchmark Taxonomy v0.2

校准时必须保持以下边界：

- Corpus 分布用于发现覆盖、缺口和来源风险；
- Corpus 分布不能完全决定 Benchmark 的能力目标；
- Domain 调整应说明依据、影响和历史兼容方式；
- Taxonomy 调整不得未经评审地改变 Project Charter 的三个 Benchmark Track；
- 40% / 30% / 30% 仍属于 Sampling Target，不能由 Taxonomy 单独决定。

## 16. Design Inspirations

以下内容只作为设计参考，不表示直接复制其 Taxonomy，也不声称本设计完全来自某一个 Benchmark。

### 16.1 MechVQA

启发包括：

- Capability 与 Task 分层；
- Recognition / Reasoning / Judging；
- 机械图纸 Fine-grained Tasks；
- Difficulty 分层；
- 数据审计与去重。

### 16.2 MMMU / MMMU-Pro

启发包括：

- Discipline / Subject / Subfield 多级领域分类；
- Domain-specific knowledge + reasoning；
- 视觉对象多样化；
- 多模态问题必须真正依赖视觉信息。

### 16.3 MMLU-Pro

启发包括：

- 减少过于简单的问题；
- 增强推理要求；
- 提高 Benchmark 区分度。

### 16.4 Industry-oriented Benchmark Design

启发包括：机械工业 Benchmark 不应只按照学校课程划分，还需要关注：

- standards；
- selection；
- process；
- quality；
- diagnosis；
- engineering calculation。

这些内容在本项目中作为设计参考和讨论起点，最终分类仍需经过本项目的 Taxonomy Governance 和 Phase 2 Calibration。

Phase 2 的 Source Selection 将从 Candidate Source Corpus 中形成用于后续 Benchmark 构建的 Benchmark Source Corpus；具体选择字段、隔离策略和数据处理方式不在本文件中决定。

## 17. References / Traceability

下表记录本 Taxonomy v0.1 的外部设计参考。参考资料只用于说明设计启发和追溯，不直接复制其 taxonomy；版本或日期未被可靠记录的，明确保留为 TBD。

| Benchmark name | Reference URL / paper identifier | Consulted version / date | 本项目实际借鉴内容 | 说明 |
| --- | --- | --- | --- | --- |
| MechVQA | https://github.com/xiaofengShi/MechVQA?utm_source=chatgpt.com | Version: TBD；consulted date: 2026-09-11 | Capability 与 Task 分层；Recognition / Reasoning / Judging；机械图纸 Fine-grained Tasks；视觉推理与数据审计思路 | 不直接复制其 taxonomy |
| IndustryBench | https://huggingface.co/datasets/alibaba-multimodal-industrial-ai/IndustryBench?utm_source=chatgpt.com | Version: TBD；consulted date: 2026-09-11 | 工业知识能力不只按行业划分，并关注标准术语、工艺原理、选型、安全、质量、故障诊断和工程计算等能力方向 | 不直接复制其 taxonomy |
| MMMU | TBD - reference link to be added during documentation review | Version/date: TBD | 多级学科/主题/子领域组织和视觉对象多样化的设计启发 | 不直接复制其 taxonomy |
| MMMU-Pro | TBD - reference link to be added during documentation review | Version/date: TBD | 多模态问题的视觉依赖和综合推理设计启发 | 不直接复制其 taxonomy |
| MMLU-Pro | https://arxiv.org/abs/2406.01574?utm_source=chatgpt.com；arXiv:2406.01574 | Version: TBD；consulted date: 2026-09-11 | 减少过于简单和噪声题，增强推理要求，关注 Benchmark 区分度 | 不直接复制其 taxonomy |

## 18. 当前范围与禁止事项

Taxonomy v0.1 只进行理论分类设计：

- 不处理 Candidate Source Corpus；
- 不编写 PDF 解析代码；
- 不自动生成 Benchmark 问题；
- 不实现评测代码；
- 不根据未知的 Candidate Source Corpus 分布调整题目比例；
- 不擅自决定仍为 TBD 的项目决策；
- 不开始 Data Specification 的正式设计。

本文件中的 Domain、Capability、Task、Modality、Difficulty、Answer Type 和 Coverage Matrix 均属于 v0.1 理论设计，后续必须经过项目评审和 Phase 2 Calibration。

## 19. Open Questions

以下问题尚未完全正式决定；尚未决定部分保持 TBD：

1. D03 / D04 是否需要长期分开？—— TBD
2. D12 是否应该是 Domain 还是 Cross-cutting Capability / Metadata？—— TBD
3. Fine-grained Capability 是否允许一个 Item 多标签？—— TBD
4. 一个 Item 是否允许 Secondary Domain？—— TBD
5. Calculation + Multimodal 混合题：v0.1 已规定 visual dependency 优先进入 T3；仍待 Data Specification 决定 secondary capability、cross-cutting skill 和 multi-label metadata 如何表达。—— TBD
6. Multimodal visual types 是否需要进一步划分？—— TBD
7. Difficulty Dimensions 哪些必须进入最终 Schema？—— TBD
8. Domain Level 2 是否需要在 Phase 2 增删？—— TBD
9. 是否需要增加 Electrical / Industrial Engineering 边界说明？—— TBD
10. Taxonomy v0.2 如何根据 Corpus Inventory 校准而不被 Corpus 分布绑架？—— TBD
11. 是否需要正式引入 `cross_cutting_skill_tags`，记录 calculation、reasoning、diagnosis、selection、compliance、spatial_reasoning 等跨 Track 技能？—— TBD
