import pytest
from unittest.mock import patch
from agents.debugger_agent import debug_tool_issue


# 🧠 Updated dummy LLM to mimic real LangGraph output format
class DummyLLM:
    def invoke(self, input_data, config=None):
        if isinstance(input_data, str) or isinstance(input_data, dict):
            code = input_data if isinstance(input_data, str) else input_data.get("code", "")

            if "summarize" in code:
                return {
                    "explanation": "There's a bug in the summarize function.",
                    "bug_found": True,
                    "suggested_fix": "Ensure proper slicing with boundary checks.",
                    "severity": "medium"
                }
            else:
                return {
                    "explanation": "Payload format does not match schema.",
                    "bug_found": True,
                    "suggested_fix": "Validate input types before processing.",
                    "severity": "high"
                }
        return {
            "explanation": "",
            "bug_found": False,
            "suggested_fix": "",
            "severity": "low"
        }


@pytest.mark.parametrize("input_text, expected_keyword", [
    ("def summarize(txt): return txt[:100]", "summarize"),
    ('{"schema": {"type": "object"}, "payload": {"name": 123}}', "payload")
])
@patch("agents.langgraph_agent.get_llm_with_fallback", return_value=(DummyLLM(), DummyLLM()))
def test_debugger_agent(mock_llm, input_text, expected_keyword):
    result = debug_tool_issue(input_text)
    print(f"🧪 Test Input:\n{input_text}\n🧠 Output:\n{result}\n")
    
    # Since result is a JSON string, let's parse it first
    import json
    result_json = json.loads(result)

    # ✅ Validate keys and expected content
    assert result_json["bug_found"] is True
    assert expected_keyword.lower() in result_json["explanation"].lower() or \
           expected_keyword.lower() in result_json["suggested_fix"].lower()
