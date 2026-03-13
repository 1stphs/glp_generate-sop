"""
DeepAgent Base Class - Unified LLM Framework

Simple, clean, universal base class for all agents.
"""

import time
from typing import Dict, Any, Optional

from .config import Config


def DeepAgent(system_prompt: str, **config):
    """
    Factory function to create DeepAgent instances.

    This provides a simple interface to create agents with system prompts.

    Args:
        system_prompt: System prompt defining agent's role
        **config: LLM configuration (api_provider, model, temperature, max_tokens)

    Returns:
        DeepAgent instance

    Usage:
        >>> writer = DeepAgent(system_prompt="writer_prompt", api_provider="openai", model="gpt-4o")
        >>> result = writer.run("your task")
    """
    return _DeepAgentImpl(system_prompt=system_prompt, config=config)


class _DeepAgentImpl:
    """
    Implementation of DeepAgent base class.

    Responsibilities:
    - LLM client initialization
    - Unified run() interface
    - Built-in retry logic with exponential backoff
    - Error handling
    """

    def __init__(self, system_prompt: str, config: Dict[str, Any]):
        self.system_prompt = system_prompt
        self.config = config
        self.client = self._init_llm_client()

    def _init_llm_client(self):
        """Initialize LLM client based on api_provider."""
        provider = self.config.get("api_provider", Config.get_llm_provider())

        if provider == "openai":
            from openai import OpenAI
            import httpx

            api_key = self.config.get("api_key") or Config.get_llm_api_key()
            api_base = self.config.get("api_base") or Config.get_llm_api_base()

            return OpenAI(
                api_key=api_key,
                base_url=api_base,
                http_client=httpx.Client(timeout=Config.get_llm_timeout()),
            )
        elif provider == "anthropic":
            from anthropic import Anthropic

            api_key = self.config.get("api_key") or Config.get_llm_api_key()
            api_base = self.config.get("api_base") or Config.get_llm_api_base()

            return Anthropic(api_key=api_key, base_url=api_base)
        else:
            raise ValueError(f"Unsupported api_provider: {provider}")

    def run(self, query: str) -> str:
        """
        Execute agent's primary action.

        Args:
            query: User's query or task description

        Returns:
            LLM's response text
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]

        response = self._llm_call_with_retry(messages)
        return response

    def _llm_call_with_retry(self, messages: list, max_retries: int = 3) -> str:
        """Execute LLM call with exponential backoff retry logic."""
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.get("model", Config.get_llm_model()),
                    messages=messages,
                    temperature=self.config.get(
                        "temperature", Config.get_llm_temperature()
                    ),
                    max_tokens=self.config.get(
                        "max_tokens", Config.get_llm_max_tokens()
                    ),
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("LLM returned empty response")
                return content
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"⚠️  Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"LLM call failed after {max_retries} attempts. Last error: {last_error}"
                    )
