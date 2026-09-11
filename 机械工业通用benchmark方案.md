# 机械工业通用benchmark方案

你现在手里的“7 万本机械工业 PDF”是一个非常有价值的起点，但它本身不是 Benchmark。更准确的定位应该是：

> 7 万本 PDF = Benchmark 的候选知识源库
> Benchmark = 从知识源库中经过分类、抽取、构题、验证、去重、分层后形成的一小套高质量评测集

如果目标是做一套真正能长期评测 GLM、Qwen、GPT、Claude 等模型机械工业能力的 Benchmark，我建议按照下面这套架构来做。

# 一、先定义你究竟要测什么

我建议把第一版 Benchmark 定义成：

**Mechanical Industry General Knowledge Benchmark（机械工业通用知识基准）**

一级能力暂时就定你现在这三个，非常合适：

| 一级能力                 | 建议占比 | 核心问题                                 |
| ------------------------ | -------- | ---------------------------------------- |
| Mechanical Knowledge     | 40%      | 模型懂不懂机械工业知识                   |
| Engineering Calculation  | 30%      | 模型会不会根据机械知识进行计算           |
| Multimodal Understanding | 30%      | 模型能不能理解机械图、表格、示意图并推理 |

但一级能力下面一定要继续拆。

例如可以形成这样的 taxonomy：

| 一级能力 | 二级能力     | 典型问题               |
| -------- | ------------ | ---------------------- |
| 知识     | 概念与术语   | 什么是过盈配合         |
| 知识     | 原理理解     | 为什么滚动轴承需要预紧 |
| 知识     | 材料         | 40Cr 调质处理的目的    |
| 知识     | 制造工艺     | 铣削与车削适用场景     |
| 知识     | 机械设计     | 齿轮模数的意义         |
| 知识     | 公差与测量   | H7/g6 表示什么         |
| 知识     | 液压/气动    | 溢流阀作用             |
| 知识     | 标准与规范   | 某符号或标准定义       |
| 计算     | 公式直接计算 | 功率、扭矩、转速换算   |
| 计算     | 多步工程计算 | 传动比→转速→扭矩       |
| 计算     | 单位换算     | MPa、N/mm² 等          |
| 计算     | 参数选择     | 给定载荷计算轴径       |
| 计算     | 表格+公式    | 查表后计算             |
| 多模态   | 图形识别     | 判断零件类型           |
| 多模态   | 工程图识别   | 读取尺寸、公差、粗糙度 |
| 多模态   | 表格理解     | 从性能表查参数         |
| 多模态   | 图表理解     | 应力应变曲线分析       |
| 多模态   | 几何计算     | 根据图纸尺寸计算       |
| 多模态   | 投影视图     | 三视图、剖视图理解     |
| 多模态   | 结构推理     | 判断零件装配关系       |

这实际上已经非常接近一个 Benchmark 的骨架了。

