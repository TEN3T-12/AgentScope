import pytest
from agents.debugger_agent import debug_tool_issue

@pytest.mark.parametrize("input_text, expected", [
    ("def summarize(txt): return txt[:100]", "summarize"),
    ("{\"schema\": {\"type\": \"object\"}, \"payload\": {\"name\": 123}}", "invalid")
])
def test_debugger_agent(input_text, expected):
    output = debug_tool_issue(input_text)
    assert expected.lower() in output.lower()
