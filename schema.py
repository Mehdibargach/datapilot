"""Schema detection — reads a CSV and extracts column types, stats, samples."""

import pandas as pd
from typing import Any


def detect_schema(csv_path: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read CSV and detect column types, stats, sample values."""
    # Try multiple encodings and delimiter detection
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(csv_path, encoding=encoding, sep=None, engine="python")
            break
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    else:
        raise ValueError("Could not read CSV: unsupported encoding or format.")

    schema = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_info": [],
    }

    for col in df.columns:
        info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_pct": round(df[col].isnull().mean() * 100, 1),
            "unique": int(df[col].nunique()),
            "sample_values": [str(v) for v in df[col].dropna().head(3).tolist()],
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            info["min"] = float(df[col].min())
            info["max"] = float(df[col].max())
            info["mean"] = round(float(df[col].mean()), 2)
        schema["column_info"].append(info)

    return df, schema


def schema_to_text(schema: dict[str, Any]) -> str:
    """Convert schema dict to a compact text representation for the LLM."""
    lines = [f"Dataset: {schema['rows']} rows, {schema['columns']} columns\n"]
    for col in schema["column_info"]:
        line = f"- {col['name']} ({col['dtype']})"
        if "min" in col:
            line += f" | range: {col['min']} to {col['max']}, mean: {col['mean']}"
        line += f" | {col['null_pct']}% null | samples: {col['sample_values']}"
        lines.append(line)
    return "\n".join(lines)
