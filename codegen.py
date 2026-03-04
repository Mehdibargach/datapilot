"""Code generation — calls LLM to produce pandas code from schema + question."""

import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a data analyst. Generate concise pandas code to answer the question.

ALREADY AVAILABLE — do NOT import: df (DataFrame), pd, np, plt, sns, CHART_PATH.

#1 RULE — NEVER BREAK THIS:
You MUST set `result` to a human-readable string. EVERY code you generate MUST end with `result = f"..."` or `result = "..."`. If result is not set, the entire response fails. Even if you create a chart, `result` MUST contain the key numbers as text.

Other mandatory rules:
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
Color rules — THIS IS CRITICAL, read carefully:
PALETTE = ['#818CF8', '#34D399', '#F59E0B', '#F87171', '#A78BFA', '#38BDF8']
- ONE series over time (e.g. total revenue by month): single color '#818CF8' for all bars/points.
- MULTIPLE series over time (e.g. revenue by channel by month): use PALETTE, one DISTINCT color per series. Each line/bar group gets a different color. Add a legend.
- Categories comparison (e.g. top 5 products): single color '#818CF8' for all bars.
- How to decide: if plotting data grouped by a category column (channel, segment, region), use PALETTE with distinct colors. Otherwise single color.
For date axes: plt.xticks(rotation=45, ha='right') and use ax.xaxis.set_major_locator(plt.MaxNLocator(12)) to limit label count.
For long category labels: truncate to 25 chars (label[:25]+'...' if len(label)>25), rotate 30 degrees.
CRITICAL: If "top N" is asked, filter data to EXACTLY N rows BEFORE plotting. Chart must show exactly N bars/points.
plt.tight_layout(); plt.savefig(CHART_PATH, dpi=100, bbox_inches='tight', facecolor='#0A0A0A')

Other: Handle NaN with dropna(). Parse dates with pd.to_datetime() if needed. No comments, no imports, no prints.
IMPORTANT: pandas >= 2.2 — use 'ME' not 'M' for month-end frequency, 'YE' not 'Y' for year-end.

META-QUESTIONS (how, why, what method, formula, confidence, explain):
When the user asks about methodology — look at conversation history for the previous code, then set `result` to an explanation: method + formula + columns used + assumptions + limitations + confidence. Do NOT recompute — explain the previous computation. No chart needed.

Return JSON: {"code": "...", "needs_chart": true/false, "explanation": "1 sentence summary"}"""


def generate_code(schema_text: str, question: str, error_context: str | None = None, history: list | None = None) -> dict:
    """Call LLM to generate pandas code from schema + question."""
    client = OpenAI()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Schema:\n{schema_text}"},
    ]

    # Add conversation history for context
    if history:
        for turn in history[-5:]:  # Last 5 turns max to stay within token limits
            messages.append({"role": "user", "content": turn["question"]})
            messages.append({"role": "assistant", "content": f"Answer: {turn['answer']}\nCode used: {turn.get('code', 'N/A')}\nExplanation: {turn.get('explanation', 'N/A')}"})

    messages.append({"role": "user", "content": question})

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
