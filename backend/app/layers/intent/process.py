import json
import os
import traceback
from typing import Optional

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

from app.domain.ontology import Constraints, ForecastOntology

# Load env vars
load_dotenv()


class GeminiIntentAnalyzer:
    """
    Two-Stage Analyzer:
    1. LLM infers structure (Columns, Intent, Horizon).
    2. Python calculates statistics (Sparsity) based on that structure.
    """

    def _construct_prompt(self, df_head: pd.DataFrame, user_prompt: str) -> str:
        """
        Stage 1 Prompt: Asks only for structural mapping, not data profiling.
        """
        schema_desc = ForecastOntology.model_json_schema()
        data_summary = df_head.to_string()

        prompt = f"""
        You are an expert forecasting architect.
        User Request: "{user_prompt}"

        Dataset Sample (first 5 rows):
        {data_summary}

        Task: Map this to a Forecast Ontology.
        - Identify the 'target' and 'time_index' columns.
        - Infer the user's constraints (e.g. non-negative).
        - LEAVE 'sparsity_ratio' as null (the system will calculate this later).
        - For the time_index column, CAREFULLY analyze the date format in the sample data
          and provide the 'date_format' field using Python strftime notation. Examples:
          * '2024-01-15' -> '%Y-%m-%d'
          * '88-01-01' (2-digit year, month, day) -> '%y-%m-%d'
          * '15/01/2024' -> '%d/%m/%Y'
          * '1-01' (year-month only, like 2001-01) -> This is non-standard, set null
          * 'Jan 15, 2024' -> '%b %d, %Y'
          If the format is non-standard or unclear, set date_format to null.

        Output ONLY the JSON adhering to:
        {json.dumps(schema_desc, indent=2)}
        """
        return prompt

    def _clean_display_name(self, name: str) -> str:
        """
        Converts 'total_revenue' or 'totalRevenue' to 'Total Revenue'.
        """
        # Replace underscores and hyphens with spaces
        s = name.replace("_", " ").replace("-", " ")
        # Insert spaces before capital letters (camelCase)
        import re
        s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
        # Title case
        return s.title().strip()

    def _enrich_ontology(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> ForecastOntology:
        """
        Stage 2: Python Statistical Profiling.
        Uses the LLM's structural definitions to calculate targeted stats (Sparsity).
        """
        # Clean display names for all columns
        for col in ontology.columns:
            if not col.display_name or col.display_name == col.column_name:
                col.display_name = self._clean_display_name(col.column_name)
            else:
                col.display_name = self._clean_display_name(col.display_name)

        # 1. Identify Target Column from Ontology
        target_def = next((c for c in ontology.columns if c.role == "target"), None)

        if target_def:
            col_name = target_def.column_name
            # Verify column exists in the full dataframe
            if col_name in df.columns:
                series = df[col_name]

                # A. Calculate Sparsity Ratio (The "Fact")
                # We only calculate this for numeric targets
                if pd.api.types.is_numeric_dtype(series):
                    zero_count = (series == 0).sum()
                    ratio = zero_count / len(df)

                    # Initialize constraints object if it doesn't exist
                    if not target_def.constraints:
                        target_def.constraints = Constraints()

                    # Store the exact number (0.0 - 1.0)
                    target_def.constraints.sparsity_ratio = float(ratio)

                    print(f"LOG: Enriched Ontology with Sparsity Ratio: {ratio:.2%}")

        # POPULATE SAMPLE DATA
        # Convert first 5 rows to a list of dictionaries, handling NaNs
        sample = df.head(5).fillna("").to_dict(orient="records")
        ontology.sample_data = sample

        return ontology

    def _heuristic_fallback(self, df: pd.DataFrame) -> ForecastOntology:
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

        return ForecastOntology.model_validate(
            {
                "meta": {
                    "user_intent_summary": "Inferred from heuristics (LLM Failed)",
                    "domain_inference": "General",
                    "completeness_check": "complete",
                },
                "problem": {
                    "task_type": "time_series_regression",
                    "granularity": {"unit": "month", "is_regular": True},
                },
                "columns": [
                    {
                        "column_name": str(time_col) if time_col else "index",
                        "role": "time_index",
                        "data_type": "datetime",
                        "future_availability": {
                            "status": "known",
                            "action_required": "none",
                        },
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
                "requirements": {
                    "primary_objective": "accuracy_optimization",
                    "cost_function_preference": "standard",
                    "horizon_requirement": {"steps": 12, "flexibility": "approximate"},
                    "output_format": "point_forecast",
                },
            }
        )

    def analyze(self, df: pd.DataFrame, user_prompt: str) -> ForecastOntology:
        """
        Analyzes the user intent and dataset to produce a ForecastOntology.
        Tries Gemini first -> Enriches with Python Stats -> Falls back to heuristics.
        """
        print(f"DEBUG: analyze_intent called with prompt: {user_prompt}")
        api_key: Optional[str] = os.getenv("GEMINI_API_KEY")

        if not api_key or "PLACEHOLDER" in api_key:
            print("Warning: GEMINI_API_KEY not set. Using heuristics.")
            ontology = self._heuristic_fallback(df)
            # Even in fallback, we should calculate stats!
            return self._enrich_ontology(df, ontology)

        try:
            print("DEBUG: Configuring Gemini...")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                generation_config={"response_mime_type": "application/json"},
            )

            print("DEBUG: Constructing prompt...")
            # Stage 1: LLM Inference
            prompt = self._construct_prompt(df.head(), user_prompt)

            print("DEBUG: Calling Gemini API...")
            response = model.generate_content(prompt)
            print("DEBUG: Gemini response received.")

            ontology = ForecastOntology.model_validate_json(response.text)

            # Stage 2: Python Enrichment
            ontology = self._enrich_ontology(df, ontology)

            return ontology

        except Exception as e:
            exc_name = type(e).__name__
            print(f"LLM Error: {exc_name}: {e}. Falling back to heuristics.")
            traceback.print_exc()
            ontology = self._heuristic_fallback(df)
            return self._enrich_ontology(df, ontology)
