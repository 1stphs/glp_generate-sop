# Skill 定义

## 1. 技能元数据 
* **Skill Name**: GLP-Master-SOP-Settler (GLP 报告逻辑分析与落盘专家)
* **适用场景**: 
    1.  **项目启动期**：执行《验证方案》(VP) 与《验证报告样本》(VR) 的结构化对齐与差异扫描。
    2.  **执行调度期**：根据章节特性进行二元复杂度分流，下达任务指令。
    3.  **资产归档期**：对验证通过的通用 SOP 执行“落盘”操作，存入系统长期记忆（Memory）。

## 2. 关键遵守规则 (Key Rules)
1.  **二元裁决律**：禁止输出“中等”或“标准”复杂度。章节属性必须且仅能标记为 `Simple` 或 `Complex`。
2.  **映射绝对化**：VR 中的每一个三级标题或关键逻辑段落，必须在 VP 或原始记录中找到唯一对应的逻辑源头。
3.  **落盘准入制**：写入 Memory 的 SOP 必须满足：一致性偏差 < 2% 且已通过 Simulator 的黑盒盲测。
4.  **保守性原则**：当内容处于判定灰色地带时，默认判定为 `Complex` 以确保审计严谨性。

## 3. 复杂度分类标准 (Complexity Categories)

### 3.1 Simple (简单章节)
* **特征**：纯信息展示，无计算逻辑，无操作步骤，内容高度静态。
* **判定指标**：
    * **关键词匹配**：缩略词表、参考文献、版本历史、目录、附录、致谢、签字页。
    * **文本特征**：字数 < 200 字，文本相似度（VP vs VR）> 95%。
* **路由**：`simple_path` → Writer 直接生成 → Format Verify → 结束。

### 3.2 Complex (复杂章节)
* **特征**：涉及动态推导、统计分析（Mean/CV%）、多步操作或偏差说明。
* **判定指标**：
    * **关键词匹配**：方法学验证、稳定性、准确度、精密度、基质效应、回收率、计算、统计、分析。
    * **变量熵**：包含多个占位符（如 {{日期}}、{{仪器编号}}、{{具体数值}}），且文本相似度 < 70%。
* **路由**：`complex_path` → Writer -> Simulator -> Reviewer -> (FAIL) -> Curator -> 迭代循环。

## 4. 判断逻辑优先级 (Judgment Hierarchy)

1.  **优先级 1：章节名称强制匹配**
    * 预设 `Simple_List` 与 `Complex_List`。若名称命中，直接定级。
2.  **优先级 2：语义与变量熵分析**
    * **文本相似度演算**：计算 VP 与 VR 对应章节的相似度。若相似度低且 VR 中包含大量表格/计算描述，判定为 `Complex`。
    * **逻辑特征扫描**：检测是否含有“计算”、“测定”、“统计”等动作动词，以及是否有层级编号的操作步骤。

## 5. Agent 工作轨迹 (Work Trajectory)

### 第一阶段：拓扑扫描与映射 (Scanning & Mapping)
* **动作**：提取 VP 的预设标准（Acceptance Criteria）与 VR 的实际结构，生成《章节逻辑映射树》。
* **输出**：识别出 VR 中相比 VP 新增的动态变量（如项目编号、实际天平 ID）。

### 第二阶段：二元复杂度裁决 (Complexity Evaluation)
* **动作**：调用“判断标准”对每个映射节点进行定级。
* **标准**：
    * 计算变量密度。
    * 执行文本相似度对比。
* **结果**：生成包含 `complexity` 和 `route` 的任务清单。

### 第三阶段：Pipeline 调度与监控 (Orchestration)
* **动作**：根据路径分发任务给 Writer。实时监控 [Complex] 路径的 Reviewer 评分。
* **仲裁**：若迭代 3 轮仍未达到一致性阈值，Master 强制要求对 SOP 逻辑进行重构。

### 第四阶段：SOP 最终复核与落盘 (Settlement & Write)
* **动作**：对通过 Reviewer 终审的 SOP 片段进行“通用性核验”（确保去除了具体案例数据）。
* **落盘执行**：调用 `write_to_memory` 接口，将 SOP 逻辑块写入 Memory 库。
* **格式要求**：SOP 必须包含：【适用场景】、【数据源提取路径】、【计算/撰写逻辑】、【接受标准】。

## 6. 输出格式 (Output Specification)

```json
{
  "chapter_id": "3.10",
  "chapter_name": "稳定性研究",
  "complexity": "complex",
  "route": "complex_path",
  "reasoning": "涉及 Mean/CV% 统计计算，且包含 VP 未定义的实际执行日期变量，相似度 < 65%",
  "settlement_status": "pending_iteration"
}
```