"""
Memory Manager - Memory System for DeepAgent

Manages the memory.md file that stores:
1. Audit Log (迭代记录)
2. Rules (ACE Rules部分)
3. SOP Templates (SOP模板部分)
"""

import os
from typing import List, Dict, Any
from datetime import datetime


class MemoryManager:
    """
    Manages DeepAgent memory system.

    Memory structure:
    - Categories section with three parts:
      1. Audit Log: Iteration history
      2. Rules: Reusable experience rules
      3. SOP Templates: Generated SOPs
    """

    def __init__(self, file_path: str = "deepagent_sop/memory/memory.md"):
        """
        Initialize MemoryManager.

        Args:
            file_path: Path to memory.md file
        """
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create memory.md with initial structure if it doesn't exist."""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self._create_initial_memory()

    def _create_initial_memory(self):
        """Create initial memory.md structure."""
        initial_content = """# DeepAgent Experience Memory

## Last Updated: {date}

## 元信息
- Version: 1.0
- Created: {date}
- Total Insights: 0

---

## Categories

### (1) 审计日志部分（AuditLog）
**用途**：记录轨迹细节、迭代历史、执行统计

暂无迭代记录。

---

### (2) Rules部分（ACE Rules）
**用途**：⭐ 存储可复用的经验规则（DeepAgent的"存储层"）

暂无规则记录。

---

### (3) SOP模板部分（SOPTemplates）
**用途**：存储生成的SOP内容和版本

暂无SOP模板记录。
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

    def read(self) -> str:
        """
        Read complete memory content.

        Returns:
            Full memory.md content as string
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, content: str):
        """
        Write complete memory content (replace entire file).

        Args:
            content: New memory content to write
        """
        # Update Last Updated timestamp
        content = self._update_timestamp(content)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def append(self, content: str):
        """
        Append content to memory.

        Args:
            content: Content to append
        """
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)

    def _update_timestamp(self, content: str) -> str:
        """Update Last Updated timestamp in content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if line.startswith("## Last Updated:"):
                lines[i] = f"## Last Updated: {timestamp}"
                break

        return "\n".join(lines)

    def query_rules(self, sop_type: str = "", chapter_id: str = "") -> List[str]:
        """
        Query relevant rules from memory.

        Args:
            sop_type: SOP type filter (rule_template, simple_insert, complex_composite)
            chapter_id: Chapter ID filter (optional)

        Returns:
            List of rule content strings
        """
        memory_content = self.read()

        # Extract Rules section
        rules_section = self._extract_section(memory_content, "Rules部分")

        if not rules_section or rules_section == "暂无规则记录。":
            return []

        # Filter by sop_type and chapter_id if provided
        # This is a simple implementation - can be enhanced with better parsing
        rules = []
        lines = rules_section.split("\n")

        current_rule = []
        in_rule_block = False

        for line in lines:
            if line.strip().startswith("###### rule-"):
                # Start of a new rule
                if current_rule:
                    rules.append("\n".join(current_rule))
                current_rule = [line]
                in_rule_block = True
            elif in_rule_block:
                current_rule.append(line)

        # Don't forget the last rule
        if current_rule:
            rules.append("\n".join(current_rule))

        # Apply filters
        filtered_rules = []
        for rule in rules:
            include_rule = True

            if sop_type and sop_type not in rule:
                include_rule = False

            if chapter_id and chapter_id not in rule:
                include_rule = False

            if include_rule:
                filtered_rules.append(rule)

        return filtered_rules

    def log_iteration(self, chapter_id: str, iteration_data: Dict[str, Any]):
        """
        Log iteration information.

        Args:
            chapter_id: Chapter ID
            iteration_data: {
                "timestamp": "ISO-8601",
                "version": "Version1/2/3",
                "sop": "SOP内容",
                "sop_id": "sop_xxx",
                "sop_type": "rule_template",
                "curation": {...},
                "metrics": {...},
                "quality_assessment": {...}
            }
        """
        memory_content = self.read()

        # Find Audit Log section
        audit_section = self._extract_section(memory_content, "审计日志部分")

        # Create new iteration entry
        iteration_entry = f"""
##### 迭代记录
- **时间**：{iteration_data.get("timestamp", datetime.now().isoformat())}
- **版本**：{iteration_data.get("version", "Version1")}
- **SOP内容**：{iteration_data.get("sop", "")[:200]}...
- **SOP ID**：{iteration_data.get("sop_id", "N/A")}
- **SOP类型**：{iteration_data.get("sop_type", "unknown")}
- **Metrics**：{iteration_data.get("metrics", {})}
- **质量评估**：{iteration_data.get("quality_assessment", {})}
---

"""

        # Append to Audit Log section
        if "暂无迭代记录。" in audit_section:
            new_audit = audit_section.replace("暂无迭代记录。", iteration_entry)
        else:
            new_audit = audit_section + iteration_entry

        # Replace in memory content
        memory_content = memory_content.replace(audit_section, new_audit)
        self.write(memory_content)

    def save_sop(
        self,
        chapter_id: str,
        sop_type: str,
        sop_content: str,
        version: str = "latest",
        quality_score: float = 0.0,
    ):
        """
        Save SOP to memory.

        Args:
            chapter_id: Chapter ID
            sop_type: SOP type
            sop_content: SOP content
            version: Version identifier
            quality_score: Quality score
        """
        memory_content = self.read()

        # Find SOP Templates section
        sop_section = self._extract_section(memory_content, "SOP模板部分")

        # Create new SOP entry
        sop_entry = f"""
###### {sop_type}类型SOP - {version}
- **章节ID**：{chapter_id}
- **SOP内容**：{sop_content[:200]}...
- **版本**：{version}
- **质量分数**：{quality_score}
- **生成时间**：{datetime.now().strftime("%Y-%m-%d")}
---

"""

        # Append to SOP Templates section
        if "暂无SOP模板记录。" in sop_section:
            new_sop = sop_section.replace("暂无SOP模板记录。", sop_entry)
        else:
            new_sop = sop_section + sop_entry

        # Replace in memory content
        memory_content = memory_content.replace(sop_section, new_sop)
        self.write(memory_content)

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract a section from memory content.

        Args:
            content: Full memory content
            section_name: Section name to extract (e.g., "审计日志部分")

        Returns:
            Section content
        """
        lines = content.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            if section_name in line:
                in_section = True
                section_lines.append(line)
            elif in_section:
                # Check if we've reached the next major section
                if line.startswith("---") and section_lines:
                    break
                section_lines.append(line)

        return "\n".join(section_lines)
