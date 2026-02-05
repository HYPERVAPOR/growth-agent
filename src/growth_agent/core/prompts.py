"""
Prompt template loader from files.

This module loads prompt templates from text files for easy management.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Load prompt templates from files.

    Supports variable substitution using {variable} syntax.
    """

    def __init__(self, prompts_dir: Path):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt template files
        """
        self.prompts_dir = Path(prompts_dir)

    def load(self, prompt_name: str, **kwargs: Any) -> str:
        """
        Load a prompt template and substitute variables.

        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            **kwargs: Variables to substitute in the template

        Returns:
            Prompt template with variables substituted

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        # Read template
        template = prompt_path.read_text(encoding="utf-8")

        # Substitute variables
        try:
            prompt = template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable in prompt template: {e}")
            raise

        return prompt

    def get_system_prompt(self, task: str, **kwargs: Any) -> str:
        """
        Load system prompt for a specific task.

        Args:
            task: Task name (e.g., "content_evaluation", "blog_generation")
            **kwargs: Variables to substitute

        Returns:
            System prompt string
        """
        return self.load(f"{task}_system", **kwargs)

    def get_user_prompt(self, task: str, **kwargs: Any) -> str:
        """
        Load user prompt for a specific task.

        Args:
            task: Task name (e.g., "content_evaluation", "blog_generation")
            **kwargs: Variables to substitute

        Returns:
            User prompt string
        """
        return self.load(f"{task}_user", **kwargs)

    def list_prompts(self) -> list[str]:
        """
        List all available prompt templates.

        Returns:
            List of prompt names (without .txt extension)
        """
        if not self.prompts_dir.exists():
            return []

        prompts = []
        for file_path in self.prompts_dir.glob("*.txt"):
            prompts.append(file_path.stem)

        return sorted(prompts)
