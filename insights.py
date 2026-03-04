"""Proactive insight discovery — scans a dataset and finds anomalies, patterns, outliers."""

import json
from openai import OpenAI

from schema import schema_to_text

INSIGHT_PROMPT = """You are a senior data analyst. Given a dataset schema and a statistical summary, discover NON-OBVIOUS insights the user didn't ask for.

ALREADY AVAILABLE in the code namespace: df (DataFrame), pd, np, plt, sns, CHART_PATH.

Find 3-5 insights such as:
- Anomalies (unexpected spikes, dips, outliers)
- Correlations (two columns that move together or inversely)
- Segments that outperform/underperform
- Trends over time (if date columns exist)
- Data quality issues (high null rates, suspicious patterns)

For EACH insight, generate pandas code that computes the evidence.

MANDATORY: Set `result` to a human-readable string listing all insights with specific numbers.

Rules: No imports, no comments, no prints. df, pd, np, plt, sns, CHART_PATH are already available.

Return JSON:
{"code": "pandas code that computes all insights and sets result", "insights": ["insight 1 summary", "insight 2 summary", ...], "explanation": "brief overview"}"""


def discover_insights(schema: dict, df_summary: str) -> dict:
    """Call LLM to generate insight-discovery code from schema + summary stats."""
    client = OpenAI()
    schema_text = schema_to_text(schema)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": INSIGHT_PROMPT},
            {
                "role": "user",
                "content": f"Schema:\n{schema_text}\n\nStatistical summary:\n{df_summary}",
            },
        ],
        max_completion_tokens=2000,
    )

    return json.loads(response.choices[0].message.content)


def get_df_summary(df) -> str:
    """Generate a compact statistical summary of the dataframe for the LLM."""
    import pandas as pd

    lines = []

    # Numeric columns: describe
    num_desc = df.describe().round(2)
    lines.append("Numeric columns summary:")
    lines.append(num_desc.to_string())
    lines.append("")

    # Categorical columns: value counts (top 5)
    for col in df.select_dtypes(include=["object", "category"]).columns[:10]:
        vc = df[col].value_counts().head(5)
        lines.append(f"{col} (top 5): {dict(vc)}")

    # Null summary
    nulls = df.isnull().sum()
    if nulls.any():
        lines.append(f"\nNull counts: {dict(nulls[nulls > 0])}")

    return "\n".join(lines)
