"""
Configuration Manager for DeepAgent SOP

Centralized configuration management with environment variable support.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


# Load .env file from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Try to load .env file (optional - won't fail if missing)
load_dotenv(ENV_PATH)


class Config:
    """
    Configuration class for DeepAgent SOP.

    All configuration values are loaded from environment variables with sensible defaults.
    """

    # ====================
    # LLM Configuration
    # ====================

    @staticmethod
    def get_llm_provider() -> str:
        """Get LLM API provider (openai | anthropic)."""
        return os.getenv("DEEPAGENT_LLM_PROVIDER", "openai")

    @staticmethod
    def get_llm_model() -> str:
        """Get LLM model name."""
        provider = Config.get_llm_provider()
        if provider == "openai":
            return os.getenv("OPENVIKING_LLM_MODEL", "gpt-4o")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        return "gpt-4o"

    @staticmethod
    def get_llm_api_key() -> str:
        """Get LLM API key."""
        provider = Config.get_llm_provider()
        if provider == "openai":
            api_key = os.getenv("OPENVIKING_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
        else:
            api_key = None

        if not api_key:
            raise RuntimeError(
                f"API key not found for provider '{provider}'. "
                f"Please set {provider.upper()}_API_KEY environment variable."
            )
        return api_key

    @staticmethod
    def get_llm_api_base() -> Optional[str]:
        """Get LLM API base URL (optional)."""
        provider = Config.get_llm_provider()
        if provider == "openai":
            return os.getenv("OPENVIKING_LLM_API_BASE") or os.getenv("OPENAI_API_BASE")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_BASE")
        return None

    @staticmethod
    def get_llm_temperature() -> float:
        """Get default LLM temperature."""
        return float(os.getenv("DEEPAGENT_LLM_TEMPERATURE", "0.7"))

    @staticmethod
    def get_llm_max_tokens() -> int:
        """Get default max tokens for LLM."""
        return int(os.getenv("DEEPAGENT_LLM_MAX_TOKENS", "4096"))

    @staticmethod
    def get_llm_timeout() -> float:
        """Get LLM request timeout in seconds."""
        return float(os.getenv("DEEPAGENT_LLM_TIMEOUT", "60.0"))

    # ====================
    # Memory Configuration
    # ====================

    @staticmethod
    def get_memory_path() -> str:
        """Get path to memory.md file."""
        return os.getenv("DEEPAGENT_MEMORY_PATH", "deepagent_sop/memory/memory.md")

    # ====================
    # Learning Configuration
    # ====================

    @staticmethod
    def is_learning_enabled() -> bool:
        """Check if learning loop is enabled by default."""
        return os.getenv("DEEPAGENT_LEARNING_ENABLED", "true").lower() == "true"

    # ====================
    # Trajectory Configuration
    # ====================

    @staticmethod
    def get_trajectory_path() -> Optional[str]:
        """Get path to save trajectory (optional)."""
        return os.getenv("DEEPAGENT_TRAJECTORY_PATH")

    @staticmethod
    def should_log_trajectory() -> bool:
        """Check if trajectory logging is enabled."""
        return os.getenv("DEEPAGENT_LOG_TRAJECTORY", "true").lower() == "true"

    # ====================
    # Retry Configuration
    # ====================

    @staticmethod
    def get_max_retries() -> int:
        """Get max retry attempts for LLM calls."""
        return int(os.getenv("DEEPAGENT_MAX_RETRIES", "3"))

    @staticmethod
    def get_retry_backoff_base() -> float:
        """Get base backoff time for retries in seconds."""
        return float(os.getenv("DEEPAGENT_RETRY_BACKOFF", "2.0"))

    # ====================
    # Debug Configuration
    # ====================

    @staticmethod
    def is_debug_mode() -> bool:
        """Check if debug mode is enabled."""
        return os.getenv("DEEPAGENT_DEBUG", "false").lower() == "true"

    @staticmethod
    def get_log_level() -> str:
        """Get logging level."""
        return os.getenv("DEEPAGENT_LOG_LEVEL", "INFO")

    # ====================
    # Utility Methods
    # ====================

    @staticmethod
    def print_config():
        """Print current configuration (for debugging)."""
        print("=" * 60)
        print("DeepAgent SOP Configuration")
        print("=" * 60)
        print(f"LLM Provider: {Config.get_llm_provider()}")
        print(f"LLM Model: {Config.get_llm_model()}")
        print(f"LLM API Base: {Config.get_llm_api_base() or 'default'}")
        print(f"LLM Temperature: {Config.get_llm_temperature()}")
        print(f"LLM Max Tokens: {Config.get_llm_max_tokens()}")
        print(f"Memory Path: {Config.get_memory_path()}")
        print(f"Learning Enabled: {Config.is_learning_enabled()}")
        print(f"Max Retries: {Config.get_max_retries()}")
        print(f"Debug Mode: {Config.is_debug_mode()}")
        print("=" * 60)
