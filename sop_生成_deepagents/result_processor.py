"""
结果处理器 - 解析和保存subagent输出
"""
import json
import re
from memory_manager import MemoryManager

class ResultProcessor:
    def __init__(self, memory_dir="./memory"):
        self.memory = MemoryManager(memory_dir)
    
    def process_result(self, result, experiment_type, section_name):
        """处理agent执行结果并保存到memory"""
        
        # 提取所有消息内容
        sop_content = ""
        score = 3
        
        if result and "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        sop_content += content + "\n"
        
        # 保存规则
        rule_content = self._extract_rules(sop_content, section_name)
        if rule_content:
            rule_id = self.memory.add_rule(experiment_type, section_name, rule_content)
            print(f"✓ 规则: {rule_id}")
        
        # 保存模板
        if sop_content:
            template_path = self.memory.save_template(
                experiment_type, section_name, 
                {"sop": sop_content[:2000]}, score
            )
            print(f"✓ 模板: {template_path}")
        
        # 保存日志
        task_id = self.memory.log_execution({
            "experiment_type": experiment_type,
            "section": section_name,
            "status": "completed",
            "quality_score": score,
            "iterations": 1
        })
        print(f"✓ 日志: {task_id}")
        
        # 保存完整SOP文档
        sop_file = f"memory/sop_templates/{section_name}_完整版.md"
        with open(sop_file, "w", encoding="utf-8") as f:
            f.write(f"# {section_name}\n\n{sop_content}")
        print(f"✓ 文档: {sop_file}")
        
        return sop_content
    
    def _extract_rules(self, content, section_name):
        """从内容中提取规则"""
        if "标准曲线" in section_name:
            return "需包含浓度范围、回归方程、接受标准、R²值"
        elif "准确度" in section_name or "精密度" in section_name:
            return "需包含批内/批间数据、CV值、偏差范围"
        elif "稳定性" in section_name:
            return "需包含储存条件、时间点、稳定性数据"
        return f"{section_name}的标准规则"
