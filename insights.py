"""Proactive insight discovery — scans a dataset and finds anomalies, patterns, outliers."""

import json
from openai import OpenAI

from schema import schema_to_text

INSIGHT_PROMPT = """You are a senior data analyst presenting findings to a VP. No fluff, no vague statements. Every insight must be specific, quantified, and actionable.

ALREADY AVAILABLE in the code namespace: df (DataFrame), pd, np, plt, sns, CHART_PATH.

Find 3-5 NON-OBVIOUS insights the user didn't ask for. For EACH insight:
1. STATE the finding with EXACT NUMBERS (dollar amounts, percentages, counts)
2. EXPLAIN why it matters ("so what?")
3. SUGGEST one concrete action

BAD insight: "Monthly profit shows fluctuations between years."
GOOD insight: "Profit dropped 34% from Q3 ($45K) to Q4 ($29K) — investigate seasonal discounting. Consider reducing Q4 discounts by 5pp."

BAD insight: "Consumer segment is the top performer."
GOOD insight: "Consumer generates $134K profit (47% of total) but Home Office has 31% higher profit per transaction ($33.8 vs $25.8) — shift acquisition spend toward Home Office."

Categories to explore:
- Anomalies: unexpected spikes, dips, outliers WITH exact values
- Correlations: two columns that move together WITH correlation coefficient
- Segment gaps: which segment over/underperforms BY HOW MUCH
- Trends: direction + magnitude + time period
- Data quality: null rates WITH exact percentages, only if > 5%

For EACH insight, generate pandas code that computes the evidence.

MANDATORY: The code MUST compute all numbers from the actual data using pandas. NEVER hardcode numbers in strings.
MANDATORY: Set `result` to a multi-line string where each line is one insight, numbered (1. ..., 2. ..., etc). Each insight must include computed variables, NOT literal numbers you made up.
MANDATORY: Build each insight string using f-strings with computed variables. Example: f"1. Revenue dropped {pct_change:.1f}% from ${q3_rev:,.0f} to ${q4_rev:,.0f} — investigate seasonal discounting."

Chart rules (if you generate a chart):
DARK THEME MANDATORY — use this exact setup:
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('#0A0A0A')
ax.set_facecolor('#0A0A0A')
ax.tick_params(colors='#94A3B8', labelsize=9)
ax.xaxis.label.set_color('#94A3B8')
ax.yaxis.label.set_color('#94A3B8')
ax.title.set_color('#FFFFFF')
for spine in ax.spines.values(): spine.set_color('#1C1C1C')
ax.grid(True, alpha=0.1, color='#FFFFFF')
PALETTE = ['#818CF8', '#34D399', '#F59E0B', '#F87171', '#A78BFA', '#38BDF8']
plt.tight_layout(); plt.savefig(CHART_PATH, dpi=100, bbox_inches='tight', facecolor='#0A0A0A')

Rules: No imports, no comments, no prints. df, pd, np, plt, sns, CHART_PATH are already available.

Return JSON:
{"code": "pandas code that computes all insights and sets result", "explanation": "brief overview"}"""


def discover_insights(schema: dict, df_summary: str) -> dict:
    """Call LLM to generate insight-discovery code from schema + summary stats."""
    client = OpenAI()
    schema_text = schema_to_text(schema)

    try:
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
    except Exception as e:
        return {"code": f"result = 'Insights unavailable: {str(e)[:100]}'", "explanation": "API error"}

    content = response.choices[0].message.content or ""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"code": "result = 'Could not generate insights.'", "explanation": "JSON parse error"}


def get_df_summary(df) -> str:
    """Generate a compact statistical summary of the dataframe for the LLM."""
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
