"""
记忆管理器 V5 - SQLite + 事务锁
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


class MemoryManagerV5:
    """SQLite数据库管理系统 + 物理文件备份"""

    def __init__(self, db_path: str = "./memory/sop_memory.db"):
        self.db_path = Path(db_path)
        self.base_dir = self.db_path.parent
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 物理物理目录
        self.audit_dir = self.base_dir / "audit_logs"
        self.rules_dir = self.base_dir / "rules"
        self.sop_templates_dir = self.base_dir / "sop_templates"
        
        for d in [self.audit_dir, self.rules_dir, self.sop_templates_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    section_title TEXT NOT NULL,
                    experiment_type TEXT,
                    version TEXT,
                    sop_id TEXT,
                    quality_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_title TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    rationale TEXT,
                    priority TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(section_title, rule_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sop_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_title TEXT NOT NULL UNIQUE,
                    template TEXT NOT NULL,
                    core_principles TEXT,
                    examples TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @contextmanager
    def _get_conn(self):
        """获取数据库连接（带事务锁）"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _sanitize(self, name: str) -> str:
        """清理文件名"""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

    def log_audit(self, data: Dict[str, Any]) -> int:
        """记录审计日志（SQL + JSONL文件）"""
        timestamp = datetime.now().isoformat()
        section_title = data.get("section_title", "unknown")
        section_safe = self._sanitize(section_title)
        
        # 存入数据库
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO audit_logs (timestamp, section_title, experiment_type, version, sop_id, quality_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                section_title,
                data.get("experiment_type", ""),
                data.get("version", ""),
                data.get("sop_id", ""),
                json.dumps(data.get("quality_assessment", {}), ensure_ascii=False)
            ))
            conn.commit()
            last_id = cursor.lastrowid

        # 写入 JSONL 文件备份
        audit_file = self.audit_dir / f"{section_safe}_audit.jsonl"
        log_entry = {
            "timestamp": timestamp,
            "section_title": section_title,
            "quality_assessment": data.get("quality_assessment", {})
        }
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
        return last_id

    def load_rules(self, section_title: str) -> List[Dict[str, Any]]:
        """加载章节规则"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT rule_id, content, rationale, priority
                FROM rules
                WHERE section_title = ?
                ORDER BY id
            """, (section_title,)).fetchall()
            return [dict(row) for row in rows]

    def save_rules_bundle(self, section_title: str, rules_list: List[Dict[str, Any]]):
        """保存章节所有规则（SQL + JSON文件）"""
        section_safe = self._sanitize(section_title)
        
        with self._get_conn() as conn:
            for rule in rules_list:
                conn.execute("""
                    INSERT OR REPLACE INTO rules (section_title, rule_id, content, rationale, priority)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    section_title,
                    rule.get("rule_id", ""),
                    rule.get("content", ""),
                    rule.get("rationale", ""),
                    rule.get("priority", "medium")
                ))
            conn.commit()

        # 导出到物理文件
        rules_file = self.rules_dir / f"{section_safe}_rules.json"
        export_data = {
            "section_title": section_title,
            "updated_at": datetime.now().isoformat(),
            "rules": rules_list
        }
        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def load_sop_template(self, section_title: str) -> Dict[str, Any]:
        """加载SOP模板"""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT template, core_principles, examples
                FROM sop_templates
                WHERE section_title = ?
            """, (section_title,)).fetchone()
            
            if row:
                return {
                    "template": row["template"],
                    "core_principles": json.loads(row["core_principles"] or "[]"),
                    "examples": json.loads(row["examples"] or "[]")
                }
            return {"template": "", "core_principles": [], "examples": []}

    def save_sop_template(self, section_title: str, data: Dict[str, Any]):
        """保存SOP模板（SQL + Markdown文件）"""
        section_safe = self._sanitize(section_title)
        timestamp = datetime.now().isoformat()
        
        # 存入数据库
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sop_templates (section_title, template, core_principles, examples, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                section_title,
                data.get("template", ""),
                json.dumps(data.get("core_principles", []), ensure_ascii=False),
                json.dumps(data.get("examples", []), ensure_ascii=False),
                timestamp
            ))
            conn.commit()

        # 存入物理文件 (Markdown) - 只有模板内容
        template_file = self.sop_templates_dir / f"{section_safe}_template.md"
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(data.get("template", ""))
