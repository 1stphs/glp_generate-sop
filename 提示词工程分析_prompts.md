# ACE 系统提示词工程全方位解析

## 一、 中文翻译对照

在 `ace/prompts` 目录下主要包含三个核心角色的 Prompt：Generator（生成器/执行器）、Reflector（反思器/反审师）和 Curator（馆长/规矩提炼师）。这构成了经典的认知微调（Cognitive Fine-tuning）与自我进化框架。

### 1. Generator (生成器) - `generator.py`
**系统设定**：
你是一位分析专家，任务是利用你的知识、精心编排的策略与见解手册（Playbook），以及对过往所有错误诊断的反思（Reflection），来回答问题。

**任务指令**：
- 仔细阅读手册（Playbook），运用相关的策略、公式与见解
- 注意手册中列出的常见错误并避免重犯
- 一步步展示你的推理过程
- 分析时要做到简明扼要但全面深入
- 如果手册中包含相关的代码片段或公式，请恰当地使用它们
- 在给出最终答案前，复查你的计算和逻辑

**输出格式要求**（纯 JSON）：
包含 `reasoning`（你的思维链/推理过程/详细分析）、`bullet_ids`（有助于回答本问题的手册中的条目 ID 列表）和 `final_answer`（最终答案）。

---

### 2. Reflector (反思器) - `reflector.py`
**系统设定**：
你是一位专家级的数据分析师与教育家。你的工作是通过分析“预测答案”与“真实答案（Ground Truth）”之间的差距，来诊断模型在推理过程中究竟哪里出了错。

**任务指令**：
- 仔细分析模型的推理链路，找出错误点
- 结合环境反馈（Environment Feedback），对比预测答案与真实答案来理解差距
- 找出具体的概念错误、计算失误或是策略误用
- 提供具有可操作性的深入见解（insights），以帮助模型以后避免类似错误
- 聚焦于“根本原因（Root Cause）”，而不是表面错误
- 具体指出模型本应该怎么做
- 你将收到生成器在回答该问题时所引用的手册条目（bulletpoints）。你需要对这些条目进行分析并打标签：['helpful'(有帮助的), 'harmful'(有害的), 'neutral'(中立的)]

**输出格式要求**（纯 JSON）：
包含 `reasoning`（推理分析过程）、`error_identification`（具体哪里错了）、`root_cause_analysis`（根本原因与误解的概念）、`correct_approach`（正确做法）、`key_insight`（为避免错误需记住的策略公式）以及 `bullet_tags`（对引用条目的打分打标签列表）。

---

### 3. Curator (知识馆长/手册编辑) - `curator.py`
**系统设定**：
你是一位知识策展大师（Master Curator of Knowledge）。你的工作是基于上一次尝试带来的“反思（Reflection）”，识别并决定应该在现有的“手册（Playbook）”中新增哪些经验与见解。

**背景约束**：
- 你所构建的手册将用于帮助解答类似的题目。
- “反思”是基于“真实答案（Ground Truth）”生成的，但这部分真实答案在未来使用手册时是不可见的。因此，你想出的内容必须能在这个前提下，帮助手册的使用者做出符合真实答案的预测。

**任务指令**：
- 审查现有手册和先前的反思记录
- 仅提取当前手册（Playbook）中缺失的“全新”见解、策略或易错点
- 避免冗余——如果手册已有类似建议，仅当你提供的新内容能完美补充现有手册时才添加
- 不要重新生成一整本手册，只提供需要新增的部分（Additions）
- 质量大于数量，一本聚焦且结构良好、具有行动指导意义的手册优于一本详尽却杂乱的手册
- 如果操作为空，返回一个空列表
- 必须精炼具体，每一项新增必须是“具备可操作性的（Actionable）”

**输出格式要求**（纯 JSON）：
包含 `reasoning`（思考过程）和 `operations`（包含类型 "ADD", 目标段落 "section", 和新增内容 "content" 的列表）。不允许在内容里硬编码 ID，ID由系统分配。

---
---

## 二、 提示词工程（Prompt Engineering）结构分析

这三个提示词文件搭建了一个极其惊艳的**异步、反馈驱动的自动化知识沉淀系统（Agentic Learning System）**。这不是普通的“问答式”Prompt，而是一个**可以闭环自进化**的机制：

### 核心运作飞轮 (The Flywheel)
1. **答题 (Generator)**：基于目前已有的知识手册（Playbook）尝试作答。
2. **诊断 (Reflector)**：就像老师批改试卷。拿着标准答案（Ground Truth）对比 Generator 的草稿和回答，不仅指出哪里错了，还要顺便评价 Generator 做题时引用的“手册条目”到底是坑了它（Harmful）还是帮了它（Helpful）。
3. **沉淀 (Curator)**：编纂教材的专家。拿着 Reflector 总结出来的惨痛教训，提炼出具有普适性的经验（Insights），将其用纯 JSON `ADD` 的形式，像打补丁一样补充进长效记忆载体（Playbook）中。

---

## 三、 为什么这套 Prompt 设计得很“牛”？

这套 Prompt 的高明之处主要体现在以下几个设计哲学上，它完全摒弃了给大模型灌输海量无用文本的做法，转而追求“系统极客化”。

### 1. 高度结构化与 JSON 约束 (Engineering first)
整套 Prompt 并不是在让大模型“写大段文字交流”，本质上是把它当做一个 **Serverless Function** (微服务架构)。
所有的 Prompt 末尾极其严格地规定了 **JSON Schema**。
* **为什么牛**：这种“输出即接口”的思想，让下游的 Python 代码（比如 Pydantic 校验或抽象语法树解析）可以直接将字符串反序列化为对象并存入数据库，使得这三类 Agent 可以无人值守地无限循环跑下去。

