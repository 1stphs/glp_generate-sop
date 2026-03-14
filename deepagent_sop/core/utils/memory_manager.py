import os
import re
from typing import List, Dict, Any
from datetime import datetime
import json


class MemoryManager:
    """
    Manages DeepAgent dynamic memory system using structured JSON files.

    Memory structure:
    - deepagent_sop/memory/audit_log/audit_log_{date}.json (按天存储迭代与执行指标, 列表结构)
    - deepagent_sop/memory/rules/rules_{experiment_type}.json (按实验类型存储可复用打怪经验, 字典结构)
    - deepagent_sop/memory/sop_templates/sop_templates_{experiment_type}.json (按实验类型存储标准标品结构, 字典结构)
    
    Guideline files (kept as Markdown):
    - deepagent_sop/memory/audit_log/audit_log.md
    - deepagent_sop/memory/rules/rules.md
    - deepagent_sop/memory/sop_templates/sop_templates.md
    """

    def __init__(self, base_dir: str = "deepagent_sop/memory"):
        self.base_dir = base_dir
        self.audit_dir = os.path.join(self.base_dir, "audit_log")
        self.rules_dir = os.path.join(self.base_dir, "rules")
        self.sop_dir = os.path.join(self.base_dir, "sop_templates")

        os.makedirs(self.audit_dir, exist_ok=True)
        os.makedirs(self.rules_dir, exist_ok=True)
        os.makedirs(self.sop_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize experiment type names for use in filenames."""
        if not name:
            return "默认"
        # On Windows, / \ : * ? " < > | are forbidden.
        return re.sub(r'[\/\\:\*\?"<>\|]', '_', name).strip()

    def _get_audit_file(self) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.audit_dir, f"audit_log_{date_str}.json")

    def _get_rules_file(self, experiment_type: str) -> str:
        safe_name = self._sanitize_filename(experiment_type)
        return os.path.join(self.rules_dir, f"rules_{safe_name}.json")

    def _get_sop_file(self, experiment_type: str) -> str:
        safe_name = self._sanitize_filename(experiment_type)
        return os.path.join(self.sop_dir, f"sop_templates_{safe_name}.json")

    def log_iteration(self, iteration_data: Dict[str, Any]):
        """
        Log iteration information to daily JSON audit log.
        """
        file_path = self._get_audit_file()
        
        # Load existing data or start new list
        data = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = []

        # Prepare entry
        entry = {
            "timestamp": iteration_data.get("timestamp", datetime.now().isoformat()),
            "experiment_type": iteration_data.get("experiment_type", "未知"),
            "version": iteration_data.get("version", "Version1"),
            "sop_id": iteration_data.get("sop_id", "N/A"),
            "sop_summary": str(iteration_data.get("sop", ""))[:200],
            "curation": iteration_data.get("curation", {}),
            "metrics": iteration_data.get("metrics", {}),
            "quality_assessment": iteration_data.get("quality_assessment", {})
        }
        
        data.append(entry)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def query_rules(self, experiment_type: str, chapter_id: str = "") -> List[str]:
        """
        Query structured rules from JSON.
        """
        file_path = self._get_rules_file(experiment_type)
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            return []

        chapters_dict = data.get("chapters", {})
        rules = []

        if chapter_id:
            # Match specific chapter or similar name
            for key, chap_rules in chapters_dict.items():
                if chapter_id in key:
                    for r in chap_rules:
                        rules.append(r.get("content", ""))
        else:
            # Return all rules for the experiment type
            for chap_rules in chapters_dict.values():
                for r in chap_rules:
                    rules.append(r.get("content", ""))

        return rules

    def save_sop(self, experiment_type: str, chapter_id: str, content: Any, version: str = "latest", quality_score: float = 0.0):
        """
        Save SOP template block to structured JSON.
        """
        file_path = self._get_sop_file(experiment_type)
        
        # Load or initialize
        data = {"experiment_type": experiment_type, "templates": {}}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass

        # Ensure correct structure
        if "templates" not in data:
            data["templates"] = {}

        # Prepare template entry
        if chapter_id not in data["templates"]:
            data["templates"][chapter_id] = []
            
        data["templates"][chapter_id].append({
            "version": version,
            "quality_score": quality_score,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": content  # This is the structured dict: {"报告规则": [...], "通用模板": "...", "示例": "..."}
        })
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    def apply_rules_operations(self, experiment_type: str, chapter_id: str, operations: List[Dict[str, Any]]):
        """
        Apply ADD operations to structured JSON Rules.
        """
        if not operations:
            return

        file_path = self._get_rules_file(experiment_type)
        
        # Load or initialize
        data = {"experiment_type": experiment_type, "chapters": {}}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass

        if "chapters" not in data:
            data["chapters"] = {}

        if chapter_id not in data["chapters"]:
            data["chapters"][chapter_id] = []

        for op in operations:
            if op.get("type") == "ADD":
                content = op.get("content", "")
                if not content:
                    continue
                
                # Use a more readable ID format
                rule_id = f"rule-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:20]}"
                data["chapters"][chapter_id].append({
                    "id": rule_id,
                    "content": content,
                    "created_at": datetime.now().isoformat()
                })

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
