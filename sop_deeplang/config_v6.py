"""
SOP Generation System V6 - Configuration
基于LangGraph的多模型SOP自动生成系统
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============== Base Configuration ==============
BASE_DIR = Path(__file__).parent.resolve()
MEMORY_DIR = BASE_DIR / "memory"
SKILLS_DIR = MEMORY_DIR / "skills"
TEMPLATES_DIR = MEMORY_DIR / "sop_templates"
AUDIT_LOGS_DIR = MEMORY_DIR / "audit_logs"

# Ensure directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============== API Configuration ==============
# OpenAI-compatible API (for Grok)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Google Gemini API
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============== Model Configuration (V6 - Grok + Gemini) ==============
# Master/Simulator/Reviewer/Curator: Grok 4.1 Fast Reasoning
MASTER_MODEL = "grok-4-1-fast-non-reasoning"
SIMULATOR_MODEL = "grok-4-1-fast-non-reasoning"
REVIEWER_MODEL = "grok-4-1-fast-non-reasoning"
CURATOR_MODEL = "grok-4-1-fast-non-reasoning"

# Writer: Gemini 3.1 Flash Lite (fast and cost-effective)
# WRITER_MODEL = "gemini-3.1-flash-lite"
WRITER_MODEL = "grok-4-1-fast-non-reasoning"

# ============== System Configuration ==============
EXPERIMENT_TYPE = "LC-MS_MS结构化验证"
MAX_ITERATIONS = 3  # Maximum iteration attempts for complex sections

# Complexity thresholds
SIMPLE_WORD_COUNT = 200  # If content < 200 words -> simple
COMPLEX_WORD_COUNT = 1000  # If content > 1000 words -> complex
COMPLEX_KEYWORDS = ["计算", "统计", "验证", "分析", "数据", "稳定", "方法", "质量"]

# ============== Complexity Rules ==============
SIMPLE_SECTIONS = [
    "缩略词表",
    "缩写",
    "参考文献",
    "版本历史",
    "修订记录",
    "目录",
    "附录",
    "致谢",
    "术语",
    "符号说明",
    "单位说明",
]

COMPLEX_SECTIONS = [
    "方法学验证",
    "稳定性研究",
    "统计分析",
    "数据分析",
    "结果与讨论",
    "质量控制",
    "系统适用性",
    "样品制备",
    "色谱条件",
    "质谱条件",
    "定量分析",
    "定性与定量",
]

# ============== Skill Versioning ==============
# MASTER_SKILL_VERSION = "1.0"
# WRITER_SKILL_VERSION = "1.0"
# SIMULATOR_SKILL_VERSION = "1.0"
# REVIEWER_SKILL_VERSION = "1.0"
# ANALYZER_SKILL_VERSION = "1.0"
# CURATOR_SKILL_VERSION = "1.0"

MASTER_SKILL_VERSION = "1"
WRITER_SKILL_VERSION = "1"
SIMULATOR_SKILL_VERSION = "1"
REVIEWER_SKILL_VERSION = "1"
ANALYZER_SKILL_VERSION = "1"
CURATOR_SKILL_VERSION = "1"

# ============== Node Configuration ==============
# Output control: clean JSON/Markdown only
CLEAN_OUTPUT = True
INCLUDE_THINKING = False

# ============== Logging Configuration ==============
LOG_LEVEL = "INFO"
ENABLE_AUDIT_LOG = True
ENABLE_SKILL_VERSIONING = True


# ============== Validation ==============
def validate_config() -> bool:
    """Validate required configuration"""
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY not set")
        return False
    # if not GEMINI_API_KEY:
    #     print("WARNING: GEMINI_API_KEY not set")
    #     return False
    return True


# ============== Model Mapping ==============
MODEL_CONFIG = {
    "master": {
        "model": MASTER_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "temperature": 0.3,
    },
    "writer": {
        "model": WRITER_MODEL,
        # "api_key": GEMINI_API_KEY,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "temperature": 0.5,
    },
    "simulator": {
        "model": SIMULATOR_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "temperature": 0.7,
    },
    "reviewer": {
        "model": REVIEWER_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "temperature": 0.1,
    },
    "curator": {
        "model": CURATOR_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "temperature": 0.3,
    },
}
