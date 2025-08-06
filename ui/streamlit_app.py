import sys
import os
import json

# Ensure project root is on PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from agents.debugger_agent import debug_tool_issue

st.set_page_config(page_title="AutoAgent Debugger", layout="wide")
st.title("🧠 AutoAgent Debugger")

input_mode = st.radio("Input mode:", ["Text", "Upload .py file"])
user_input = ""

if input_mode == "Text":
    user_input = st.text_area("Paste code or describe issue:", height=300)
else:
    uploaded = st.file_uploader("Upload a .py/.json file", type=["py", "json"])
    if uploaded:
        user_input = uploaded.read().decode("utf-8")
        st.info(f"Loaded `{uploaded.name}`")

if st.button("🔍 Analyze"):
    if not user_input.strip():
        st.warning("Please provide input.")
    else:
        with st.spinner("Analyzing…"):
            result = debug_tool_issue(user_input)

        st.subheader("📤 Agent Response:")

        if isinstance(result, dict):
    # Already a structured dict
            st.json(result)

        elif isinstance(result, str):
            try:
                parsed = json.loads(result)
                st.json(parsed)  # Parsed stringified JSON
            except json.JSONDecodeError:
                if result.strip() == "":
                    st.warning("⚠️ Agent returned an empty response.")
                else:
                    st.warning("Could not parse JSON. Showing raw response:")
                    st.code(result, language="markdown")

        else:
            # Catch-all for other formats (e.g., LangChain message object)
            try:
                st.code(result.content if hasattr(result, "content") else str(result), language="markdown")
            except Exception as e:
                st.error(f"❌ Unexpected error displaying result: {e}")