"""
Tests for Task Tool Spike (TASK-003A)

This test verifies that the Task tool can:
1. Spawn a subagent with a simple prompt
2. Return a structured response
3. Respect timeout parameters
4. Handle JSON response parsing
"""

import pytest


class TestTaskToolSpike:
    """Test suite for Task tool integration spike."""

    def test_spawn_simple_agent_returns_valid_json(self):
        """
        Test that spawning an agent with a simple prompt returns valid JSON.

        This is the most basic test: can we call Task() and get data back?
        """
        from experiments.task_tool_spike import spawn_simple_analyzer

        test_input = "You are a helpful assistant. What is 2+2?"

        result = spawn_simple_analyzer(test_input)

        assert result is not None, "Agent should return a result"
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "response" in result, "Result should contain 'response' key"
        assert result["response"], "Response should not be empty"

    def test_spawn_agent_with_structured_output(self):
        """
        Test that agent can return structured JSON output.

        This tests if we can get the agent to return formatted JSON,
        which is critical for the Analyzer/Fixer/Reporter pipeline.
        """
        from experiments.task_tool_spike import spawn_structured_analyzer

        prompt = """
        Analyze this simple prompt and return JSON with this structure:
        {
            "grade": "A" | "B" | "C" | "D" | "F",
            "score": <float 0-100>,
            "issues": [<list of strings>]
        }

        Prompt to analyze: "Write a function that adds two numbers."
        """

        result = spawn_structured_analyzer(prompt)

        assert result is not None, "Agent should return a result"
        assert "grade" in result, "Result should have 'grade'"
        assert "score" in result, "Result should have 'score'"
        assert "issues" in result, "Result should have 'issues'"
        assert result["grade"] in ["A", "B", "C", "D", "F"], "Grade should be A-F"
        assert isinstance(result["score"], (int, float)), "Score should be numeric"
        assert isinstance(result["issues"], list), "Issues should be a list"

    def test_agent_respects_timeout(self):
        """
        Test that timeout parameter works and raises appropriate exception.

        This validates PROP-005: Agent spawning must eventually return or timeout.
        """
        from experiments.task_tool_spike import spawn_agent_with_timeout

        timeout_seconds = 1
        prompt = "Count to 1000 slowly, taking your time."

        with pytest.raises(TimeoutError, match="(?i)timeout|timed out"):
            spawn_agent_with_timeout(prompt, timeout=timeout_seconds)

    def test_agent_with_reasonable_timeout_succeeds(self):
        """
        Test that agent completes successfully with reasonable timeout.

        This ensures we don't have false positives on timeout behavior.
        """
        from experiments.task_tool_spike import spawn_agent_with_timeout

        timeout_seconds = 30
        prompt = "What is the capital of France? Return just the city name."

        result = spawn_agent_with_timeout(prompt, timeout=timeout_seconds)

        assert result is not None, "Should get result within timeout"
        assert "response" in result, "Result should contain response"

    def test_response_parsing_handles_markdown_json_blocks(self):
        """
        Test that we can parse JSON even if agent wraps it in markdown code blocks.

        Claude often returns JSON inside ```json ... ``` blocks, so we need
        to handle that gracefully.
        """
        from experiments.task_tool_spike import parse_json_response

        markdown_response = """
        Here's the analysis:

        ```json
        {
            "grade": "B",
            "score": 85,
            "issues": ["Minor formatting issue"]
        }
        ```

        Hope this helps!
        """

        result = parse_json_response(markdown_response)

        assert result is not None, "Should extract JSON from markdown"
        assert result["grade"] == "B", "Should parse grade correctly"
        assert result["score"] == 85, "Should parse score correctly"
        assert len(result["issues"]) == 1, "Should parse issues list"

    def test_response_parsing_handles_plain_json(self):
        """
        Test that we can parse plain JSON without markdown.
        """
        from experiments.task_tool_spike import parse_json_response

        plain_json = '{"grade": "A", "score": 95, "issues": []}'

        result = parse_json_response(plain_json)

        assert result is not None, "Should parse plain JSON"
        assert result["grade"] == "A", "Should parse grade correctly"
        assert result["score"] == 95, "Should parse score correctly"
        assert result["issues"] == [], "Should parse empty issues list"

    def test_response_parsing_handles_invalid_json(self):
        """
        Test that invalid JSON raises appropriate error.
        """
        from experiments.task_tool_spike import parse_json_response

        invalid_json = "This is not JSON at all!"

        with pytest.raises(ValueError, match="(?i)json|parse"):
            parse_json_response(invalid_json)


@pytest.mark.integration
class TestTaskToolIntegration:
    """
    Integration tests that actually call the Task tool.

    Run with: pytest -m integration experiments/test_task_tool_spike.py

    These tests require Claude Code CLI to be available and will actually
    spawn real subagents, so they're slower and may consume API credits.
    """

    def test_real_task_tool_spawn(self):
        """
        Integration test: Actually spawn a subagent via Task tool.

        This is the ultimate validation - does Task() actually work?
        """
        from experiments.task_tool_spike import real_task_tool_test

        result = real_task_tool_test()

        assert result is not None, "Task tool should return result"
        assert "status" in result, "Should have status"
        assert result["status"] == "success", "Task should complete successfully"
