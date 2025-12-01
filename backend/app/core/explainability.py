import pandas as pd
from app.models.ontology import ForecastOntology

def generate_explanation(history_df: pd.DataFrame, forecast_df: pd.DataFrame, ontology: ForecastOntology) -> str:
    """
    Generates a simple natural language summary of the forecast.
    """
    target_col = next(c.column_name for c in ontology.columns if c.role == "target")
    
    last_hist_val = history_df[target_col].iloc[-1]
    last_pred_val = forecast_df[target_col].iloc[-1]
    
    horizon = len(forecast_df)
    
    trend = "increase" if last_pred_val > last_hist_val else "decrease"
    pct_change = ((last_pred_val - last_hist_val) / last_hist_val) * 100
    
    explanation = f"""
    Based on the historical data, the system forecasts a {trend} in {target_col} over the next {horizon} periods.
    The value is expected to move from {last_hist_val:.2f} to {last_pred_val:.2f}, representing a {pct_change:.1f}% change.
    
    The model detected patterns in the historical data and projected them forward using an additive smoothing method.
    """
    
    return explanation