MechVQA 的设计很值得你参考，它不是简单做“看图回答问题”，而是把机械图纸能力进一步拆成 Recognition、Reasoning、Judging，并细分到尺寸标注、投影、多视图、结构理解、几何计算等任务。它目前公开的 Benchmark 约包含 3,300 张机械图和 21K QA。([GitHub](https://github.com/xiaofengShi/MechVQA?utm_source=chatgpt.com))

IndustryBench 也值得借鉴，它把工业知识进一步标注为“标准术语、工艺原理、选型替代、安全、质量计量、故障诊断、工程计算”等能力，而不是只划行业。([Hugging Face](https://huggingface.co/datasets/alibaba-multimodal-industrial-ai/IndustryBench?utm_source=chatgpt.com))

这两个设计思想建议直接吸收到你的方案中。

------

# 二、7 万本 PDF 最重要的第一步不是出题，而是做“知识源盘点”

你现在最大的不确定性其实是：

> 我到底拥有哪一些机械知识？

7 万本 PDF 很多，但质量未知、类别未知、重复情况未知。如果现在直接让大模型批量出题，最后很可能得到几十万道质量参差不齐的题。

因此第一步应该建立：

**Mechanical Corpus Inventory**

即机械工业知识库画像。

不要先解析全部正文，可以先对 7 万份 PDF 做低成本扫描。

最终形成类似：

```text
document_id
file_name
title
year
publisher
document_type
domain
subdomain
page_count
language
scan_or_text_pdf
ocr_quality
formula_count
table_count
image_count
drawing_count
duplicate_group
copyright_status
quality_score
```

其中 `document_type` 非常重要：

```text
教材
手册
标准
行业规范
论文
技术报告
产品手册
培训材料
考试资料
未知
```

Benchmark 的知识来源，我会优先级排序成：

**标准 / 权威手册 / 高质量教材 > 行业规范 > 技术报告 > 论文 > 普通网络资料。**

因为 Benchmark 最大的问题不是“题少”，而是：

**Ground Truth 到底是不是真的正确。**

------

# 三、不要直接对 7 万本 PDF 全量 MinerU

比较合理的是分两层。

第一层先做“轻解析”。

抽：

```text
文件名
PDF metadata
目录
前几页
页数
文本密度
图片数量
公式数量
```

然后模型分类：

```text
机械设计
机械制造
工程力学
材料
液压
公差
轴承
齿轮
CAD/CAM
测量
焊接
机床
……
```

得到整个语料库的分布。

假设最终发现：

```text
机械制造  18%
材料      15%
机械设计  14%
工程力学  12%
液压      8%
测量      7%
……
```

这时候才知道 Benchmark 应该怎么采样。

第二层再对筛选出的高价值 PDF 做 MinerU 等高质量解析。

我会建议第一版可能只选：

**2,000～5,000 本高质量 PDF。**

根本没有必要一开始处理 70,000 本。

------

# 四、PDF 解析结果不要只保存 Markdown

这个问题对你后面的多模态 Benchmark 非常重要。

建议数据结构至少保留：

```text
PDF
 ├── document
 ├── page
 │    ├── text blocks
 │    ├── formulas
 │    ├── tables
 │    ├── figures
 │    └── page image
 │
 └── provenance
      ├── pdf_id
      ├── page
      ├── bbox
      └── source
```

也就是说：

每一道题必须能反查：

> 这道题来自哪本书、哪一页、哪个公式、哪张图、哪段文字。

例如：

```json
{
  "source_doc": "机械设计手册_v3",
  "page": 328,
  "bbox": [120, 350, 860, 950]
}
```

这叫 **provenance / data lineage**。

这一步以后会救你的命。

因为模型自动生成 20,000 道题以后，突然发现一道答案似乎有问题，没有 provenance 基本无法检查。

------

# 五、知识问答不要全部生成成开放问答

第一版 Benchmark，我建议知识类以：

**客观题为主，开放题为辅。**

例如 1,800 道知识题可以设计成：

| 类型      | 数量 |
| --------- | ---- |
| 单选题    | 900  |
| 多选/判断 | 300  |
| 短答案    | 400  |
| 原理推理  | 200  |

不要全部做：

> “请解释一下滚动轴承的作用。”

这种题。

因为答案可以有无数种表达，最后很依赖 LLM-as-Judge。

更好的 Benchmark 问法是：

> 深沟球轴承最主要承受以下哪种载荷？

或者：

> H7/g6 通常属于哪种配合？

这样 Ground Truth 明确，评测稳定。

OpenCompass 本身就支持 MCQ、QA、数学验证以及规则+LLM Judge 级联评测，所以这一部分非常容易接入。([OpenCompass](https://doc.opencompass.org.cn/advanced_guides/custom_dataset.html?utm_source=chatgpt.com))

------

# 六、计算题反而是你这套 Benchmark 很有价值的部分

我建议把“机械工程计算”做成你的特色。

因为纯知识问题，大模型可能已经记忆得很好。

真正能区分模型的是：

> 能否理解机械工程问题 → 选公式 → 代入 → 单位转换 → 得到工程结果。

比如：

```text
某电机功率 P = 7.5 kW，
转速 n = 1450 r/min，
求输出轴理论扭矩。
```

Ground Truth 可以程序计算：

$T=\frac{9550P}{n}$

答案：

$T \approx 49.4 N·m$

这类题最好不要让 LLM 决定 Ground Truth。

应该：

```text
PDF
↓
提取公式
↓
公式结构化
↓
参数范围
↓
自动生成参数
↓
Python/SymPy计算
↓
生成Ground Truth
```

例如形成：

```json
{
  "formula_id": "shaft_torque_001",
  "variables": {
    "P": 7.5,
    "n": 1450
  },
  "units": {
    "P": "kW",
    "n": "rpm"
  },
  "answer": 49.3965,
  "unit": "N*m",
  "tolerance": 0.5
}
```

评分根本不需要 Judge：

```text
| prediction - ground_truth | < tolerance
```

即可。

这种题的可信度会比 LLM 自动生成答案高得多。

LightAlloy-Bench 就使用了类似的思路：先从大量资料中结构化抽取数据，再构建知识题和“成分—工艺—性能”的推理任务。结果显示模型在基础知识和真正工程推理上的表现差异很明显。([DOI](https://doi.org/10.1016/j.jma.2026.102127?utm_source=chatgpt.com))

------

# 七、计算题最好采用“参数化题目”

这是我特别建议你做的一点。

不要只有：

```text
P=7.5kW
n=1450rpm
```

而是模板：

```text
某电机功率为 {P} kW，
转速为 {N} rpm，
求理论输出扭矩。
```

然后：

```text
P ∈ [2.2, 4, 5.5, 7.5, 11, 15]
N ∈ [720, 960, 1450, 2900]
```

可以动态生成很多版本。

Benchmark 固定其中一部分。

好处非常大：

第一是降低数据泄漏影响。

第二是测真正的计算，而不是背答案。

第三是以后可以更新 Benchmark。

这和 LiveBench “持续更新题目、尽量避免测试集污染”的思想是一致的。数据污染已经是当前 LLM Benchmark 非常严重的问题。([arXiv](https://arxiv.org/abs/2406.19314?utm_source=chatgpt.com))

------

# 八、多模态不要只做 OCR

这是很多工业 Benchmark 非常容易犯的错误。

例如给一张图：

> 图中的文字是什么？

这个基本是在测 OCR。

真正有价值的是：

```text
图 → 信息提取 → 机械知识 → 推理 → 答案
```

例如给一张工程图：

> 图中 φ25 H7 孔与 φ25 g6 轴装配后属于什么类型的配合？

模型需要：

看懂图纸
→ 识别公差
→ 理解 H7/g6
→ 机械知识推理
→ 得到答案。

这才是工业多模态能力。

MechVQA 的任务设计就很值得参考，目前包含尺寸标注、几何计算、投影视图、结构理解、文本/表格等任务。([Hugging Face](https://huggingface.co/datasets/XiaofengAlg/MechVQA?utm_source=chatgpt.com))

另外可以借鉴一个非常有用的检测方法：

**Image Dependency Test**

把图片去掉，只给问题。

如果模型仍然能非常高概率答对，那么这道题可能并没有真正测试视觉能力。

理想情况应该是：

```text
有图：80%
无图：20%
```

而不是：

```text
有图：85%
无图：80%
```

后者其实基本是在测语言知识。

------

# 九、我建议第一版不要做十几万题

第一版建议：

**3,000～5,000 道。**

例如非常现实的一版：

| Benchmark V1 | 数量  |
| ------------ | ----- |
| Knowledge    | 1,800 |
| Calculation  | 1,200 |
| Multimodal   | 1,000 |
| 总计         | 4,000 |

4,000 道高质量题，已经足够评测模型。

Benchmark 不是 SFT。

SFT 数据可能需要几十万、几百万。

Benchmark 更重要的是：

**覆盖度 + 正确性 + 区分度。**

MMLU-Pro 的设计思路也强调清理过于简单和噪声题，让测试更具有区分度，而不是简单扩大题量。([arXiv](https://arxiv.org/abs/2406.01574?utm_source=chatgpt.com))

------

# 十、每道题建议建立完整的 Benchmark Schema

不要只存：

```json
{
  "question": "...",
  "answer": "..."
}
```

至少应该做到：

```json
{
  "id": "MIGB_CALC_000001",

  "domain": "mechanical_design",
  "subdomain": "gear",

  "capability": "engineering_calculation",
  "task": "gear_ratio",

  "difficulty": "medium",

  "question_type": "numeric",

  "question": "...",

  "answer": {
    "value": 48.6,
    "unit": "N*m",
    "tolerance": 0.5
  },

  "source": {
    "document_id": "...",
    "page": 328,
    "bbox": []
  },

  "formula_id": "...",

  "requires_image": false,

  "generation_method": "template",

  "verification": {
    "rule_checked": true,
    "llm_checked": true,
    "human_checked": false
  }
}
```

以后所有：

数据治理
Leaderboard
错误分析
模型能力雷达图
Difficulty 分析

都会依赖这些 metadata。

------

# 十一、题目生成建议采用“LLM 生成 + 程序验证”，而不是纯 LLM

整个流水线建议变成：

```text
70000 PDFs
        ↓
文档扫描 / 去重 / 分类
        ↓
机械知识 Taxonomy
        ↓
高质量 PDF 筛选
        ↓
MinerU / Layout Parsing
        ↓
文本 / 公式 / 表格 / 图片
        ↓
候选知识单元
        ↓
LLM 生成候选问题
        ↓
规则验证
        ↓
Ground Truth 验证
        ↓
多模型交叉验证
        ↓
质量过滤
        ↓
人工抽检
        ↓
Benchmark
```

关键在于：

**LLM 是出题助手，而不是最终裁判。**

------

# 十二、质量控制建议至少做四层

这部分决定你的 Benchmark 最终专业不专业。

第一层是 Source Quality，也就是原始 PDF 是否可信。

第二层是 Question Quality，检查题目有没有歧义、信息是否充分、是不是太简单。

第三层是 Answer Verification，计算题程序验证，知识题回到原文验证，多模态题回到原图验证。

第四层是 Model Validation。

这里可以非常巧妙：

拿不同能力模型跑，例如：

```text
小模型
中等模型
Frontier Model
```

然后观察。

如果：

```text
所有模型100%
```

题可能太简单。

如果：

```text
所有模型0%
```

可能题错、过难或者信息不足。

真正有价值的是能产生模型差异的题。

------

# 十三、Difficulty 不要让 LLM 随便标 Easy/Medium/Hard

最好建立规则。

例如 Knowledge：

```text
Easy：直接事实/定义
Medium：概念应用
Hard：跨知识点推理
```

Calculation：

```text
Easy：一步公式
Medium：2~3步
Hard：多公式 + 单位转换 + 条件判断
```

Multimodal：

```text
Easy：视觉识别
Medium：视觉 + 知识
Hard：视觉 + 多步工程推理
```

模型跑完以后还可以根据实际通过率重新校准难度。

------

# 十四、你必须现在就考虑“数据污染”

这个项目很可能还有另一个用途：

你们可能会拿机械领域 PDF 去 CPT/SFT。

这里会出现一个严重问题：

```text
Benchmark题目来源
       ↓
同样的PDF
       ↓
进入模型CPT/SFT
```

这样评测就污染了。

所以从项目第一天就应该划：

```text
70k PDF
 │
 ├── Training Corpus
 │
 └── Benchmark Source Corpus
```

Benchmark Source Corpus 中的 PDF：

**禁止进入 CPT/SFT。**

而且去重要在“书级别”做。

例如：

```text
机械设计手册 第5版
机械设计手册 第6版
机械设计手册 扫描版
```

不能一个进训练，一个进测试。

需要：

```text
book-family split
```

而不仅是 question-level split。

如果以后这个 Benchmark 对外发布，我甚至建议：

```text
Public Dev Set       20%
Private Test Set     80%
```

对外只公布部分题。

真正排行榜跑 Private Test。

这是降低 benchmark contamination 最有效的方案之一。

------

# 十五、评分方式不要只有一个 Accuracy

建议最终报告至少长这样：

```text
Mechanical Benchmark Score
              72.8

Knowledge
              82.1

Calculation
              65.3

Multimodal
              70.9
```

下面再展开：

```text
Mechanical Design       79.2
Manufacturing            75.1
Materials                83.2
Mechanics                64.3
Tolerance & Metrology    71.2
Hydraulics               78.4
...
```

以及：

```text
Easy     91.2
Medium   73.4
Hard     42.8
```

这样 Benchmark 才真正具有分析价值。

总分我反而建议：

**Knowledge / Calculation / Multimodal 做 Macro Average。**

例如：

$Score = \frac{Knowledge+Calculation+Multimodal}{3}$

而不是因为知识题多就自动权重大。

------

# 十六、关于 OpenCompass，我现在仍然建议你用，但采用“双框架”

结合你前面问我的 OpenCompass，我现在会给一个比较明确的方案。

文本和数学：

**OpenCompass**

多模态：

**VLMEvalKit**

原因是 OpenCompass 当前自定义 ChatML 快速评测路径虽然展示了 image 类型的数据格式，但官方文档仍明确注明当前该路径“不支持多模态评测”。而 OpenCompass 团队另外维护的 VLMEvalKit 就是专门用于 VLM/MLLM 评测的，目前支持大量视觉语言模型和 Benchmark。([OpenCompass](https://doc.opencompass.org.cn/advanced_guides/custom_dataset.html?utm_source=chatgpt.com))

因此你的架构完全可以是：

```text
             Benchmark Dataset
                    │
         ┌──────────┴──────────┐
         │                     │
       Text                  Vision
         │                     │
   OpenCompass           VLMEvalKit
         │                     │
         └──────────┬──────────┘
                    │
              Result DB
                    │
              Leaderboard
```

不要为了“统一框架”强行把所有东西塞进一个工具。

Benchmark 的 dataset/schema 才是核心。

评测框架只是 runner。

------

# 十七、如果让我来推进这个项目，我会按这个节奏做

| 阶段     | 工作                     | 产出                      |
| -------- | ------------------------ | ------------------------- |
| Phase 0  | 明确 Benchmark 目标      | Benchmark Definition      |
| Phase 1  | 7 万 PDF 盘点            | Corpus Inventory          |
| Phase 2  | 机械领域 taxonomy        | Capability Taxonomy       |
| Phase 3  | 选 2k～5k 高质量 PDF     | Source Corpus V1          |
| Phase 4  | MinerU 等结构化解析      | Text/Table/Image/Formula  |
| Phase 5  | 先生产 500 道 Pilot      | Benchmark Pilot           |
| Phase 6  | 跑 5～10 个代表模型      | Difficulty/Quality Report |
| Phase 7  | 清洗、修改 taxonomy      | Benchmark Spec V1         |
| Phase 8  | 扩展到约 4,000 道        | Benchmark V1              |
| Phase 9  | OpenCompass + VLMEvalKit | Evaluation Harness        |
| Phase 10 | 自动生成评测报告         | Leaderboard               |

其中有一个原则：

**不要一上来做 4,000 道。**

先做：

**500 道 Pilot。**

比如：

```text
Knowledge        200
Calculation      150
Multimodal       150
```

拿 GPT、Claude、Qwen、GLM、DeepSeek 等不同模型真正跑一遍。

你马上就会发现大量之前设计阶段想不到的问题：

题太简单
题有歧义
图像裁剪不合理
单位问题
答案格式问题
Judge 不稳定
模型猜答案
题目不依赖图片
不同领域分布失衡。

Pilot 修好以后再扩量。

------

# 十八、你现在最应该做的，不是“开始让模型从 7 万 PDF 出题”

你现在应该先完成三份东西：

1. **《机械工业通用 Benchmark 能力体系设计》**

定义：

```text
Domain
Capability
Task
Difficulty
Question Type
Metric
```

1. **《Benchmark 数据构建规范》**

定义：

```text
PDF怎么筛
题怎么生成
答案怎么生成
source怎么保存
如何审核
如何去重
如何避免污染
```

1. **500 道 Benchmark Pilot**

这 500 道题才是后面整个项目真正的验证。

如果这三个东西确定了，你后面的 7 万 PDF、MinerU、LLM 自动出题、OpenCompass，本质上都只是工程实现问题。

我给你一个最终的项目结构建议：

```text
Mechanical-Industry-Benchmark/
│
├── docs/
│   ├── benchmark_definition.md
│   ├── taxonomy.md
│   ├── data_spec.md
│   └── evaluation_spec.md
│
├── corpus/
│   ├── metadata/
│   └── source_registry/
│
├── pipeline/
│   ├── pdf_parser/
│   ├── knowledge_extractor/
│   ├── question_generator/
│   ├── formula_generator/
│   ├── multimodal_generator/
│   └── quality_checker/
│
├── benchmark/
│   ├── knowledge.jsonl
│   ├── calculation.jsonl
│   └── multimodal.jsonl
│
├── evaluation/
│   ├── opencompass/
│   ├── vlmevalkit/
│   └── evaluators/
│
└── reports/
    └── leaderboard/
```

如果让我评价你目前的项目状态，我认为你现在其实还处在 **Benchmark Definition + Data Strategy** 阶段，而不是数据构建阶段。

这个阶段最需要优先确定的不是“用什么框架”，也不是“用什么模型出题”，而是：

> **Mechanical Industry Benchmark 到底测哪些能力，每种能力用什么题测，以及什么样的数据才算一条合格的 Benchmark 数据。**

这三个问题一旦定下来，后面 7 万 PDF 应该怎么利用就会变得非常清楚。