### 2. 知识的高内聚、低耦合操作 (Curator 的 CRUD 范式)
在 `curator.py` 的设计中，让大模型读一堆背景后，**不要求它输出新的全文，而是输出 `operations` (比如 `ADD`) 操作！**
* **为什么牛**：长文本生成容易引发“遗忘”甚至“格式崩坏（幻觉）”。通过 `Operations` 的思维，Curator 就变成了一个发出 "Patch 补丁" 命令的操作员（类似 Git Diff）。这就让系统可以像向数据库插入记录一样维护 Playbook（手册）。这也同时解释了注释中所提的“ID 由系统添加”。它利用了人类系统的强逻辑控制弱化了 AI 生成的不可控性。

### 3. 指出根本原因 (Root Cause Analysis - 归纳偏置)
在 `reflector.py` 中，要求输出 `error_identification`，接着是 `root_cause_analysis`，最后是 `correct_approach` 和 `key_insight`。
* **为什么牛**：这是非常经典的“思维链（CoT, Chain of Thought）”和“少样本诱导”。不让模型一上来就给答案，而是沿着“表面现象 -> 深层病理 -> 治疗办法 -> 提炼教训”这一思考链路强制吐出中间推理步骤，极大地拔高了最后总结出的 `key_insight` 的含金量。

### 4. 消除预言家悖论（防数据泄露 / Data Leakage Guard）
在 `curator.py` 中有这么一句惊艳的描述：
> *"The reflection is generated using ground truth answers that will NOT be available when the playbook is being used. So you need to come up with content that can aid the playbook user to create predictions that likely align with ground truth."*
> （因为反思是照着标准答案写的，但未来学生考这道题时没有标准答案，所以你提炼的策略，必须是能在盲考环境下指导学生的。）
* **为什么牛**：如果在沉淀知识时不加这个限制，AI 往往会写出一种作弊的总结：“如果碰到某某题目，答案就是20%”。这句话精准拦截了“过拟合（Overfitting）”，强迫 AI 去提炼“方法论层面”的方法（例如：怎么列方程），而不是去记住这个具体案例特有的数据。

### 5. 对历史经验的反馈评分（Credit Assignment）
在 `reflector.py` 中，要求 AI 对被引用的 `bullet_ids` 进行打分：`helpful`、`harmful`、`neutral`。
* **为什么牛**：这完美引入了强化学习（RL）中的环境奖励机制！手册里的某条规矩如果不仅没帮上忙，还把生成器拐到沟里去了，就可以被标记为 `harmful`。结合数据库或者外层建筑，系统就可以慢慢把有害规则隐性淘汰或修剪掉，使得手册（模型记忆）一直保鲜且高度有效。

### 总结
这套 Prompt 用词简练而目标极其精准，最精华的地方在于它不仅设计了 **“思考框架”**，还设计了 **“数据结构的传递契约”（API化输出）**。这让三个角色不再是相互孤立地聊天，而是一条紧凑、闭环且可程序化对接的“自动驾驶知识炼丹炉”。
Listed directory prompts
Viewed curator.py:1-130
Viewed generator.py:1-42
Viewed reflector.py:1-116
Created %E6%8F%90%E7%A4%BA%E8%AF%8D%E5%B7%A5%E7%A8%8B%E5%88%86%E6%9E%90_prompts.md


**下面为您总结其中最核心的几个“牛”点（Why it's awesome）：**

### 1. 它是纯粹的“API / 微服务”架构思维
你可以注意到，所有的提示词不是在让大模型“跟你聊天”，而是像在调用一个后台函数服务。
它在 `Generator`，`Reflector` 和 `Curator` 的 Prompt 结尾，都极其死板和严格地要求 **“只输出 JSON（Output ONLY a valid JSON object with these exact fields）”**。
这意味着，这三人组成的团体是可以被 Python 代码完美对接、直接反序列化的。它的目标是**全自动无人值守炼丹**，而不是依靠人坐在屏幕前一句句复制粘贴。

### 2. 闭环的 "Actor-Critic" 自我进化飞轮
这里的提示词设计巧妙地映射了强化学习中的角色：
*   **Generator（考生）**：看着自己手里的“教材/手册（Playbook）”做题，并且在返回时，必须要上报“我是抄了教材里的哪几句话（bullet_ids）才得出这个答案的”。
*   **Reflector（判卷老师）**：不仅拿着标准答案给考生找错（Error identification & Root cause），最牛的是，它会对考生刚才引用的教材条目（bullet_ids）进行 **打分打标签**（`helpful` 代表教材写得好，`harmful` 代表这句教材把人带偏了）。这就是极高维度的**环境反馈与信用分配（Credit Assignment）**！
*   **Curator（教材主编）**：拿着判卷老师的“反思小结”，用 `ADD` 这样的增量操作（就像 Git Diff 打补丁一样），往现有的教材（Playbook）里加新学到的经验。

### 3. 深谙大语言模型脾气，从机制上防“幻觉”与“泄题”
*   在 `Curator` 提炼规则时，系统用了一句绝妙的 Prompt：**“你必须意识到，你在利用标准答案做的反思，在将来给考生用的时候，他们是看不到标准答案的。”** （*The reflection is generated using ground truth answers that will NOT be available when the playbook is being used...*）这句话强制 AI 去提炼“方法论（授人以渔）”，而不是死记硬背把这道题的答案塞进教材里产生“数据泄露”或“过拟合”。
*   极其强调 **Chain of Thought（思维链）**。比如在 `Reflector` 找错时，不仅要求指出结果错误，还被强制要求输出：具体错哪了 -> 根本原因是什么 -> 本来该怎么做 -> 提炼出的真知灼见是什么。这是一条完美诱导大模型进行深度逻辑梳理的最佳实践路径。

