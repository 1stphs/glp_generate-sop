"""
Memory Manager V6 - File-based storage for Skills, Templates, and Audit Logs
SOP Generation System - V6 DeepLang
"""

import json
import re
import threading
from pathlib import Path

# Create a module-level lock for thread-safe file operations
_file_lock = threading.Lock()
from typing import Dict, List, Any, Optional
from datetime import datetime
from config_v6 import (
    SKILLS_DIR,
    TEMPLATES_DIR,
    AUDIT_LOGS_DIR,
    MEMORY_DIR,
    WRITER_SKILL_VERSION,
    SIMULATOR_SKILL_VERSION,
    REVIEWER_SKILL_VERSION,
    CURATOR_SKILL_VERSION,
    CLEAN_OUTPUT,
)


class MemoryManagerV6:
    """
    V6 Memory Manager - Manages three core libraries:
    1. Skill Library (memory/skills/) - Dynamic, versioned .md files
    2. Template Library (memory/sop_templates/) - Final verified SOPs
    3. Audit Log Library (memory/audit_logs/) - Complete execution history
    """

    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.templates_dir = TEMPLATES_DIR
        self.audit_logs_dir = AUDIT_LOGS_DIR

        # Subdirectories for skills
        self.writing_dir = self.skills_dir / "writing"
        self.simulation_dir = self.skills_dir / "simulation"
        self.evaluation_dir = self.skills_dir / "evaluation"
        self.curation_dir = self.skills_dir / "curation"

        # Markdown output directory (separate folder for all MD files)
        self.markdown_dir = MEMORY_DIR / "markdown_sops"

        # Previous SOPs storage (for enhancement iteration)
        self.previous_sops_file = MEMORY_DIR / "previous_sops.json"

        # Ensure all directories exist
        for d in [
            self.skills_dir,
            self.writing_dir,
            self.simulation_dir,
            self.evaluation_dir,
            self.curation_dir,
            self.templates_dir,
            self.audit_logs_dir,
            self.markdown_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def save_previous_sop(self, section_title: str, sop_content: str):
        """保存上一次生成的SOP，用于下一次增强"""
        try:
            with _file_lock:
                previous_sops = self._load_previous_sops()
                previous_sops[section_title] = sop_content
                self._write_previous_sops(previous_sops)
        except Exception as e:
            print(f"   ✗ 保存Previous SOP失败: {e}")

    def load_previous_sop(self, section_title: str) -> str:
        """加载上一次生成的SOP"""
        try:
            previous_sops = self._load_previous_sops()
            return previous_sops.get(section_title, "")
        except Exception as e:
            print(f"   ✗ 加载Previous SOP失败: {e}")
            return ""

    def _load_previous_sops(self) -> dict:
        """加载所有previous_sops（内部方法）"""
        if self.previous_sops_file.exists():
            with open(self.previous_sops_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _write_previous_sops(self, previous_sops: dict):
        """写入所有previous_sops（内部方法）"""
        with open(self.previous_sops_file, "w", encoding="utf-8") as f:
            json.dump(previous_sops, f, ensure_ascii=False, indent=2)

    def get_checkpoint(self) -> int:
        """
        获取最后一次处理的数据集索引。

        Returns:
            最后处理的数据集索引（从1开始），如果没有checkpoint则返回0
        """
        checkpoint_file = MEMORY_DIR / "dataset_checkpoint.json"
        if checkpoint_file.exists():
            try:
                with _file_lock:
                    with open(checkpoint_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data.get("last_processed_index", 0)
            except Exception:
                return 0
        return 0

    def save_checkpoint(self, dataset_index: int):
        """
        保存当前处理的数据集索引。

        Args:
            dataset_index: 当前处理的数据集索引（从1开始）
        """
        checkpoint_file = MEMORY_DIR / "dataset_checkpoint.json"
        with _file_lock:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"last_processed_index": dataset_index}, f, ensure_ascii=False, indent=2
                )

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename to be safe for filesystem"""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

    # ============== Skill Library Management ==============

    def load_skill(self, skill_type: str, skill_name: str = None) -> str:
        """
        Load a skill file from the skill library.

        Args:
            skill_type: Type of skill (master, writer, simulator, reviewer, curator)
            skill_name: Name of skill file (optional, uses default for type)

        Returns:
            Skill content as string
        """
        if skill_type == "master":
            skill_file = self.skills_dir / "master" / "complexity_analysis_skill_v1.md"
        elif skill_type == "writer":
            skill_file = self.writing_dir / f"writer_skill_v{WRITER_SKILL_VERSION}.md"
        elif skill_type == "simulator":
            skill_file = (
                self.simulation_dir / f"simulator_skill_v{SIMULATOR_SKILL_VERSION}.md"
            )
        elif skill_type == "reviewer":
            skill_file = (
                self.evaluation_dir / f"reviewer_skill_v{REVIEWER_SKILL_VERSION}.md"
            )
        elif skill_type == "curator":
            skill_file = (
                self.curation_dir / f"curator_skill_v{CURATOR_SKILL_VERSION}.md"
            )
        else:
            raise ValueError(f"Unknown skill type: {skill_type}")

        if not skill_file.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_file}")

        with open(skill_file, "r", encoding="utf-8") as f:
            return f.read()

    def update_writer_skill(self, new_rule: Dict[str, str]) -> str:
        """
        Update Writer Skill with a new rule and save as new version.

        Args:
            new_rule: Dictionary with 'update_type', 'new_rule', 'rationale'

        Returns:
            New version number (e.g., "1.1")
        """
        with _file_lock:
            # Load current version
            current_file = self.writing_dir / f"writer_skill_v{WRITER_SKILL_VERSION}.md"
            with open(current_file, "r", encoding="utf-8") as f:
                content = f.read()
    
            # Parse version number
            version_match = re.search(r"v(\d+\.\d+)", current_file.name)
            if version_match:
                current_version = float(version_match.group(1))
                new_version = f"{current_version + 0.1:.1f}"
            else:
                new_version = "1.1"
    
            # Insert new rule based on update_type
            update_type = new_rule.get("update_type", "add_principle")
    
            if update_type == "add_principle":
                # Find and update "核心原则" section
                marker = "## 核心原则"
                if marker in content:
                    # Find existing principles count
                    principle_lines = []
                    in_section = False
                    for line in content.split("\n"):
                        if marker in line:
                            in_section = True
                        elif in_section and line.startswith("## "):
                            break
                        elif in_section and line.startswith(("## ", "### ")):
                            break
                        elif in_section:
                            principle_lines.append(line)
    
                    new_line = f"N. **{new_rule['new_rule']}**：{new_rule['rationale']}"
                    updated_content = content.replace(marker, marker + "\n" + new_line)
                else:
                    updated_content = (
                        content
                        + f"\n\n## 核心原则\nN. **{new_rule['new_rule']}**：{new_rule['rationale']}"
                    )
    
            elif update_type == "add_prohibition":
                # Find and update "禁止事项" section
                marker = "## 禁止事项"
                if marker in content:
                    new_line = f"❌ {new_rule['new_rule']}"
                    if marker + "\n" in content:
                        updated_content = content.replace(
                            marker + "\n", marker + "\n" + new_line + "\n"
                        )
                    else:
                        updated_content = content.replace(marker, marker + "\n" + new_line)
                else:
                    updated_content = content + f"\n\n## 禁止事项\n❌ {new_rule['new_rule']}"
            else:
                # Default to add_principle if update_type is unknown
                print(f"⚠️  Unknown update_type: {update_type}, defaulting to add_principle")
                new_line = f"N. **{new_rule.get('new_rule', '未知规则')}**：{new_rule.get('rationale', '未知理由')}"
                marker = "## 核心原则"
                if marker in content:
                    updated_content = content.replace(marker, marker + "\n" + new_line)
                else:
                    updated_content = content + "\n\n## 核心原则\n" + new_line
    
            # Save new version
            new_file = self.writing_dir / f"writer_skill_v{new_version}.md"
            with open(new_file, "w", encoding="utf-8") as f:
                f.write(updated_content)
    
            # Log to audit outside file operations but inside lock
            self.log_skill_update("writer", new_version, new_rule)
    
            return new_version

    def log_skill_update(
        self, skill_type: str, new_version: str, update_data: Dict[str, Any]
    ):
        """Log skill update to audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "skill_update",
            "skill_type": skill_type,
            "new_version": new_version,
            "update_data": update_data,
        }
        self._write_audit_log(log_entry)

    # ============== Template Library Management ==============

    def save_sop_template(
        self, section_title: str, sop_content: str, metadata: Dict[str, Any] = None
    ):
        """
        Save SOP template to unified JSON and separate MD files.

        Args:
            section_title: Title of section
            sop_content: Complete SOP content (Markdown)
            metadata: Additional metadata (score, iteration count, etc.)
        """
        safe_name = self._sanitize_filename(section_title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_file = self.markdown_dir / f"{safe_name}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(sop_content)

        all_sops_file = self.templates_dir / "all_sops.json"
        
        with _file_lock:
            all_sops = []
            if all_sops_file.exists():
                with open(all_sops_file, "r", encoding="utf-8") as f:
                    try:
                        all_sops = json.load(f)
                        if not isinstance(all_sops, list):
                            all_sops = []
                    except json.JSONDecodeError:
                        all_sops = []

        new_entry = {
            "section_title": section_title,
            "sop_content": sop_content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "verified": metadata.get("is_pass", False) if metadata else False,
        }

        with _file_lock:
            all_sops = [
                sop for sop in all_sops if sop.get("section_title") != section_title
            ]
            all_sops.append(new_entry)
            
            with open(all_sops_file, "w", encoding="utf-8") as f:
                json.dump(all_sops, f, ensure_ascii=False, indent=2)

        # Log to audit
        self.log_template_save(section_title, metadata)

    def load_sop_template(self, section_title: str) -> Optional[Dict[str, Any]]:
        """
        Load latest SOP template for a section.

        Args:
            section_title: Title of the section

        Returns:
            Template data dict or None if not found
        """
        safe_name = self._sanitize_filename(section_title)
        json_files = list(self.templates_dir.glob(f"{safe_name}_*.json"))

        if not json_files:
            return None

        # Get latest file
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def log_template_save(self, section_title: str, metadata: Dict[str, Any]):
        """Log template save to audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "template_save",
            "section_title": section_title,
            "metadata": metadata,
        }
        self._write_audit_log(log_entry)

    # ============== Audit Log Management ==============

    def log_execution_start(self, section_title: str, complexity: str, route: str):
        """Log execution start"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "execution_start",
            "section_title": section_title,
            "complexity": complexity,
            "route": route,
        }
        self._write_audit_log(log_entry)

    def log_node_execution(
        self, section_title: str, node_name: str, node_output: Dict[str, Any]
    ):
        """
        Log node execution with clean output.

        Args:
            section_title: Section being processed
            node_name: Name of the node (writer, simulator, reviewer, etc.)
            node_output: Output from the node
        """
        # Clean output based on config
        if CLEAN_OUTPUT:
            # Store only essential data
            clean_output = self._clean_node_output(node_name, node_output)
        else:
            clean_output = node_output

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "node_execution",
            "section_title": section_title,
            "node_name": node_name,
            "output": clean_output,
        }
        self._write_audit_log(log_entry)

    def _clean_node_output(
        self, node_name: str, output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Clean node output for storage (remove verbose text, keep structured data).

        Args:
            node_name: Name of the node
            output: Raw output from node

        Returns:
            Cleaned output
        """
        cleaned = {}

        # For Writer: keep SOP content only
        if node_name == "writer":
            cleaned["sop_content"] = output.get("sop_content", "")
            cleaned["iteration"] = output.get("iteration", 1)

        # For Simulator: keep structured JSON
        elif node_name == "simulator":
            if "result" in output and isinstance(output["result"], dict):
                cleaned = output["result"]
            else:
                cleaned = output

        # For Reviewer: keep score and pass status
        elif node_name == "reviewer":
            if "result" in output and isinstance(output["result"], dict):
                cleaned["score"] = output["result"].get("score")
                cleaned["is_pass"] = output["result"].get("is_pass")
                cleaned["critical_issues"] = output["result"].get("critical_issues", [])
            else:
                cleaned = output

        # For Curator: keep update type and new rule
        elif node_name == "curator":
            if "result" in output and isinstance(output["result"], dict):
                cleaned["update_type"] = output["result"].get("update_type")
                cleaned["new_rule"] = output["result"].get("new_rule")
                cleaned["rationale"] = output["result"].get("rationale")
            else:
                cleaned = output

        else:
            cleaned = output

        return cleaned

    def log_execution_complete(
        self, section_title: str, final_score: float, total_iterations: int
    ):
        """Log execution completion"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "execution_complete",
            "section_title": section_title,
            "final_score": final_score,
            "total_iterations": total_iterations,
            "success": final_score >= 4,
        }
        self._write_audit_log(log_entry)

    def _write_audit_log(self, log_entry: Dict[str, Any]):
        """Write audit log entry to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = self.audit_logs_dir / f"audit_{timestamp}.jsonl"

        with _file_lock:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def get_audit_logs(self, section_title: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs.

        Args:
            section_title: Filter by section title (optional)

        Returns:
            List of audit log entries
        """
        all_logs = []
        for log_file in self.audit_logs_dir.glob("audit_*.jsonl"):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if (
                        section_title is None
                        or entry.get("section_title") == section_title
                    ):
                        all_logs.append(entry)

        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get("timestamp", ""))

        return all_logs

    # ============== Complexity Analysis Helpers ==============

    def analyze_complexity_by_rules(self, section_title: str) -> str:
        """
        Analyze complexity based on predefined rules (no LLM call).

        Args:
            section_title: Title of the section

        Returns:
            Complexity level: "simple", "standard", or "complex"
        """
        from config_v6 import SIMPLE_SECTIONS, COMPLEX_SECTIONS

        # Simple sections (direct match)
        for simple in SIMPLE_SECTIONS:
            if simple in section_title:
                return "simple"

        # Complex sections (direct match)
        for complex_section in COMPLEX_SECTIONS:
            if complex_section in section_title:
                return "complex"

        # Default: standard
        return "standard"

    def analyze_complexity_by_content(self, content: str) -> str:
        """
        Analyze complexity based on content length and keywords.

        Args:
            content: Content to analyze

        Returns:
            Complexity level: "simple", "standard", or "complex"
        """
        from config_v6 import COMPLEX_KEYWORDS, SIMPLE_WORD_COUNT, COMPLEX_WORD_COUNT

        word_count = len(content.split())

        # Simple: very short content
        if word_count < SIMPLE_WORD_COUNT:
            return "simple"

        # Complex: long content or contains complex keywords
        if word_count > COMPLEX_WORD_COUNT or any(
            keyword in content for keyword in COMPLEX_KEYWORDS
        ):
            return "complex"

        # Standard: everything else
        return "standard"
