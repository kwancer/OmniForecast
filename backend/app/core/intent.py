import json
import os
from typing import Optional

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

from app.models.ontology import UserIntentOntology

# Load env vars
load_dotenv()


def construct_prompt(df_head: pd.DataFrame, user_prompt: str) -> str:
    schema_desc = UserIntentOntology.model_json_schema()

    data_summary = df_head.to_string()

    prompt = f"""
    You are an expert forecasting assistant. Your goal is to map a user's natural
    language request and a dataset sample into a structured Forecast Ontology (User Intent).

    User Request: "{user_prompt}"

    Dataset Sample (first 5 rows):
    {data_summary}

    Please analyze the request and data, and output a JSON object that strictly
    adheres to the following schema:
    {json.dumps(schema_desc, indent=2)}

    Ensure you identify:
    1. The time column and target column.
    2. The frequency/granularity.
    3. The forecast horizon (default to 12 steps if not specified).
    4. Any specific user requirements.

    Output ONLY the JSON.
    """
    return prompt


def heuristic_fallback(df: pd.DataFrame) -> UserIntentOntology:
    """
    Fallback method if LLM fails.
    """
    print("Using Heuristic Fallback...")
    # 1. Find datetime column
    time_col: Optional[str] = None
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            time_col = str(col)
            break
    if not time_col:
        # Try to parse
        for col in df.columns:
            try:
                pd.to_datetime(df[col], errors="raise")
                time_col = str(col)
                break
            except Exception:
                continue

    # 2. Find target (numeric)
    target_col: Optional[str] = None
    for col in df.columns:
        if col != time_col and pd.api.types.is_numeric_dtype(df[col]):
            target_col = str(col)
            break

    return UserIntentOntology(
        meta={
            "user_intent_summary": (
                "Inferred from heuristics (LLM Failed/Not Configured)"
            ),
            "domain_inference": "General",
            "completeness_check": "complete",
        },
        problem={
            "task_type": "time_series_regression",
            "granularity": {"unit": "month", "is_regular": True},
        },
        columns=[
            {
                "column_name": str(time_col) if time_col else "index",
                "role": "time_index",
                "data_type": "datetime",
                "future_availability": {"status": "known", "action_required": "none"},
            },
            {
                "column_name": str(target_col) if target_col else "value",
                "role": "target",
                "data_type": "continuous",
                "future_availability": {
                    "status": "unknown",
                    "action_required": "internal_forecast",
                },
            },
        ],
        requirements={
            "primary_objective": "accuracy_optimization",
            "cost_function_preference": "standard",
            "horizon_requirement": {"steps": 12, "flexibility": "approximate"},
            "output_format": "point_forecast",
        },
    )


def analyze_intent(df: pd.DataFrame, user_prompt: str) -> UserIntentOntology:
    """
    Analyzes the user intent and dataset to produce a UserIntentOntology.
    Tries Gemini first, falls back to heuristics.
    """
    print(f"DEBUG: analyze_intent called with prompt: {user_prompt}")
    api_key: Optional[str] = os.getenv("GEMINI_API_KEY")

    if not api_key or "PLACEHOLDER" in api_key:
        print("Warning: GEMINI_API_KEY not set or is placeholder. Using heuristics.")
        return heuristic_fallback(df)

    try:
        print("DEBUG: Configuring Gemini...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            generation_config={"response_mime_type": "application/json"},
        )

        print("DEBUG: Constructing prompt...")
        prompt: str = construct_prompt(df.head(), user_prompt)

        print("DEBUG: Calling Gemini API...")
        response = model.generate_content(prompt)

        print("DEBUG: Gemini response received.")
        content: str = response.text
        print(f"DEBUG: Response content: {content[:100]}...")  # Print first 100 chars

        return UserIntentOntology.model_validate_json(content)

    except Exception as e:
        exc_name = type(e).__name__
        print(f"LLM Error: {exc_name}: {e}. Falling back to heuristics.")
        import traceback

        traceback.print_exc()
        return heuristic_fallback(df)
