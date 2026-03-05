"""Code generation — calls LLM to produce pandas code from schema + question."""

import json
import re
from openai import OpenAI

META_KEYWORDS = re.compile(
    r"\b(how did you|what method|what formula|how confident|"
    r"explain.*(approach|method|calculation)|"
    r"what.*(formula|method)|"
    r"how.*(calculat|comput|analyz|deriv|predict|project)|"
    r"give me.*(formula|method|approach|explanation)|"
    r"show me.*(formula|method|approach)|"
    r"what approach|what technique|why did you|"
    r"(the|your) (method|formula|approach|logic))\b",
    re.IGNORECASE,
)

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

ANTI-HALLUCINATION — CRITICAL:
- If the question asks about data, columns, or metrics NOT present in the schema, respond with: result = "This dataset does not contain [X]. Available columns are: [list relevant ones]."
- NEVER invent proxies (e.g., do NOT use 'profit' as a proxy for 'satisfaction'). If the exact data is not there, say so.
- If the question references a time period not covered by the data, state: result = "The data covers [start] to [end]. No data available for [requested period]."

Other: Handle NaN with dropna(). Parse dates with pd.to_datetime() if needed. No comments, no imports, no prints.
IMPORTANT: pandas >= 2.2 — use 'ME' not 'M' for month-end frequency, 'YE' not 'Y' for year-end.
result MUST be a human-readable string, NEVER a raw DataFrame or Series. Convert to string with actual values.

Return JSON: {"code": "...", "needs_chart": true/false, "explanation": "1 sentence summary"}"""

META_SYSTEM = """You are a data analyst explaining your methodology. The user is asking about a PREVIOUS analysis.

Here is the previous question, answer, and code:
Question: {prev_q}
Answer: {prev_a}
Code: {prev_code}

Explain clearly:
1. Method used and the actual formula/logic from the code above
2. Which columns and data were used
3. Assumptions made
4. Limitations (e.g., naive projection, no seasonality, limited data)
5. Confidence level (high/medium/low with reason)

Do NOT recompute anything. Just explain.

Return JSON: {{"answer": "your explanation text here", "explanation": "methodology explanation"}}"""


def generate_code(schema_text: str, question: str, error_context: str | None = None, history: list | None = None) -> dict:
    """Call LLM to generate pandas code from schema + question."""
    # Detect meta-questions and handle with dedicated prompt
    if history and META_KEYWORDS.search(question):
        last = history[-1]
        return _generate_meta_answer(last, question)

    client = OpenAI()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Schema:\n{schema_text}"},
    ]

    # Add conversation history for context
    if history:
        for turn in history[-5:]:
            messages.append({"role": "user", "content": turn["question"]})
            messages.append({"role": "assistant", "content": f"Answer: {turn['answer']}\nCode used: {turn.get('code', 'N/A')}\nExplanation: {turn.get('explanation', 'N/A')}"})

    messages.append({"role": "user", "content": question})

    if error_context:
        messages.append({
            "role": "user",
            "content": f"Previous attempt failed. Fix this error:\n{error_context}\n\nWrite the code as multi-line (not semicolons) to avoid syntax issues.",
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages,
            max_completion_tokens=2000,
        )
    except Exception as e:
        return {"code": f"result = 'LLM service error: {str(e)[:100]}'", "needs_chart": False, "explanation": "API error"}

    content = response.choices[0].message.content or ""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        if '"code"' in content:
            match = re.search(r'"code"\s*:\s*"(.*?)"(?:\s*,|\s*})', content, re.DOTALL)
            if match:
                return {"code": match.group(1), "needs_chart": False, "explanation": "recovered from malformed JSON"}
        return {"code": "result = 'Error: could not generate code'", "needs_chart": False, "explanation": "JSON parse error"}


def _generate_meta_answer(prev_turn: dict, question: str) -> dict:
    """Handle meta-questions — returns answer directly, no code execution needed."""
    client = OpenAI()
    system = META_SYSTEM.format(
        prev_q=prev_turn.get("question", "N/A"),
        prev_a=prev_turn.get("answer", "N/A"),
        prev_code=prev_turn.get("code", "N/A"),
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            max_completion_tokens=1000,
        )
    except Exception as e:
        return {"_is_meta": True, "answer": f"Could not explain methodology: {str(e)[:100]}", "explanation": "API error"}

    content = response.choices[0].message.content or ""
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"answer": "Could not explain methodology."}

    result["_is_meta"] = True
    return result
