"""Agent orchestrator — the full pipeline: CSV → schema → code → execute → answer."""

import os
import time

from schema import detect_schema, schema_to_text
from codegen import generate_code
from sandbox import execute_code
from insights import discover_insights, get_df_summary

# Pre-loaded demo datasets
DEMO_DATASETS = {
    "superstore": "data/superstore.csv",
    "saas": "data/saas_metrics.csv",
    "marketing": "data/marketing_spend.csv",
}


def _run_with_retry(schema_text, question, df, chart_path, error_context=None, history=None):
    """Generate code and execute, with 1 retry on error."""
    max_attempts = 2
    last_error = error_context

    for attempt in range(max_attempts):
        codegen_result = generate_code(schema_text, question, error_context=last_error, history=history)

        # Meta-questions return answer directly, no sandbox needed
        if codegen_result.get("_is_meta"):
            exec_result = {"success": True, "result": codegen_result.get("answer", ""), "chart_path": None}
            return codegen_result, exec_result

        code = codegen_result.get("code", "")
        exec_result = execute_code(code, df, chart_path=chart_path)

        if exec_result["success"]:
            return codegen_result, exec_result

        last_error = f"Code:\n{code}\nError: {exec_result['error']}"

    return codegen_result, exec_result


def analyze(csv_path: str, question: str, chart_path: str = "chart.png", history: list | None = None) -> dict:
    """Prompt Chaining pipeline: schema → codegen → execute → answer."""
    start = time.time()

    # Step 1: Schema detection
    df, schema = detect_schema(csv_path)
    schema_text = schema_to_text(schema)
    t_schema = time.time() - start

    # Step 2 + 3: Code generation → execution (with retry)
    codegen_result, exec_result = _run_with_retry(schema_text, question, df, chart_path, history=history)
    t_exec = time.time() - start

    if not exec_result["success"]:
        return {
            "success": False,
            "error": exec_result["error"],
            "code": codegen_result.get("code", ""),
            "timings": {"total": round(t_exec, 2)},
        }

    t_total = time.time() - start

    return {
        "success": True,
        "answer": exec_result["result"],
        "code": codegen_result.get("code", ""),
        "chart_path": exec_result.get("chart_path"),
        "explanation": codegen_result.get("explanation", ""),
        "timings": {
            "schema": round(t_schema, 2),
            "analysis": round(t_exec - t_schema, 2),
            "total": round(t_total, 2),
        },
    }


def analyze_with_insights(csv_path: str, question: str, chart_path: str = "chart.png", history: list | None = None) -> dict:
    """Full pipeline: answer + proactive insights + recommendations."""
    start = time.time()

    # Step 1: Schema detection
    df, schema = detect_schema(csv_path)
    schema_text = schema_to_text(schema)

    # Step 2: Answer the question
    codegen_result, exec_result = _run_with_retry(schema_text, question, df, chart_path, history=history)
    t_answer = time.time() - start

    if not exec_result["success"]:
        return {
            "success": False,
            "error": exec_result["error"],
            "code": codegen_result.get("code", ""),
            "timings": {"total": round(t_answer, 2)},
        }

    # Step 3: Proactive insights (parallel-ready, separate LLM call)
    df_summary = get_df_summary(df)
    insight_result = discover_insights(schema, df_summary)
    insight_code = insight_result.get("code", "")
    t_insights_gen = time.time() - start

    # Execute insight code
    insight_chart = chart_path.replace(".png", "_insights.png")
    insight_exec = execute_code(insight_code, df, chart_path=insight_chart)
    t_insights_exec = time.time() - start

    insights_text = ""
    insights_from_code = []
    if insight_exec["success"]:
        insights_text = insight_exec["result"]
        raw = insights_text.strip()
        for line in raw.split("\n"):
            line = line.strip()
            if line and len(line) > 10:
                clean = line.lstrip("0123456789.-) ").strip()
                if clean:
                    insights_from_code.append(clean)

    # Use code-computed insights (accurate), fallback to LLM-generated
    recommendations = insights_from_code if insights_from_code else insight_result.get("insights", [])

    t_total = time.time() - start

    return {
        "success": True,
        "answer": exec_result["result"],
        "code": codegen_result.get("code", ""),
        "chart_path": exec_result.get("chart_path"),
        "explanation": codegen_result.get("explanation", ""),
        "insights": insights_text,
        "insights_list": recommendations,
        "insights_chart": insight_exec.get("chart_path") if insight_exec["success"] else None,
        "timings": {
            "answer": round(t_answer, 2),
            "insights_gen": round(t_insights_gen - t_answer, 2),
            "insights_exec": round(t_insights_exec - t_insights_gen, 2),
            "total": round(t_total, 2),
        },
    }


def list_datasets() -> dict:
    """List available pre-loaded demo datasets."""
    result = {}
    base = os.path.dirname(os.path.abspath(__file__))
    for name, path in DEMO_DATASETS.items():
        full_path = os.path.join(base, path)
        exists = os.path.exists(full_path)
        result[name] = {"path": full_path, "available": exists}
    return result


if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/superstore.csv"
    question = sys.argv[2] if len(sys.argv) > 2 else "What is the total sales amount?"
    mode = sys.argv[3] if len(sys.argv) > 3 else "simple"

    if mode == "insights":
        result = analyze_with_insights(csv_path, question)
    else:
        result = analyze(csv_path, question)

    if result["success"]:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        print(f"\nAnswer: {result['answer']}")
        if result.get("insights"):
            print(f"\n--- Proactive Insights ---")
            print(result["insights"])
        if result.get("insights_list"):
            print(f"\n--- Recommendations ---")
            for i, rec in enumerate(result["insights_list"], 1):
                print(f"  {i}. {rec}")
        print(f"\nTimings: {result['timings']}")
        if result.get("chart_path"):
            print(f"Chart: {result['chart_path']}")
    else:
        print(f"ERROR: {result['error']}")
