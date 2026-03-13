"""
DeepAgent Base Class - Unified LLM Framework

Simple, clean, universal base class for all agents.
"""

import time
from typing import Dict, Any
import os


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
        provider = self.config.get("api_provider", "openai")

        if provider == "openai":
            from openai import OpenAI

            return OpenAI(
                api_key=self._get_api_key(), base_url=self.config.get("api_base", None)
            )
        elif provider == "anthropic":
            from anthropic import Anthropic

            return Anthropic(api_key=self._get_api_key())
        else:
            raise ValueError(f"Unsupported api_provider: {provider}")

    def _get_api_key(self) -> str:
        """Get API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Try Anthropic key as fallback
            api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY environment variable is set"
            )
        return api_key

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
                    model=self.config["model"],
                    messages=messages,
                    temperature=self.config.get("temperature", 0.7),
                    max_tokens=self.config.get("max_tokens", 2048),
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2**attempt
                    print(
                        f"⚠️  Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"LLM call failed after {max_retries} attempts. Last error: {last_error}"
                    )
