"""
SOP Generation System V6 - Configuration
基于LangGraph的多模型SOP自动生成系统
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not found, skipping load_dotenv()")

# ============== Base Configuration ==============
BASE_DIR = Path(__file__).parent.parent.resolve()
MEMORY_DIR = BASE_DIR / "memory"
SKILLS_DIR = BASE_DIR / "skills"
TEMPLATES_DIR = MEMORY_DIR / "sop_templates"
AUDIT_LOGS_DIR = MEMORY_DIR / "audit_logs"
CHAPTER_RULES_DIR = MEMORY_DIR / "chapter_rules"

# Ensure directories exist
for d in [MEMORY_DIR, SKILLS_DIR, TEMPLATES_DIR, AUDIT_LOGS_DIR, CHAPTER_RULES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============== API Configuration ==============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ============== Model Configuration ==============
MASTER_MODEL = "grok-4-fast-non-reasoning"
SIMULATOR_MODEL = "grok-4-fast-non-reasoning"
REVIEWER_MODEL = "grok-4-fast-non-reasoning"
CURATOR_MODEL = "grok-4-fast-non-reasoning"
WRITER_MODEL = "grok-4-fast-non-reasoning"

# ============== Section Classification ==============
STATIC_SECTIONS = [
    "签字页",
    "GLP遵从性声明",
    "质量保证声明",
    "目录",
    "附表目录",
    "附图目录",
    "缩略语表",
    "参考文献",
    "附录",
]

SIMPLE_SECTIONS = [
    "验证目的",
    "前言",
    "摘要",
    "验证试验名称",
    "验证试验编号",
    "结论",
    "版本历史",
    "修订记录",
    "主要操作人员",
    "验证负责人",
]

COMPLEX_SECTIONS = [
    "稳定性",
    "精密度",
    "准确度",
    "方法学验证",
    "定量下限",
    "标准曲线",
    "特异性",
    "稀释可靠性",
    "提取回收率",
    "基质效应",
    "系统适用性",
    "残留",
    "干扰",
]

COMPLEX_KEYWORDS = [
    "计算",
    "统计",
    "验证",
    "分析",
    "数据",
    "稳定",
    "方法",
    "回收",
    "精密度",
    "准确度",
]

# ============== System Configuration ==============
EXPERIMENT_TYPE = "BV实验"
MAX_ITERATIONS = 3
MAX_DATASETS = 1
CLEAN_OUTPUT = True

# ============== Skill Versioning ==============
MASTER_SKILL_VERSION = "1"
WRITER_SKILL_VERSION = "1"
SIMULATOR_SKILL_VERSION = "1"
REVIEWER_SKILL_VERSION = "1"
ANALYZER_SKILL_VERSION = "1"
CURATOR_SKILL_VERSION = "1"


# ============== Validation ==============
def validate_config() -> bool:
    """Validate required configuration"""
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY not set")
        return False
    return True


# ============== Model Mapping ==============
MODEL_CONFIG = {
    "master": {
        "model": MASTER_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
    },
    "writer": {
        "model": WRITER_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
    },
    "simulator": {
        "model": SIMULATOR_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
    },
    "reviewer": {
        "model": REVIEWER_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
    },
    "curator": {
        "model": CURATOR_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
    },
}
