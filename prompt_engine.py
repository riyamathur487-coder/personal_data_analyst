import textwrap
from typing import List, Dict

import numpy as np
import pandas as pd


def _detect_column_types(df: pd.DataFrame) -> Dict[str, list]:
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = []

    # Try to infer datetime columns
    for c in df.columns:
        if np.issubdtype(df[c].dtype, np.datetime64):
            datetime_cols.append(c)
        else:
            try:
                sample = df[c].dropna().astype(str).iloc[:20]
                parsed = pd.to_datetime(sample, errors="coerce")
                if parsed.notna().sum() >= max(1, min(5, len(sample) // 2)):
                    datetime_cols.append(c)
            except Exception:
                pass

    # Categorical: non-numeric + low cardinality
    categorical = [
        c for c in df.columns
        if c not in numeric + datetime_cols and df[c].nunique(dropna=True) <= 50
    ]

    return {
        "numeric": numeric,
        "datetime": datetime_cols,
        "categorical": categorical,
    }


def suggest_prompts(df: pd.DataFrame, max_suggestions: int = 8) -> List[str]:
    """
    Returns a list of ready-to-run prompt strings for the dataset.
    Works without any LLM.
    """
    types = _detect_column_types(df)
    numeric = types["numeric"]
    datetime_cols = types["datetime"]
    categorical = types["categorical"]

    suggestions: List[str] = []

    # Dataset summary
    suggestions.append(
        "Summarize the dataset in 5 bullet points (rows, columns, missing values, numeric columns, top categorical)."
    )

    # Top values for categorical
    if categorical:
        col = categorical[0]
        suggestions.append(f"Show the top 10 counts for the categorical column '{col}'.")

    # Numeric summaries
    if numeric:
        suggestions.append(
            "Show summary statistics (count, mean, std, min, 25%, 50%, 75%, max) for numeric columns."
        )
        col = numeric[0]
        suggestions.append(f"Create a histogram of the numeric column '{col}'.")
        if len(numeric) >= 2:
            suggestions.append(
                f"Create a scatter plot comparing '{numeric[0]}' (x) vs '{numeric[1]}' (y)."
            )
        suggestions.append(f"Show the top 10 rows sorted by '{col}' descending.")

    # Time series
    if datetime_cols:
        dcol = datetime_cols[0]
        ag = numeric[0] if numeric else None
        if ag:
            suggestions.append(
                f"Create a time series of monthly sum of '{ag}' using the datetime column '{dcol}'."
            )
        else:
            suggestions.append(
                f"Show counts per month using the datetime column '{dcol}'."
            )

    # Correlation
    if len(numeric) >= 2:
        suggestions.append("Show the correlation matrix heatmap for numeric columns.")

    # Anomalies
    suggestions.append(
        "Find rows that look like anomalies using z-score > 3 on numeric columns and show top 20."
    )

    return suggestions[:max_suggestions]


def prompt_to_code(prompt: str, df: pd.DataFrame) -> str | None:
    """
    Convert known prompt templates into runnable python code strings.
    If unrecognized, return None so UI can call Groq.
    """
    p = prompt.strip().lower()

    # 1. Summary
    if p.startswith("summarize the dataset"):
        code = textwrap.dedent(
            """
            # Simple dataset summary in text
            info = []
            info.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            info.append("Column types: " + ", ".join([f"{c}:{str(df[c].dtype)[:10]}" for c in df.columns[:10]]))
            miss = df.isnull().sum().sort_values(ascending=False).head(10)
            if (miss > 0).any():
                info.append("Top missing: " + ", ".join([f"{idx}:{val}" for idx, val in miss.items() if val > 0]))
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            info.append(f"Numeric columns count: {len(numeric_cols)}")
            result = "\\n".join(["- " + i for i in info])
            """
        )
        return code

    # 2. Top counts for categorical
    if "top 10 counts for the categorical column" in p or (
        "top 10 counts" in p and "'" in p
    ):
        import re

        m = re.search(r"'([^']+)'", prompt)
        if not m:
            m = re.search(r'"([^"]+)"', prompt)
        col = m.group(1) if m else None
        if col:
            code = textwrap.dedent(
                f"""
                # top 10 counts for '{col}'
                result = df['{col}'].value_counts(dropna=False).head(10).reset_index()
                result.columns = ['value', 'count']
                """
            )
            return code

    # 3. Summary statistics for numeric
    if "summary statistics" in p or "describe" in p:
        code = textwrap.dedent(
            """
            result = df.select_dtypes(include=["number"]).describe().T
            """
        )
        return code

    # 4. Histogram
    if p.startswith("create a histogram of the numeric column") or \
       "histogram of the numeric column" in p:
        import re

        m = re.search(r"'([^']+)'", prompt)
        col = m.group(1) if m else None
        if col:
            code = textwrap.dedent(
                f"""
                # histogram for '{col}'
                plt.figure(figsize=(6, 4))
                df['{col}'].dropna().astype(float).hist(bins=30)
                plt.title('Histogram of {col}')
                plt.xlabel('{col}')
                plt.ylabel('count')
                result_img_path = None
                """
            )
            return code

    # 5. Scatter plot
    if "scatter plot comparing" in p and "vs" in p:
        import re

        m = re.search(r"'([^']+)' \\(x\\) vs '([^']+)' \\(y\\)", prompt)
        if m:
            xcol, ycol = m.group(1), m.group(2)
            code = textwrap.dedent(
                f"""
                plt.figure(figsize=(6, 4))
                df.plot.scatter(x='{xcol}', y='{ycol}')
                plt.title('{ycol} vs {xcol}')
                result_img_path = None
                """
            )
            return code

    # 6. Top rows sorted by col
    if p.startswith("show the top 10 rows sorted by"):
        import re

        m = re.search(r"by '([^']+)'", prompt)
        if m:
            col = m.group(1)
            code = textwrap.dedent(
                f"""
                result = df.sort_values('{col}', ascending=False).head(10).reset_index(drop=True)
                """
            )
            return code

    # 7. Time series monthly sum
    if "monthly sum" in p and "using the datetime column" in p:
        import re

        m = re.search(r"sum of '([^']+)' using the datetime column '([^']+)'", prompt)
        if m:
            ag, dcol = m.group(1), m.group(2)
            code = textwrap.dedent(
                f"""
                tmp = df.copy()
                tmp['{dcol}'] = pd.to_datetime(tmp['{dcol}'], errors='coerce')
                res = tmp.dropna(subset=['{dcol}'])
                res = res.set_index('{dcol}').resample('M')['{ag}'].sum().reset_index()
                result = res
                """
            )
            return code

    # 8. Counts per month
    if "counts per month using the datetime column" in p:
        import re

        m = re.search(r"datetime column '([^']+)'", prompt)
        dcol = m.group(1) if m else None
        if dcol:
            code = textwrap.dedent(
                f"""
                tmp = df.copy()
                tmp['{dcol}'] = pd.to_datetime(tmp['{dcol}'], errors='coerce')
                res = (
                    tmp.dropna(subset=['{dcol}'])
                    .set_index('{dcol}')
                    .resample('M')
                    .size()
                    .reset_index(name='count')
                )
                result = res
                """
            )
            return code

    # 9. Correlation matrix heatmap
    if "correlation matrix heatmap" in p or "correlation heatmap" in p:
        code = textwrap.dedent(
            """
            corr = df.select_dtypes(include=["number"]).corr()
            plt.figure(figsize=(6, 5))
            plt.imshow(corr, cmap="viridis", aspect="auto")
            plt.colorbar()
            plt.xticks(range(len(corr)), corr.columns, rotation=90)
            plt.yticks(range(len(corr)), corr.columns)
            plt.title("Correlation matrix")
            result_img_path = None
            """
        )
        return code

    # 10. Anomaly detection using z-score
    if "anomalies" in p and "z-score" in p:
        code = textwrap.dedent(
            """
            from scipy import stats
            num = df.select_dtypes(include=["number"]).dropna()
            if num.shape[1] == 0:
                result = pd.DataFrame()
            else:
                z = np.abs(stats.zscore(num.select_dtypes(include=["number"])))
                mask = (z > 3).any(axis=1)
                result = df.loc[mask].head(20).reset_index(drop=True)
            """
        )
        return code

    # Unknown / custom prompts -> handled by Groq
    return None
