from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.messages.utils import convert_to_messages
from langchain.output_parsers import OutputFixingParser, StructuredOutputParser
from langchain.output_parsers.structured import ResponseSchema
from langchain_ollama import ChatOllama  # ✅ new import


from typing import TypedDict, List
import time
import json
import os
import sys
import re

# Ensure utils/tools are accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.tools import (
    simulate_bug_trigger,
    simulate_paths,
    rank_bug_severity,
    generate_unit_tests,
)

# 🧠 LLM Setup
parser = StructuredOutputParser.from_response_schemas([
    ResponseSchema(name="explanation", description="What does the function do?"),
    ResponseSchema(name="bug_found", description="True if buggy, else false"),
    ResponseSchema(name="suggested_fix", description="Fix if bug found"),
    ResponseSchema(name="severity", description="Bug severity: low/medium/critical")
])


def get_llm_with_fallback(model_list=["phi3:mini", "mistral"]):
    for model in model_list:
        try:
            print(f"⚙️ Trying model: {model}")
            llm = ChatOllama(
                model=model,
               base_url="http://localhost:11434",  # ✅ for Docker
                timeout=20
            )
            parser_with_model = OutputFixingParser.from_llm(parser=parser, llm=llm)
            _ = parser_with_model.invoke("def foo(): return 42")  # sanity check
            return parser_with_model, llm
        except Exception as e:
            print(f"❌ Model {model} failed: {e}")
    raise RuntimeError("All fallback models failed.")

parsed_llm, llm = get_llm_with_fallback()

# Timer decorator
def timed_node(func):
    def wrapper(state: dict) -> dict:
        start = time.time()
        result = func(state)
        end = time.time()
        print(f"⏱️ Node '{func.__name__}' took {round(end - start, 2)} sec\n")
        return result
    return wrapper

@timed_node
def agent_node(state: dict) -> dict:
    messages = convert_to_messages(state["messages"])
    user_input = messages[-1].content

    explanation = ""
    bug_found = False
    suggested_fix = ""
    severity = "low"

    try:
        parsed = parsed_llm.invoke(user_input)
        explanation = parsed.get("explanation", "")
        bug_found = parsed.get("bug_found", False)
        suggested_fix = parsed.get("suggested_fix", "")
        severity = parsed.get("severity", "low")

    except Exception as e:
        print("⚠️ OutputFixingParser failed:", e)
        try:
            raw_response = llm.invoke([HumanMessage(content=user_input)]).content
            print("📤 Raw fallback LLM response:\n", raw_response)
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                parsed_fallback = json.loads(match.group(0))
                explanation = parsed_fallback.get("explanation", "")
                bug_found = parsed_fallback.get("bug_found", False)
                suggested_fix = parsed_fallback.get("suggested_fix", "")
                severity = parsed_fallback.get("severity", "low")
            else:
                explanation = f"⚠️ No valid JSON found in fallback response:\n{raw_response.strip()[:200]}..."
        except Exception as fallback_e:
            explanation = f"❌ Double fallback failed: {fallback_e}"

    new_messages = [AIMessage(content=json.dumps({
        "explanation": explanation,
        "bug_found": bug_found,
        "suggested_fix": suggested_fix,
        "severity": severity
    }))]

    return {
        "messages": add_messages(messages, new_messages),
        "tool_outputs": state.get("tool_outputs", []),
        "retry": False
    }

@timed_node
def bug_fixer_node(state: dict) -> dict:
    messages = convert_to_messages(state["messages"])
    try:
        last_response = json.loads(messages[-1].content)
        patch = last_response.get("suggested_fix", "").strip()
        if not patch:
            raise ValueError("No suggested_fix found.")
        print("🛠️ Applying Patch:\n", patch)
        return {
            "messages": [HumanMessage(content=patch)],
            "tool_outputs": state.get("tool_outputs", []),
            "retry": False
        }
    except Exception as e:
        print("❌ BugFixer failed:", e)
        return state

@timed_node
def verify_patch_node(state: dict) -> dict:
    messages = convert_to_messages(state["messages"])
    last = json.loads(messages[-1].content)
    patch = last.get("suggested_fix")
    retry = False

    if patch:
        works = not simulate_bug_trigger(patch, [1, 3, 2], 3)
        status = "✅ Patch works!" if works else "❌ Patch failed!"
        retry = not works
    else:
        status = "⚠️ No patch to verify."

    return {
        "messages": add_messages(messages, [AIMessage(content=status)]),
        "tool_outputs": state.get("tool_outputs", []),
        "retry": retry
    }

@timed_node
def simulate_paths_node(state: dict) -> dict:
    code = convert_to_messages(state["messages"])[0].content
    sim = simulate_paths(code)
    return {"messages": add_messages(state["messages"], [AIMessage(content=sim)]), "tool_outputs": []}

@timed_node
def severity_rank_node(state: dict) -> dict:
    code = convert_to_messages(state["messages"])[0].content
    rank = rank_bug_severity(code)
    return {"messages": add_messages(state["messages"], [AIMessage(content=f"🔺 Severity: {rank}")]), "tool_outputs": []}

@timed_node
def generate_tests_node(state: dict) -> dict:
    code = convert_to_messages(state["messages"])[0].content
    try:
        raw = generate_unit_tests(code)
        match = re.search(r"json\n(.*?)", raw, re.DOTALL)
        if match:
            test_json = json.loads(match.group(1))
        else:
            test_json = json.loads(raw)
        test_code = test_json.get("test_code", "# ❌ No 'test_code' key.")
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        test_code = raw if isinstance(raw, str) else "# ❌ Failed to parse unit test."
    return {
        "messages": add_messages(state["messages"], [AIMessage(content=test_code)]),
        "tool_outputs": []
    }

@timed_node
def summarize_all_node(state: dict) -> dict:
    messages = convert_to_messages(state["messages"])
    sections = [m.content.strip() for m in messages if isinstance(m, AIMessage)]
    summary = "\n\n---\n\n".join(sections)
    return {"messages": [AIMessage(content=summary)], "tool_outputs": []}

class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    tool_outputs: List
    retry: bool

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("bug_fixer", bug_fixer_node)
graph.add_node("verify_patch", verify_patch_node)
graph.add_node("simulate_paths", simulate_paths_node)
graph.add_node("rank_severity", severity_rank_node)
graph.add_node("generate_tests", generate_tests_node)
graph.add_node("summarize", summarize_all_node)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "verify_patch",
    lambda state: "bug_fixer" if state.get("retry") else "simulate_paths",
    {
        "bug_fixer": "bug_fixer",
        "simulate_paths": "simulate_paths"
    }
)

graph.add_edge("bug_fixer", "agent")
graph.add_edge("simulate_paths", "rank_severity")
graph.add_edge("rank_severity", "generate_tests")
graph.add_edge("generate_tests", "summarize")
graph.set_finish_point("summarize")

app = graph.compile()

def debug_tool_issue_v2(input_description: str, verbose=True):
    state = {
        "messages": [HumanMessage(content=input_description)],
        "tool_outputs": [],
        "retry": False
    }
    result = app.invoke(state, config=RunnableConfig({"run_name": "AutoAgent"}))
    final = result["messages"][-1] if result.get("messages") else AIMessage(content="⚠️ No output.")
    if verbose:
        print("🧠 Final Output:\n", final.content)
    return final.content