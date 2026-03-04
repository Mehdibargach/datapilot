"""Sandbox — executes LLM-generated pandas code safely."""

import io
import os
import sys
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def execute_code(code: str, df: pd.DataFrame, chart_path: str = "chart.png") -> dict:
    """Execute generated pandas code in a restricted namespace."""
    # Namespace with allowed libraries + the dataframe
    namespace = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
        "CHART_PATH": chart_path,
        "result": None,
    }

    # Clean slate for matplotlib
    plt.close("all")

    # Remove old chart if exists
    if os.path.exists(chart_path):
        os.remove(chart_path)

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(code, namespace)
        stdout_output = sys.stdout.getvalue()
    except Exception as e:
        sys.stdout = old_stdout
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        sys.stdout = old_stdout

    # Get result
    result = namespace.get("result")

    # Format result for display
    if isinstance(result, pd.DataFrame):
        result_str = result.to_string()
    elif isinstance(result, pd.Series):
        result_str = result.to_string()
    else:
        result_str = str(result)

    # Check if chart was created
    has_chart = os.path.exists(chart_path)

    return {
        "success": True,
        "result": result_str,
        "result_raw": result,
        "stdout": stdout_output,
        "chart_path": chart_path if has_chart else None,
    }
