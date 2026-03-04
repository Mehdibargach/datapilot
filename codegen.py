"""Code generation — calls LLM to produce pandas code from schema + question."""

import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a data analyst. Generate concise pandas code to answer the question.

ALREADY AVAILABLE — do NOT import: df (DataFrame), pd, np, plt, sns, CHART_PATH.

MANDATORY:
- ALWAYS set `result` to a human-readable string with exact formatted numbers that answers EVERY PART of the question. Even if you create a chart, `result` must contain the key numbers.
- Answer ALL parts of the question. If the user asks two things, answer both.
- NEVER use placeholders like [Next item] or [Next value]. Always compute ALL values from the actual data.
- Build `result` by iterating over the actual DataFrame rows/values, never by hardcoding partial strings.

Chart rules (only if useful):
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
Color rules:
- For time series (one metric over time): use a SINGLE color '#818CF8' for ALL bars/lines. Never alternate colors.
- For comparisons (multiple categories side by side): use palette ['#818CF8', '#34D399', '#F59E0B', '#F87171', '#A78BFA', '#38BDF8'], one color per category.
- For a single line chart: use '#818CF8' with linewidth=2.
For date axes: plt.xticks(rotation=45, ha='right') and use ax.xaxis.set_major_locator(plt.MaxNLocator(12)) to limit label count.
For long category labels: truncate to 25 chars (label[:25]+'...' if len(label)>25), rotate 30 degrees.
CRITICAL: If "top N" is asked, filter data to EXACTLY N rows BEFORE plotting. Chart must show exactly N bars/points.
plt.tight_layout(); plt.savefig(CHART_PATH, dpi=100, bbox_inches='tight', facecolor='#0A0A0A')

Other: Handle NaN with dropna(). Parse dates with pd.to_datetime() if needed. No comments, no imports, no prints.
IMPORTANT: pandas >= 2.2 — use 'ME' not 'M' for month-end frequency, 'YE' not 'Y' for year-end.

Return JSON: {"code": "...", "needs_chart": true/false, "explanation": "1 sentence"}"""


def generate_code(schema_text: str, question: str, error_context: str | None = None) -> dict:
    """Call LLM to generate pandas code from schema + question."""
    client = OpenAI()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Schema:\n{schema_text}\n\nQuestion: {question}"},
    ]

    if error_context:
        messages.append({
            "role": "user",
            "content": f"Previous attempt failed. Fix this error:\n{error_context}\n\nWrite the code as multi-line (not semicolons) to avoid syntax issues.",
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=messages,
        max_completion_tokens=2000,
    )

    content = response.choices[0].message.content or ""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract code from malformed JSON
        if '"code"' in content:
            import re
            match = re.search(r'"code"\s*:\s*"(.*?)"(?:\s*,|\s*})', content, re.DOTALL)
            if match:
                return {"code": match.group(1), "needs_chart": False, "explanation": "recovered from malformed JSON"}
        return {"code": "result = 'Error: could not generate code'", "needs_chart": False, "explanation": "JSON parse error"}
