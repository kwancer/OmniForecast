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

    # Identify time and target columns
    try:
        time_col = next(c.column_name for c in intent.columns if c.role == "time_index")
        target_col = next(c.column_name for c in intent.columns if c.role == "target")
    except StopIteration:
        # Fallback if columns not properly defined
        return SystemAnalysis()

    # Create a copy to avoid modifying the original df
    analysis_df = df.copy()

    # Ensure time column is datetime
    if not pd.api.types.is_datetime64_any_dtype(analysis_df[time_col]):
        try:
            analysis_df[time_col] = pd.to_datetime(analysis_df[time_col])
        except Exception:
            pass  # Use as is or handle error? For analysis we try our best.

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
            if col_def.column_name in df.columns:
                # Check if numeric
                if pd.api.types.is_numeric_dtype(df[col_def.column_name]):
                    regressors.append(col_def.column_name)

    return SystemAnalysis(
        is_daily=is_daily, seasonality_mode=seasonality_mode, regressors=regressors
    )
