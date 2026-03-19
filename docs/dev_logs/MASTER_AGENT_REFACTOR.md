# Master Agent 重构说明

## 📝 重构目标

将 `master.py` 从简单的分支选择函数改造为真正的 AI Agent，使用 LLM 和 skill 来判断复杂度。

## 🔄 主要变化

### 1. 新增 Skill 文件

**文件**: `memory/skills/master/complexity_analysis_skill_v1.md`

**内容**：
- 复杂度分类标准（Simple/Complex）
- 简化：不再使用 "standard"（太中性）
- 优先级：章节名称匹配 > 内容分析
- 详细的判断标准和示例

### 2. Master Agent 重写

**旧实现**（分支函数）：
```python
def master_node(state: MasterState) -> MasterState:
    """规则匹配，非 AI Agent"""
    complexity = memory.analyze_complexity_by_rules(section_title)
    # 简单的 if-else 逻辑
```

**新实现**（真正的 AI Agent）：
```python
class MasterAgent:
    """真正的 AI Agent，使用 LLM 判断复杂度"""
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # 加载 Complexity Analysis Skill
        skill_content = self.memory.load_skill("master")
        
        # 构建 prompt
        prompt = f"""
        # Complexity Analysis Skill (v{MASTER_SKILL_VERSION})
        {skill_content}
        
        # 输入内容
        【章节名称】：{section_title}
        【验证方案】：{protocol_content}
        【GLP 报告参考】：{original_report_content}
        
        # 任务要求
        1. 严格按照 Complexity Analysis Skill 中的判断标准
        2. 只输出 "simple" 或 "complex"，不要 "standard"
        3. 输出 JSON 格式
        """
        
        # 使用 LLM (Grok) 生成
        response = self.client.chat.completions.create(...)
        result = json.loads(response.choices[0].message.content)
        
        return {
            "complexity": result["complexity"],
            "route": result["route"],
            "reasoning": result["reasoning"]
        }
```

### 3. 复杂度简化

**旧**: Simple/Standard/Complex（三级）
**新**: Simple/Complex（二级）

**理由**：
- "standard" 太中性，不好区分
- 简化为两级更容易判断
- AI Agent 自行判断，不需要"标准"作为缓冲

### 4. 文件修改清单

#### config.py
```python
# 新增
MASTER_SKILL_VERSION = "1.0"
```

#### memory_manager.py
```python
# 修改 master skill 加载路径
def load_skill(self, skill_type: str, skill_name: str = None) -> str:
    if skill_type == "master":
        skill_file = self.skills_dir / "master" / f"complexity_analysis_skill_v{MASTER_SKILL_VERSION}.md"
```

#### nodes/master.py
- ✅ 完全重写为 MasterAgent 类
- ✅ 使用 OpenAI client (Grok)
- ✅ 加载 Complexity Analysis Skill
- ✅ 构建 prompt（包含完整内容）
- ✅ 调用 LLM 并解析 JSON 结果
- ✅ 返回 complexity, route, reasoning

#### main.py
```python
# 更新导入
from nodes.master import (
    MasterState, format_verify_node,
    should_route_simple, should_retry_complex, MasterAgent  # 新增
)

# 更新初始化
self.master = MasterAgent()  # 新增

# 更新 workflow
workflow.add_node("master", self.master)  # 使用 agent 实例
```

## 🎯 新架构对比

| 特性 | 旧实现 | 新实现 |
|------|---------|---------|
| 类型 | 分支函数 | AI Agent |
| 复杂度判断 | 规则匹配 | LLM + Skill |
| 复杂度级别 | Simple/Standard/Complex | Simple/Complex |
| 代码复杂度 | 低 | 中（需要 LLM 调用） |
| 灵活性 | 固定规则 | AI 自行判断 |
| 输出质量 | 依赖规则准确性 | AI 理解上下文判断 |
| 成本 | 0 (无 LLM 调用) | ~$0.002 (Grok 调用) |

## 📊 数据流

### 旧数据流（规则匹配）
```
section_title
  ↓ master_node (规则）
  ↓ 简单 if-else
  ↓ complexity, route
```

### 新数据流（AI Agent）
```
section_title
protocol_content
original_report_content
  ↓ MasterAgent
  ↓ load_skill("master")
  ↓ build prompt
  ↓ Grok LLM call
  ↓ JSON parse
  ↓ complexity, route, reasoning
```

## ✅ 优势

1. **更智能的判断**：AI 可以理解上下文，而不仅仅是匹配关键词
2. **更好的适应性**：新类型的章节也能通过 AI 理解判断
3. **更清晰的语义**：只保留 simple/complex，消除 neutral 的 standard
4. **Skill 驱动**：与 writer/reviewer 一致，统一的架构
5. **可解释性**：AI 提供明确的理由

## ⚠️ 注意事项

1. **成本增加**：每个章节多一次 LLM 调用（约 $0.002）
2. **时间增加**：LLM 调用需要时间（约 1-2 秒）
3. **错误处理**：如果 LLM 调用失败，默认为 complex（保守策略）

## 🔍 Skill 文件详解

### 复杂度分类

#### Simple（简单章节）
**定义**：纯格式化内容，无需操作步骤或复杂判断

**特征**：
- 缩略词表、术语表
- 参考文献、版本历史
- 目录、附录
- 致谢、签字页
- 内容少于 200 字
- 纯信息展示，无操作步骤

#### Complex（复杂章节）
**定义**：需要统计分析、多步骤操作或复杂验证的章节

**特征**：
- 方法学验证
- 稳定性研究
- 系统适用性测试
- 数据分析与统计
- 批内/批间准确度及精密度
- 基质效应分析
- 回收率验证
- 包含"计算"、"统计"、"分析"、"验证"等关键词
- 内容超过 1000 字
- 有多个嵌套的子步骤

### 判断标准

**优先级 1：章节名称匹配**
- 直接判定为 Simple 的章节（列表）
- 直接判定为 Complex 的章节（列表）

**优先级 2：内容分析**
- 当章节名称无法确定时，分析验证方案和 GLP 报告内容
- 根据 Simple/Complex 特征判断
- 只输出 simple 或 complex

## 📝 输入内容格式

```python
【章节名称】：{section_title}

【验证方案】：
{protocol_content[:3000]}

【GLP 报告参考】：
{original_report_content[:3000]}

{template_context}  # 如果有现有模板
```

## 📤 输出格式

```json
{
  "complexity": "simple|complex",
  "route": "simple_path|complex_path",
  "reasoning": "判断依据（50字以内）"
}
```

## ✅ 验证结果

### 编译检查
- ✅ main.py: 编译成功
- ✅ nodes/master.py: 编译成功
- ✅ memory_manager.py: 编译成功
- ✅ config.py: 编译成功

### 文件检查
- ✅ Skill 文件创建：`memory/skills/master/complexity_analysis_skill_v1.md`
- ✅ MasterAgent 重写完成
- ✅ 所有引用更新完成

### 导入检查
- ✅ MasterAgent 导入正确
- ✅ MASTER_SKILL_VERSION 导入正确
- ✅ 所有节点初始化正确

## 🚀 运行方式

```bash
cd sop_deeplang
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 API Keys
python main.py
```

## 📚 相关文件

1. `nodes/master.py` - Master Agent 实现
2. `memory/skills/master/complexity_analysis_skill_v1.md` - 复杂度分析 Skill
3. `memory_manager.py` - 技能加载管理
4. `config.py` - 配置文件
5. `main.py` - 主程序
