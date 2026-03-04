"""Code generation — calls LLM to produce pandas code from schema + question."""

import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a data analyst. Generate concise pandas code to answer the question.

ALREADY AVAILABLE — do NOT import: df (DataFrame), pd, np, plt, sns, CHART_PATH.

MANDATORY:
- ALWAYS set `result` to a human-readable string with exact formatted numbers that answers EVERY PART of the question. Even if you create a chart, `result` must contain the key numbers.
- Answer ALL parts of the question. If the user asks two things, answer both.

Chart rules (only if useful):
sns.set_style('whitegrid'); plt.figure(figsize=(10,6)); add title+labels; plt.tight_layout(); plt.savefig(CHART_PATH, dpi=100, bbox_inches='tight')

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
