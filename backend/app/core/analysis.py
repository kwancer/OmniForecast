import pandas as pd
from typing import List, Optional
from statsmodels.tsa.stattools import acf
from app.models.ontology import UserIntentOntology, SystemAnalysis


def analyze_data_characteristics(
    df: pd.DataFrame, intent: UserIntentOntology
) -> SystemAnalysis:
    """
    Analyzes the dataframe to infer system characteristics like frequency
    and seasonality.
    """
    # Create a copy to avoid modifying the original df
    analysis_df = df.copy()

    # Normalize column names (strip whitespace) to match potential intent
    # inconsistencies
    analysis_df.columns = analysis_df.columns.str.strip()

    # Identify time and target columns
    try:
        # We rely on the intent column names.
        # If the intent has "Name " but we stripped it to "Name", we might mismatch.
        # Ideally, we should also strip the intent column names here or try fuzzy match.
        # For robustness, let's try exact match first, then stripped match.

        def find_col_in_df(intent_name, df_cols):
            if intent_name in df_cols:
                return intent_name
            if intent_name.strip() in df_cols:
                return intent_name.strip()
            return intent_name  # Let it fail later or assume it's missing

        time_col_intent = next(
            c.column_name for c in intent.columns if c.role == "time_index"
        )
        target_col_intent = next(
            c.column_name for c in intent.columns if c.role == "target"
        )

        time_col = find_col_in_df(time_col_intent, analysis_df.columns)
        target_col = find_col_in_df(target_col_intent, analysis_df.columns)

    except StopIteration:
        # Fallback if columns not properly defined
        return SystemAnalysis()

    # Ensure time column is datetime
    if time_col in analysis_df.columns:
        if not pd.api.types.is_datetime64_any_dtype(analysis_df[time_col]):
            try:
                # Use format='mixed' if available (pandas 2.0+), else infer
                # 'coerce' will turn unparseable to NaT
                analysis_df[time_col] = pd.to_datetime(
                    analysis_df[time_col], errors="coerce"
                )
                analysis_df = analysis_df.dropna(subset=[time_col])
            except Exception:
                pass

    if time_col not in analysis_df.columns or target_col not in analysis_df.columns:
        return SystemAnalysis()

    analysis_df = analysis_df.set_index(time_col).sort_index()

    # Infer Frequency
    inferred_freq = pd.infer_freq(analysis_df.index)

    # Check if daily
    is_daily = False
    if inferred_freq:
        if "D" in inferred_freq:
            is_daily = True
    else:
        # Heuristic for daily: average diff is close to 24 hours
        if len(analysis_df) > 1:
            diffs = analysis_df.index.to_series().diff().dt.total_seconds().dropna()
            avg_diff = diffs.mean()
            if 80000 < avg_diff < 90000:  # ~24 hours (86400)
                is_daily = True

    # Detect Seasonality (Simple ACF approach)
    seasonality_mode = "none"
    try:
        # Ensure target is numeric
        if pd.api.types.is_numeric_dtype(analysis_df[target_col]):
            series = analysis_df[target_col].dropna()
            if len(series) > 14:  # Need enough points
                # Calculate ACF
                lag_acf = acf(series, nlags=40)

                # Check for significant peaks at typical seasonal lags
                # e.g., 7 (weekly) or 12 (monthly) or 24 (hourly)
                # We simply check if there's any strong autocorrelation > 0.4
                # after lag 0
                if any(abs(x) > 0.4 for x in lag_acf[1:]):
                    seasonality_mode = "additive"  # Default to additive

                    # Heuristic for multiplicative: if variance increases with level
                    # This is complex to robustly detect, so we stick to additive
                    # unless we want to implement a specific check
                    # (e.g. log transform check)
    except Exception:
        pass

    # Identify Regressors
    regressors = []
    for col_def in intent.columns:
        if col_def.role == "covariate":
            found_col = find_col_in_df(col_def.column_name, analysis_df.columns)
            if found_col in analysis_df.columns:
                # Check if numeric
                if pd.api.types.is_numeric_dtype(analysis_df[found_col]):
                    regressors.append(found_col)

    return SystemAnalysis(
        is_daily=is_daily, seasonality_mode=seasonality_mode, regressors=regressors
    )
