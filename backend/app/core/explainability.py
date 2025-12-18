import pandas as pd
from typing import List
from app.models.ontology import ForecastOntology
from app.api.schemas import ForecastMetric

def generate_explanation(
    history_df: pd.DataFrame, 
    forecast_df: pd.DataFrame, 
    ontology: ForecastOntology,
    metrics: List[ForecastMetric]
) -> str:
    """
    Generates a simple natural language summary of the forecast including performance insights.
    """
    target_col = next(c.column_name for c in ontology.columns if c.role == "target")
    
    last_hist_val = float(history_df[target_col].iloc[-1])
    last_pred_val = float(forecast_df[target_col].iloc[-1])
    
    horizon = len(forecast_df)
    
    trend = "increase" if last_pred_val > last_hist_val else "decrease"
    try:
        if last_hist_val == 0:
            pct_change = 0.0
        else:
            pct_change = ((last_pred_val - last_hist_val) / last_hist_val) * 100
    except:
        pct_change = 0.0
    
    # Extract MAE for reliability mention
    mae = next((m.value for m in metrics if m.name == "MAE"), 0.0)
    reliability = "high" if mae < (abs(last_hist_val) * 0.1) else "moderate"

    explanation = f"""
    Based on the historical data, the system forecasts a {trend} in {target_col} over the next {horizon} periods.
    The value is expected to move from {last_hist_val:.2f} to {last_pred_val:.2f}, representing a {pct_change:.1f}% change.
    
    The model indicates {reliability} reliability based on validation testing. The primary patterns identified were 
    projected forward using deterministic statistical methods.
    """
    
    return explanation.strip()
