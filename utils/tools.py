from langchain.tools import Tool
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage
import requests
import ast
import json

# LLM setup
llm = ChatOllama(model="mistral")

# External MCP-Based Tools

def call_code_parser(code: str) -> str:
    try:
        response = requests.post("http://localhost:8000/parse-function/", json={"code": code})
        return response.text or "⚠️ Empty response from Code Parser"
    except Exception as e:
        return f"❌ CodeParser error: {e}"

code_parser_tool = Tool(
    name="CodeParser",
    func=call_code_parser,
    description="Extracts function name, arguments, and docstring from Python code."
)

def validate_json_with_mcp(data: dict) -> str:
    try:
        response = requests.post("http://localhost:8001/validate-json/", json=data)
        return response.text
    except Exception as e:
        return f"❌ JSON Validator error: {e}"

json_validator_tool = Tool(
    name="JSONValidator",
    func=validate_json_with_mcp,
    description="Validates a JSON payload against schema using MCP."
)

# LLM-Based Tools

def classify_bug_type_llm(input_text: str) -> str:
    prompt = f"""Classify the bug in this code or error log:

\"\"\"{input_text}\"\"\"

Format:
Bug Type: <type>
Reason: <explanation>"""
    try:
        response = llm([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return f"Error: {e}"

bug_type_classifier_tool = Tool(
    name="BugTypeClassifier",
    func=classify_bug_type_llm,
    description="LLM classifies code bugs by type and cause."
)

def simulate_bug_trigger(code: str, test_input: list, expected: int) -> bool:
    try:
        namespace = {}
        exec(code, namespace)
        func = [v for v in namespace.values() if callable(v)][0]
        result = func(test_input)
        print(f"🔍 Simulated result: {result} | Expected: {expected}")
        return result != expected
    except Exception as e:
        print(f"❌ Simulation Error: {e}")
        return True

def refactor_code_llm(code: str) -> str:
    prompt = f"""Refactor this code for readability and best practices:

```python
{code}
```"""
    try:
        response = llm([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return f"Error: {e}"

refactor_code_tool = Tool(
    name="RefactorCode",
    func=refactor_code_llm,
    description="Refactors Python code using LLM."
)

def suggest_fix_llm(code: str) -> str:
    prompt = f"""You're a code-fixing assistant. Suggest a fix for:

```python
{code}
```"""
    try:
        response = llm([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return f"Error: {e}"

suggest_fix_tool = Tool(
    name="SuggestFix",
    func=suggest_fix_llm,
    description="Suggests corrections to buggy Python code using LLM."
)

# Static Analyzers

def visualize_flow(code: str) -> dict:
    try:
        tree = ast.parse(code)
        branches, loops, calls = [], [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                branches.append(ast.unparse(node.test))
            elif isinstance(node, (ast.For, ast.While)):
                loops.append(ast.unparse(node))
            elif isinstance(node, ast.Call):
                calls.append(ast.unparse(node.func))
        return {
            "branches": branches,
            "loops": loops,
            "function_calls": calls
        }
    except Exception as e:
        return {"error": str(e)}

flow_visualizer_tool = Tool(
    name="FlowVisualizer",
    func=visualize_flow,
    description="Returns JSON of branches, loops, and function calls from code."
)

def explain_code(code: str) -> str:
    if "def" in code and "return" in code:
        return "🔍 Likely a function returning a value — maybe a slice, transformation, or computed result."
    return "🤔 Can't determine purpose — not a function?"

code_explainer_tool = Tool(
    name="CodeExplainer",
    func=explain_code,
    description="Explains what a function or code snippet is doing."
)

# Advanced Utilities

def simulate_paths(code: str) -> str:
    try:
        tree = ast.parse(code)
        results = ["📈 Simulated Execution Path:"]
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                results.append(f"- If `{ast.unparse(node.test)}` is True → executes branch.")
            elif isinstance(node, ast.Return):
                results.append(f"- Returns → {ast.unparse(node.value)}")
        return "\n".join(results)
    except Exception as e:
        return f"Simulation failed: {e}"

def generate_unit_tests(code: str) -> str:
    prompt = f"""
    You're a test generation AI. Given this function, return a valid pytest unit test as a JSON with this format:

    {{
        "test_code": "<PYTEST CODE>"
    }}
    Function:
```python
{code}
```"""
    try:
        response = llm([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return f"# Test generation failed: {e}"


def rank_bug_severity(code: str) -> str:
    prompt = f"""Analyze the code and return bug severity:

low: stylistic or non-critical

medium: unexpected behavior

critical: logic-breaking bug Return only one word: low, medium, or critical."""
    try:
        response = llm([HumanMessage(content=prompt)])
        return response.content.strip().lower()
    except Exception as e:
        return f"Error: {e}"

def patch_code(code_str: str, agent_output: str):
    try:
        fix = json.loads(agent_output).get("suggested_fix")
        return f"\n🔧 Suggested Patch:\n# {fix}\n{code_str}"
    except:
        return "# No fix available or invalid agent output."


def simulate_execution(code_str: str):
    print("\n📊 Simulated Execution:")
    try:
        exec(code_str)
        print("✅ Execution successful.")
    except Exception as e:
        print("❌ Simulation failed:", e)


def generate_tests(code_str: str):
    print("\n🧪 Suggested Unit Test:")
    try:
        if "return" in code_str:
            ret_expr = code_str.split("return")[-1].strip()
            print(f"def test_case():\n    assert {ret_expr} == expected")
        else:
            print("# No return statement found.")
    except Exception as e:
        print(f"# Test generation failed: {e}")


available_tools = [
code_parser_tool,
json_validator_tool,
bug_type_classifier_tool,
code_explainer_tool,
refactor_code_tool,
suggest_fix_tool,
flow_visualizer_tool
]
 


