import pytest
from unittest.mock import patch
from agents.debugger_agent import debug_tool_issue

class DummyLLM:
    def invoke(self, input_text):
        # Return mock outputs based on input
        if "summarize" in input_text:
            return "The issue is in function summarize"
        return "Invalid input"

@pytest.mark.parametrize("input_text, expected", [
    ("def summarize(txt): return txt[:100]", "summarize"),
    ("{\"schema\": {\"type\": \"object\"}, \"payload\": {\"name\": 123}}", "invalid")
])
@patch("agents.langgraph_agent.get_llm_with_fallback", return_value=(DummyLLM(), DummyLLM()))
def test_debugger_agent(mock_llm, input_text, expected):
    output = debug_tool_issue(input_text)
    print(f"Input: {input_text} → Output: {output}")
    assert expected.lower() in output.lower()
