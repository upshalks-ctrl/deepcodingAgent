"""
Prompt loader utility for loading agent prompts from markdown files
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """Loads and caches prompts from markdown files"""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize prompt loader

        Args:
            prompts_dir: Directory containing prompt markdown files.
                        Defaults to src/prompts
        """
        if prompts_dir is None:
            # Default to src/prompts relative to this file
            current_dir = Path(__file__).parent
            prompts_dir = current_dir.parent / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}

        # Ensure prompts directory exists
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory does not exist: {self.prompts_dir}")
            self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def load_prompt(self, agent_name: str) -> str:
        """Load prompt for a specific agent

        Args:
            agent_name: Name of the agent (e.g., 'coordinator', 'planner')

        Returns:
            Prompt content as string (with full formatting)
        """
        # Check cache first
        if agent_name in self._cache:
            return self._cache[agent_name]

        # Construct file path
        prompt_file = self.prompts_dir / f"{agent_name}.md"

        # Load file content
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Keep the full content including title and formatting
                # Only trim leading/trailing whitespace
                content = content.strip()

                # Cache the result
                self._cache[agent_name] = content

                return content

            except Exception as e:
                logger.error(f"Error loading prompt for {agent_name}: {e}")
                return f"# Error loading prompt for {agent_name}\n\nPlease check the prompt file at {prompt_file}"
        else:
            logger.warning(f"Prompt file not found: {prompt_file}")
            return f"# Prompt for {agent_name}\n\nPlease create a prompt file at {prompt_file}"

    def reload_prompt(self, agent_name: str) -> str:
        """Force reload a prompt from file

        Args:
            agent_name: Name of the agent

        Returns:
            Freshly loaded prompt content (with full formatting)
        """
        # Remove from cache if present
        if agent_name in self._cache:
            del self._cache[agent_name]

        # Load fresh
        return self.load_prompt(agent_name)

    def list_available_prompts(self) -> list[str]:
        """List all available prompt files

        Returns:
            List of agent names with available prompts
        """
        if not self.prompts_dir.exists():
            return []

        prompts = []
        for file_path in self.prompts_dir.glob("*.md"):
            prompts.append(file_path.stem)

        return sorted(prompts)

    def clear_cache(self):
        """Clear all cached prompts"""
        self._cache.clear()


# Global instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance

    Returns:
        PromptLoader instance
    """
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_agent_prompt(agent_name: str) -> str:
    """Load prompt for an agent using the global loader

    Args:
        agent_name: Name of the agent

    Returns:
        Prompt content as string (with full formatting)
    """
    return get_prompt_loader().load_prompt(agent_name)


def load_agent_prompt_with_formatting(agent_name: str) -> str:
    """Load prompt for an agent with markdown formatting preserved

    Args:
        agent_name: Name of the agent

    Returns:
        Prompt content as string with markdown formatting
    """
    return get_prompt_loader().load_prompt(agent_name)


def format_prompt_for_agent(agent_name: str, prompt: str) -> str:
    """Format prompt specifically for an agent type

    Args:
        agent_name: Name of the agent
        prompt: Raw prompt content

    Returns:
        Formatted prompt string
    """
    # Add agent-specific formatting if needed
    if agent_name == "coordinator":
        return f"""
# {agent_name.title()} Agent

{prompt}

---
*Loaded from src/prompts/{agent_name}.md*
"""
    elif agent_name == "planner":
        return f"""
# {agent_name.title()} Agent

{prompt}

---
*Loaded from src/prompts/{agent_name}.md*
"""
    elif agent_name == "coder":
        return f"""
# {agent_name.title()} Agent

{prompt}

---
*Loaded from src/prompts/{agent_name}.md*
"""
    elif agent_name == "executor":
        return f"""
# {agent_name.title()} Agent

{prompt}

---
*Loaded from src/prompts/{agent_name}.md*
"""
    elif agent_name == "reflector":
        return f"""
# {agent_name.title()} Agent

{prompt}

---
*Loaded from src/prompts/{agent_name}.md*
"""
    else:
        # Default formatting
        return f"""
# {agent_name.title()} Agent

{prompt}

---
*Loaded from src/prompts/{agent_name}.md*
"""