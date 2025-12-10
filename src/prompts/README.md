# Agent Prompts

This directory contains prompt definitions for all agents in the deepcodeagent system.

## Prompt Files

Each agent has its own markdown file with the same name as the agent:

- `coordinator.md` - Global workflow coordinator
- `planner.md` - Research planning agent
- `research_coordinator.md` - Research task coordinator
- `searcher.md` - Web search specialist
- `analyzer.md` - Technical analysis specialist
- `researcher.md` - Deep research specialist
- `architecture_writer.md` - Architecture documentation specialist
- `code_coordinator.md` - Coding task coordinator
- `coder.md` - Code implementation specialist
- `executor.md` - Test execution and quality assurance
- `reflector.md` - Code review and reflection specialist
- `reporter.md` - Technical reporting specialist

## Prompt Structure

Each prompt file follows this structure:

1. **Title and Role Definition**
2. **Core Responsibilities**
3. **Available Tools**
4. **Interaction Guidelines**
5. **Output Requirements**

## Loading Prompts

Prompts are loaded using the `load_agent_prompt()` function from `src.utils.prompt_loader`:

```python
from src.utils.prompt_loader import load_agent_prompt

# Load prompt for an agent
prompt = load_agent_prompt("coordinator")
```

## Modifying Prompts

To modify an agent's behavior:
1. Edit the corresponding `.md` file
2. Reload the prompt using `load_agent_prompt()` with the reload option
3. The agent will use the updated prompt on next execution

## Best Practices

1. Keep prompts clear and concise
2. Focus on the agent's specific role
3. Include examples of expected behavior
4. Define clear tool usage patterns
5. Specify output formats when applicable