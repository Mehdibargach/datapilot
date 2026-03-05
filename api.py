"""FastAPI backend — POST /analyze endpoint."""

import base64
import json
import os
import tempfile
import uuid

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agent import analyze, analyze_with_insights, list_datasets, DEMO_DATASETS

app = FastAPI(title="DataPilot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _encode_chart(chart_path: str | None) -> str | None:
    """Read a chart PNG and return base64-encoded string."""
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None


@app.get("/datasets")
def get_datasets():
    """List available pre-loaded demo datasets."""
    return list_datasets()


@app.post("/analyze")
async def run_analysis(
    question: str = Form(...),
    dataset: str = Form(None),
    file: UploadFile = File(None),
    include_insights: bool = Form(False),
    history: str = Form("[]"),
):
    """Analyze a CSV with a natural language question."""
    # Parse conversation history
    try:
        history_list = json.loads(history) if history else []
    except json.JSONDecodeError:
        history_list = []

    # Resolve CSV path
    if dataset and dataset in DEMO_DATASETS:
        base = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base, DEMO_DATASETS[dataset])
    elif file:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        content = await file.read()
        tmp.write(content)
        tmp.close()
        csv_path = tmp.name
    else:
        return {"success": False, "error": "Provide a dataset name or upload a CSV file."}

    # Generate unique chart paths
    uid = uuid.uuid4().hex[:8]
    chart_path = f"/tmp/chart_{uid}.png"

    try:
        if include_insights:
            result = analyze_with_insights(csv_path, question, chart_path=chart_path, history=history_list)
        else:
            result = analyze(csv_path, question, chart_path=chart_path, history=history_list)
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)[:200]}"}
    finally:
        # Clean up uploaded temp file
        if file and os.path.exists(csv_path):
            os.unlink(csv_path)

    if not result["success"]:
        return result

    # Build response
    response = {
        "success": True,
        "answer": result["answer"],
        "code": result["code"],
        "explanation": result.get("explanation", ""),
        "chart": _encode_chart(result.get("chart_path")),
        "timings": result["timings"],
    }

    if include_insights:
        insights_list = result.get("insights_list", [])
        if not insights_list:
            # Fallback: split raw insights string into lines
            raw = result.get("insights", "")
            if raw:
                insights_list = [line.strip() for line in raw.split(". ") if line.strip()]
        response["insights"] = insights_list
        response["insights_chart"] = _encode_chart(result.get("insights_chart"))

    # Clean up chart files
    for path in [result.get("chart_path"), result.get("insights_chart")]:
        if path and os.path.exists(path):
            os.unlink(path)

    return response


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
