import io
import sys
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_code(df: pd.DataFrame, code: str):
    """
    Execute code string in a restricted local namespace.
    Returns a dict:
      - {"type": "text", "output": ...}
      - {"type": "dataframe", "df": pandas.DataFrame}
      - {"type": "image", "path": path_to_png}
    Convention:
      - If code sets `result` to a DataFrame or string, we return it.
      - If code produces a matplotlib figure, we save to temp PNG.
    """
    local_ns = {"pd": pd, "np": np, "df": df, "plt": plt}

    old_stdout = sys.stdout
    stdout_buf = io.StringIO()
    sys.stdout = stdout_buf

    try:
        exec(code, {}, local_ns)

        # Prefer explicit result_img_path if provided
        if "result_img_path" in local_ns and local_ns["result_img_path"]:
            path = local_ns["result_img_path"]
            return {"type": "image", "path": path}

        # Check for matplotlib figure
        figs = plt.get_fignums()
        if figs:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                plt.savefig(f.name, bbox_inches="tight", dpi=150)
                plt.close("all")
                return {"type": "image", "path": f.name}

        # result variable
        if "result" in local_ns:
            res = local_ns["result"]
            if isinstance(res, pd.DataFrame):
                return {"type": "dataframe", "df": res}
            else:
                return {"type": "text", "output": str(res)}

        # Fallback to printed text
        out = stdout_buf.getvalue().strip()
        if out:
            return {"type": "text", "output": out}

        return {"type": "text", "output": "Execution finished. No result produced."}

    except Exception as e:
        return {"type": "text", "output": f"Execution error: {e}"}
    finally:
        sys.stdout = old_stdout
