# main.py

import os, sys, json
from langchain.agents import initialize_agent
from langchain_ollama import ChatOllama
from utils.tools import available_tools
from agents.langgraph_agent import debug_tool_issue_v2 as langgraph_debug
from agents.langgraph_agent import init_llms


llm = ChatOllama(model="deepseek-coder")
USE_LANGGRAPH = os.getenv("USE_LANGGRAPH", "true").lower() in ("true", "1", "yes")

legacy_agent = initialize_agent(
    tools=available_tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True,
    handle_parsing_errors=True
)

def debug_tool_issue(input_description: str) -> str:
    init_llms()
    print("🤖 Agent analyzing...")
    return langgraph_debug(input_description) if USE_LANGGRAPH else legacy_agent.run(input_description)

def pretty_print_json(json_str: str):
    print("\n🔧 Suggested Fix:\n")
    try:
        parsed = json.loads(json_str)
        for k, v in parsed.items():
            if isinstance(v, str):
                print(f"- {k.capitalize()}: {v}")
            else:
                print(f"- {k.capitalize()}:\n{json.dumps(v, indent=2)}")
    except Exception:
        print(json_str)

def load_file_content(path: str) -> str:
    if not os.path.exists(path):
        return f"❌ File not found: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"❌ Error reading file: {e}"

def run_tests():
    tests = [
        ("Basic Logic Test", "def f(x): return -x if x < 0 else x", "abs"),
        ("Truncate Bug", "def summarize(txt): return txt[:100]", "summarize"),
        ("Invalid JSON", "{\"schema\": {\"type\": \"object\"}, \"payload\": {\"name\": 123}}", "invalid")
    ]
    for name, input_text, expected in tests:
        print(f"\n🧪 Test: {name}")
        out = debug_tool_issue(input_text)
        if expected in out:
            print("✅ Passed")
        else:
            print("❌ Failed")
            pretty_print_json(out)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        return

    print("🧠 AutoAgent Debugger")
    print("Type 'exit' to quit. Use 'file:<path>' to load a file.")
    print(f"Mode: {'LangGraph' if USE_LANGGRAPH else 'Legacy'}")

    while True:
        inp = input("> ").strip()
        if inp.lower() in ("exit", "quit"):
            break
        if inp.startswith("file:"):
            path = inp[5:].strip()
            inp = load_file_content(path)
            print(f"\n📂 Loaded file `{path}`")
        if not inp: continue
        try:
            result = debug_tool_issue(inp)
            pretty_print_json(result)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
