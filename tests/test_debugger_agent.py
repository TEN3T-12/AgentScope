import pytest
from unittest.mock import patch
from agents.debugger_agent import debug_tool_issue

# Dummy LLM mock to simulate LangGraph node LLM behavior
class DummyLLM:
    def invoke(self, input_data, config=None):
        # Simulate LangGraph output structure
        if isinstance(input_data, str):
            if "summarize" in input_data:
                return {"output": "The bug is in the 'summarize' function."}
            else:
                return {"output": "Invalid input"}
        elif isinstance(input_data, dict):
            code = input_data.get("code", "")
            if "summarize" in code:
                return {"output": "The bug is in the 'summarize' function."}
            else:
                return {"output": "Invalid code"}
        return {"output": "Unrecognized input"}

# Parametrized tests with expected keywords in output
@pytest.mark.parametrize("input_text, expected_keyword", [
    ("def summarize(txt): return txt[:100]", "summarize"),
    ("{\"schema\": {\"type\": \"object\"}, \"payload\": {\"name\": 123}}", "invalid")
])
@patch("agents.langgraph_agent.get_llm_with_fallback", return_value=(DummyLLM(), DummyLLM()))
def test_debugger_agent(mock_llm, input_text, expected_keyword):
    result = debug_tool_issue(input_text)
    print(f"Input:\n{input_text}\n→ Output:\n{result}\n")
    assert expected_keyword.lower() in result.lower()
