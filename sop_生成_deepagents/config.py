"""
SOP 生成 2.0 - 基于 DeepAgents 框架
配置文件
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://aihubmix.com/v1")

# V5 多模型配置
WRITER_MODEL = "gpt-4o-mini"  # 生成：便宜快速
SIMULATOR_MODEL = "gpt-4o-mini"  # 盲测：快速
REVIEWER_MODEL = "grok-4-1-fast-reasoning"  # 评估：毒舌模型
CURATOR_MODEL = "claude-opus"  # 沉淀：深度推理

# 兼容旧版
SMART_MODEL = os.getenv("SMART_MODEL", "gemini-3.1-flash-lite-preview")
FAST_MODEL = os.getenv("FAST_MODEL", "grok-4-1-fast-reasoning")

# 系统配置
EXPERIMENT_TYPE = "小分子模板"
MEMORY_DIR = "./memory"
MAX_ITERATIONS = 5

# Subagent 配置
SUBAGENTS_CONFIG = {
    "writer": {
        "name": "writer",
        "description": "根据验证方案和 GLP 报告生成详细 SOP",
        "model": SMART_MODEL
    },
    "simulator": {
        "name": "simulator",
        "description": "盲测 SOP 的可执行性",
        "model": FAST_MODEL
    },
    "reviewer": {
        "name": "reviewer",
        "description": "审核 SOP 质量并提供反馈",
        "model": FAST_MODEL
    },
    "reflector": {
        "name": "reflector",
        "description": "诊断问题根源并提出改进策略",
        "model": SMART_MODEL
    },
    "curator": {
        "name": "curator",
        "description": "根据诊断结果更新规则库",
        "model": FAST_MODEL
    }
}
