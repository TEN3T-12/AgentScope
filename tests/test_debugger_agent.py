import pytest
from unittest.mock import patch
from agents.debugger_agent import debug_tool_issue

# Dummy LLM response (optional based on how debug_tool_issue works)
class DummyLLM:
    def invoke(self, input_text):
        # Simulate a dummy LLM response for your tests
        if "summarize" in input_text:
            return "Function name: summarize"
        return "Invalid input detected"

@pytest.mark.parametrize("input_text, expected", [
    ("def summarize(txt): return txt[:100]", "summarize"),
    ("{\"schema\": {\"type\": \"object\"}, \"payload\": {\"name\": 123}}", "invalid")
])
@patch("agents.langgraph_agent.get_llm_with_fallback", return_value=DummyLLM())
def test_debugger_agent(mock_llm, input_text, expected):
    output = debug_tool_issue(input_text)
    print(f"Input: {input_text} → Output: {output}")
    assert expected.lower() in output.lower()
