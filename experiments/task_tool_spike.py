"""
Task Tool Integration Spike (TASK-003A)

This spike validates that the Task tool can be used to spawn subagents for
the wfc-prompt-fixer Analyzer/Fixer/Reporter pipeline.

CRITICAL DISCOVERY: The Task tool is NOT a Python API, it's a Claude Code
feature that can only be invoked by Claude itself during conversation.

This means:
1. We CANNOT import and call Task() from Python code
2. We CAN ask Claude to use the Task tool during orchestration
3. Orchestrators must be invoked via Claude Code, not standalone Python

This changes the architecture significantly.
"""

import json
import re
from typing import Any, Dict


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON from agent response, handling markdown code blocks.

    Args:
        response: Raw response string from agent (may contain markdown)

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If JSON cannot be parsed
    """
    json_block_pattern = r"```json\s*\n(.*?)\n\s*```"
    match = re.search(json_block_pattern, response, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
    else:
        json_str = response.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from response: {e}") from e


def spawn_simple_analyzer(prompt: str) -> Dict[str, Any]:
    """
    MOCK: Simulates spawning a simple analyzer agent.

    In production, this would use the Task tool via Claude Code.
    For the spike, we return mock data to validate the interface.

    Args:
        prompt: The prompt to send to the analyzer

    Returns:
        Dictionary with 'response' key
    """
    return {
        "response": "This is a mock response. The Task tool must be invoked by Claude Code, not Python."
    }


def spawn_structured_analyzer(prompt: str) -> Dict[str, Any]:
    """
    MOCK: Simulates spawning an analyzer that returns structured JSON.

    In production, this would use the Task tool via Claude Code.

    Args:
        prompt: The prompt requesting structured output

    Returns:
        Dictionary with expected schema (grade, score, issues)
    """
    mock_response = """
    ```json
    {
        "grade": "B",
        "score": 85.5,
        "issues": ["Minor formatting issue"]
    }
    ```
    """
    return parse_json_response(mock_response)


def spawn_agent_with_timeout(prompt: str, timeout: int) -> Dict[str, Any]:
    """
    MOCK: Simulates spawning an agent with timeout.

    In production, this would use the Task tool's timeout parameter.

    Args:
        prompt: The prompt to send
        timeout: Timeout in seconds

    Returns:
        Dictionary with response

    Raises:
        TimeoutError: If timeout is very short (< 5 seconds in mock)
    """
    if timeout < 5:
        raise TimeoutError(f"Task timed out after {timeout} seconds")

    return {"response": "Task completed within timeout"}


def real_task_tool_test() -> Dict[str, Any]:
    """
    Integration test that would actually invoke the Task tool.

    This cannot be run from Python - it must be invoked by asking Claude
    to use the Task tool during a Claude Code session.

    Returns:
        Result from Task tool invocation

    Raises:
        NotImplementedError: Always, because Task tool requires Claude Code
    """
    raise NotImplementedError(
        "Task tool can only be invoked by Claude Code, not Python. "
        "To test this:\n"
        "1. Start a Claude Code session\n"
        "2. Ask Claude to spawn a subagent via Task tool\n"
        "3. Observe the response\n\n"
        "Example prompt:\n"
        '  \'Use the Task tool to spawn a subagent with subagent_type="general-purpose" '
        'and prompt="What is 2+2? Return just the number."\'\n'
    )


"""
ARCHITECTURE DISCOVERY (from spike):

1. **Task Tool is Claude-Only**
   - Cannot be called from Python
   - Only available during Claude Code conversations
   - This means orchestrators must be invoked BY Claude, not standalone

2. **Orchestrator Architecture Must Be**:
   ```
   User → Claude Code Session
         ↓
         Claude invokes Python orchestrator
         ↓
         Orchestrator prepares prompts/context
         ↓
         Orchestrator RETURNS instructions to Claude
         ↓
         Claude uses Task tool to spawn agents
         ↓
         Claude collects results and calls orchestrator again
   ```

3. **This Changes TASK-003/004/005**:
   - Orchestrators cannot directly call Task()
   - Instead, orchestrators must INSTRUCT Claude to use Task tool
   - This is a coordinator pattern, not a direct invocation pattern

4. **Implications for wfc-prompt-fixer**:
   - fix_prompt() prepares workspace and returns agent prompts
   - Claude reads those prompts and spawns agents via Task tool
   - Results are written to workspace
   - Orchestrator reads results and proceeds

5. **Alternative Architecture** (if Task tool supports it):
   - Check if Task tool can be invoked via subprocess/CLI
   - Check if there's a Python SDK for Task tool
   - Check if Task tool supports background/async execution

RECOMMENDATION:
- Document this as a BLOCKER for current implementation approach
- Propose alternative: Use subprocess to invoke Claude Code CLI if available
- OR: Change orchestrator to be "prompt generator" not "executor"
- OR: Investigate if Task tool has Python SDK
"""


if __name__ == "__main__":
    print("=" * 70)
    print("TASK TOOL SPIKE - TASK-003A")
    print("=" * 70)
    print()
    print("CRITICAL FINDING:")
    print("-" * 70)
    print("The Task tool is NOT a Python API. It can only be invoked by")
    print("Claude during a Claude Code conversation.")
    print()
    print("This means the current architecture assumption is INCORRECT.")
    print()
    print("PROPOSED SOLUTION:")
    print("-" * 70)
    print("1. Orchestrators become 'prompt generators' not 'executors'")
    print("2. Orchestrators prepare workspace + agent prompts")
    print("3. Orchestrators return instructions for Claude to spawn agents")
    print("4. Claude uses Task tool to spawn agents")
    print("5. Agents write results to workspace")
    print("6. Orchestrator reads results and continues")
    print()
    print("TESTING APPROACH:")
    print("-" * 70)
    print("Unit tests: Test with mocks (what we have)")
    print("Integration tests: Require Claude Code session (manual)")
    print()
    print("=" * 70)
    print()

    print("Running mock tests...")
    print()

    print("Test 1: Simple spawn")
    result = spawn_simple_analyzer("What is 2+2?")
    print(f"  Result: {result}")
    print()

    print("Test 2: Structured output")
    result = spawn_structured_analyzer("Analyze this prompt")
    print(f"  Result: {result}")
    print()

    print("Test 3: JSON parsing from markdown")
    markdown = """
    Here's the result:
    ```json
    {"status": "success", "value": 42}
    ```
    """
    result = parse_json_response(markdown)
    print(f"  Result: {result}")
    print()

    print("Test 4: Timeout simulation")
    try:
        result = spawn_agent_with_timeout("Long task", timeout=1)
        print(f"  Result: {result}")
    except TimeoutError as e:
        print(f"  Timeout raised as expected: {e}")
    print()

    print("=" * 70)
    print("SPIKE COMPLETE - See experiments/task_tool_spike_results.md")
    print("=" * 70)
