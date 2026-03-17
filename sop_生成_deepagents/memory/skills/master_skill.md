# SOP Master Agent Skill v1.0

## 职责
全局编排和复杂度评估

## 复杂度评估规则（基于规则匹配）

### 简单章节（直接判断）
```
缩略词表, 缩写, 参考文献, 版本历史, 修订记录, 目录, 附录
```

### 复杂章节（直接判断）
```
方法学验证, 稳定性研究, 统计分析, 数据分析, 结果与讨论, 质量控制
```

### 标准章节
其他所有章节

## 输出格式
```json
{
    "complexity": "simple|standard|complex",
    "reasoning": "判断依据",
    "route": "simple_path|standard_path|complex_path"
}
```
