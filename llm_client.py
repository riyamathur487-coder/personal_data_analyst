import os
from groq import Groq
from dotenv import load_dotenv

# Load .env if present (local dev)
load_dotenv()


def _get_groq_client() -> Groq:
    """
    Return a Groq client using GROQ_API_KEY from environment.
    Works with:
      - local .env (via python-dotenv)
      - real env vars
      - Streamlit Cloud secrets (also exposed as env vars)
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Set it in a .env file (local) or as an environment variable / Streamlit secret."
        )
    return Groq(api_key=api_key)


def ask_llm(prompt: str,
            model: str = "llama-3.3-70b-versatile",
            timeout: int = 60) -> str:
    """
    Send prompt to Groq Chat Completions. Returns raw string content.
    We expect the model to respond with Python code inside ```python ... ``` blocks.
    """
    try:
        client = _get_groq_client()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful data analyst. "
                        "You MUST respond with Python code only, inside a ```python ... ``` block. "
                        "The DataFrame is named `df`. Use pandas (pd) for data and matplotlib (plt) for charts. "
                        "Do not call plt.show(). Do not print explanations; only code."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"[LLM-error] {e}"
