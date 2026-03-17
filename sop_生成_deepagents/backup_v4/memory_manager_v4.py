"""
优化的记忆管理器 V4 - 支持分章节存储和 JSON 格式
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class MemoryManagerV4:
    """分章节的记忆管理系统"""

    def __init__(self, base_dir: str = "./memory"):
        self.base_dir = Path(base_dir)

        # 三个核心目录
        self.audit_dir = self.base_dir / "audit_logs"
        self.rules_dir = self.base_dir / "rules"
        self.sop_templates_dir = self.base_dir / "sop_templates"

        for dir_path in [self.audit_dir, self.rules_dir, self.sop_templates_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    # ==================== 1. 审计日志（主 Agent）====================

    def log_audit(self, data: Dict[str, Any]) -> str:
        """
        记录审计日志

        Args:
            data: {
                "experiment_type": "LC-MS_MS结构化验证",
                "section_title": "引言",
                "version": "ColdStart_V1",
                "sop_id": "章节ID",
                "quality_assessment": {
                    "is_passed": False,
                    "score": 2.0,
                    "feedback": "..."
                }
            }
        """
        timestamp = datetime.now().isoformat()
        section = self._sanitize(data.get("section_title", "unknown"))

        audit_file = self.audit_dir / f"{section}_audit.jsonl"

        log_entry = {
            "timestamp": timestamp,
            "experiment_type": data.get("experiment_type", ""),
            "section_title": data.get("section_title", ""),
            "version": data.get("version", "V1"),
            "sop_id": data.get("sop_id", "N/A"),
            "sop_summary": data.get("sop_summary", "N/A"),
            "curation": data.get("curation", {"operations_added": 0}),
            "metrics": data.get("metrics", {}),
            "quality_assessment": data.get("quality_assessment", {
                "is_passed": False,
                "score": 0.0,
                "feedback": ""
            })
        }

        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return str(audit_file)

    def get_section_audit_history(self, section_title: str) -> List[Dict]:
        """获取某章节的审计历史"""
        section = self._sanitize(section_title)
        audit_file = self.audit_dir / f"{section}_audit.jsonl"

        if not audit_file.exists():
            return []

        history = []
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                history.append(json.loads(line))

        return history

    # ==================== 2. Rules（Curator）====================

    def save_rules(self, section_title: str, rules: List[Dict[str, str]]) -> str:
        """
        保存章节规则

        Args:
            section_title: 章节名称
            rules: [{"rule_id": "R001", "content": "规则内容"}, ...]
        """
        section = self._sanitize(section_title)
        rules_file = self.rules_dir / f"{section}_rules.json"

        rules_data = {
            "section_title": section_title,
            "updated_at": datetime.now().isoformat(),
            "rules": rules
        }

        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)

        return str(rules_file)

    def load_rules(self, section_title: str) -> Dict:
        """加载章节规则"""
        section = self._sanitize(section_title)
        rules_file = self.rules_dir / f"{section}_rules.json"

        if not rules_file.exists():
            return {
                "section_title": section_title,
                "rules": []
            }

        with open(rules_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def append_rule(self, section_title: str, rule_content: str) -> str:
        """追加规则到章节"""
        rules_data = self.load_rules(section_title)

        rule_id = f"R{len(rules_data['rules']) + 1:03d}"
        rules_data["rules"].append({
            "rule_id": rule_id,
            "content": rule_content,
            "created_at": datetime.now().isoformat()
        })
        rules_data["updated_at"] = datetime.now().isoformat()

        return self.save_rules(section_title, rules_data["rules"])

    # ==================== 3. SOP 模板（持续优化）====================

    def save_sop_template(self, section_title: str, template_data: Dict) -> str:
        """
        保存 SOP 模板

        Args:
            template_data: {
                "core_principles": ["原则1", "原则2"],
                "template": "模板内容",
                "examples": ["示例1", "示例2"]
            }
        """
        section = self._sanitize(section_title)
        template_file = self.sop_templates_dir / f"{section}_template.json"

        sop_data = {
            "section_title": section_title,
            "updated_at": datetime.now().isoformat(),
            "core_principles": template_data.get("core_principles", []),
            "template": template_data.get("template", ""),
            "examples": template_data.get("examples", [])
        }

        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(sop_data, f, ensure_ascii=False, indent=2)

        return str(template_file)

    def load_sop_template(self, section_title: str) -> Dict:
        """加载 SOP 模板"""
        section = self._sanitize(section_title)
        template_file = self.sop_templates_dir / f"{section}_template.json"

        if not template_file.exists():
            return {
                "section_title": section_title,
                "core_principles": [],
                "template": "",
                "examples": []
            }

        with open(template_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_sop_template(self, section_title: str,
                           core_principles: List[str] = None,
                           template: str = None,
                           examples: List[str] = None) -> str:
        """更新 SOP 模板（增量更新）"""
        sop_data = self.load_sop_template(section_title)

        if core_principles is not None:
            sop_data["core_principles"] = core_principles
        if template is not None:
            sop_data["template"] = template
        if examples is not None:
            sop_data["examples"] = examples

        return self.save_sop_template(section_title, sop_data)

    # ==================== 工具方法 ====================

    def _sanitize(self, name: str) -> str:
        """清理文件名"""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

    def get_all_sections(self) -> List[str]:
        """获取所有已处理的章节"""
        sections = set()

        for file in self.audit_dir.glob("*_audit.jsonl"):
            sections.add(file.stem.replace("_audit", ""))

        return sorted(list(sections))
