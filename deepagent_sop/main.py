"""
Main Entry Point for DeepAgent SOP System

This is the main entry point that matches the pseudocode requirements:

```python
from deepagent_sop import MainAgent

# 1. Initialize Main Agent with LLM config
llm_config = {
    "api_provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096
}
main_agent = MainAgent(llm_config=llm_config)

# 2. Execute task
result = main_agent.run(
    user_query="sop generation task description",
    enable_learning=True
)

# 3. Access results
print("Task Understanding:", result["task_understanding"])
print("Plan:", result["plan"])
print("Final Result:", result["final_result"])
print("Summary:", result["summary"])
```

Usage:
    python deepagent_sop/main.py --task "your task description"
    python deepagent_sop/main.py --task "sop generation task" --no-learning

See deepagent_sop/README.md for details.
"""

import sys
import argparse
from typing import Dict, Any

from core.config import Config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DeepAgent SOP - Autonomous Multi-Agent System"
    )
    parser.add_argument(
        "--task", type=str, required=True, help="Task description to execute"
    )
    parser.add_argument(
        "--no-learning", action="store_true", help="Disable learning loop"
    )
    parser.add_argument(
        "--api-provider",
        type=str,
        default=None,
        choices=["openai", "anthropic"],
        help=f"LLM API provider (default: {Config.get_llm_provider()})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Model name (default: {Config.get_llm_model()})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help=f"Generation temperature (default: {Config.get_llm_temperature()})",
    )
    parser.add_argument(
        "--memory-path",
        type=str,
        default=None,
        help=f"Path to memory.md file (default: {Config.get_memory_path()})",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Print current configuration and exit",
    )

    args = parser.parse_args()

    # Print config if requested
    if args.config:
        Config.print_config()
        sys.exit(0)

    # Check API key
    try:
        api_key = Config.get_llm_api_key()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Import after environment check
    from core.main_agent import MainAgent

    llm_config: Dict[str, Any] = {
        "api_provider": args.api_provider or Config.get_llm_provider(),
        "model": args.model or Config.get_llm_model(),
        "temperature": args.temperature or Config.get_llm_temperature(),
        "max_tokens": Config.get_llm_max_tokens(),
    }

    # Initialize Main Agent
    print(f"DeepAgent SOP v1.0.0")
    print(f"API Provider: {args.api_provider}")
    print(f"Model: {args.model}")
    print(f"Task: {args.task}")
    print(f"Learning: {'disabled' if args.no_learning else 'enabled'}")
    print("-" * 60)

    try:
        main_agent = MainAgent(llm_config=llm_config, memory_path=args.memory_path)

        # Execute task
        print("\nExecuting task...\n")
        result = main_agent.run(
            user_query=args.task, enable_learning=not args.no_learning
        )

        # Print results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"\nTask Understanding:\n{result['task_understanding']}\n")
        print(f"\nPlan:\n{result['plan']}\n")
        print(f"\nFinal Result:\n{result['final_result']}\n")
        print(f"\nSummary:\n{result['summary']}\n")
        print(f"\nTrajectory Steps: {len(result['trajectory'])}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
