import os

import pandas as pd
import streamlit as st

from data_loader import load_data
from prompt_engine import suggest_prompts, prompt_to_code
from code_runner import run_code
from llm_client import ask_llm


st.set_page_config(page_title="Personal AI Data Analyst", layout="wide")
st.title("🧠 Personal AI Data Analyst — THE VISHLESHAK")

st.sidebar.header("Settings")

# --- Groq configuration in sidebar ---

st.sidebar.markdown("### Groq LLM Settings")

use_llm = st.sidebar.checkbox(
    "Use Groq LLM for custom prompts",
    value=False,
    help="If OFF, only the built-in suggested prompts will work. Custom prompts need LLM.",
)

default_model = "llama-3.3-70b-versatile"
llm_model = st.sidebar.text_input(
    "Groq model name",
    value=default_model,
    help="Example: llama-3.3-70b-versatile",
)

# Way to check if key exists (without showing it)
groq_key_present = bool(os.environ.get("GROQ_API_KEY"))
if use_llm and not groq_key_present:
    st.sidebar.warning(
        "GROQ_API_KEY not found. Set it in a .env file (local) or as an environment variable / Streamlit secret."
    )

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Developed by MRITYUNJAY TIWARI. "
)

# --- File upload ---

uploaded = st.file_uploader(
    "Upload CSV, Excel, or JSON",
    type=["csv", "xls", "xlsx", "json"],
)

if uploaded is None:
    st.info("Upload a CSV / XLSX / JSON to get started. Suggestions will appear automatically.")
    st.stop()

# --- Load data ---

try:
    df = load_data(uploaded)
except Exception as e:
    st.error(f"Failed to load file: {e}")
    st.stop()

st.success("File loaded successfully ✅")

with st.expander("Preview data (first 100 rows)"):
    st.dataframe(df.head(100))

# --- Suggested prompts ---

suggestions = suggest_prompts(df)
st.markdown("## Suggested analyses (pick one or write your own)")

col1, col2 = st.columns([3, 1])

with col1:
    selected = st.selectbox(
        "Choose a suggested prompt",
        options=suggestions,
        index=0,
    )
    custom = st.text_area(
        "Or write a custom prompt (leave blank to use the selected suggestion)",
        height=80,
    )

with col2:
    st.markdown("**Quick actions**")
    if st.button("Show all suggestions"):
        st.write(suggestions)

# Determine final prompt
final_prompt = custom.strip() if custom and custom.strip() else selected

st.markdown("### Final prompt")
st.write(final_prompt)

# --- Run analysis ---

if st.button("Run analysis"):
    with st.spinner("Running analysis..."):
        # 1) Try deterministic mapping first
        code = prompt_to_code(final_prompt, df)
        if code:
            res = run_code(df, code)

        else:
            # 2) Need LLM for this custom prompt
            if use_llm:
                raw_prompt = (
                    "User wants the following analysis on a pandas DataFrame `df`:\n"
                    f"{final_prompt}\n"
                    "Return only Python code inside a ```python ... ``` block."
                )
                llm_out = ask_llm(raw_prompt, model=llm_model)

                if llm_out.startswith("[LLM-error]"):
                    st.error("Groq LLM returned an error.")
                    st.text(llm_out)
                    st.stop()

                # attempt to extract python block
                if "```python" in llm_out:
                    try:
                        code = llm_out.split("```python", 1)[1].split("```", 1)[0]
                        res = run_code(df, code)
                    except Exception as e:
                        st.error(f"Failed to execute code from LLM: {e}")
                        st.write("Raw LLM output:")
                        st.text(llm_out)
                        st.stop()
                else:
                    st.error("LLM did not return a python code block. Showing raw output:")
                    st.text(llm_out)
                    st.stop()
            else:
                st.error(
                    "This is a custom prompt that cannot be converted deterministically. "
                    "Enable 'Use Groq LLM for custom prompts' in the sidebar or edit your prompt "
                    "to match one of the suggested patterns."
                )
                st.stop()

    # --- Display result ---

    if res["type"] == "text":
        st.markdown("#### Output (text)")
        st.text(res["output"])

    elif res["type"] == "dataframe":
        st.markdown("#### Output (table)")
        st.dataframe(res["df"])
        csv = res["df"].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download result as CSV",
            data=csv,
            file_name="result.csv",
            mime="text/csv",
        )

    elif res["type"] == "image":
        st.markdown("#### Output (chart)")
        st.image(res["path"], use_column_width=True)

    else:
        st.write("Unknown result type:", res)
