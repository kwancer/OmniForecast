from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from app.models.ontology import ForecastOntology

class Forecaster(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology):
        pass
        
    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        pass

class SimpleAdditiveForecaster(Forecaster):
    """
    A robust baseline forecaster using Holt-Winters Exponential Smoothing.
    Handles Trend and Seasonality automatically.
    """
    def __init__(self):
        self.model = None
        self.fit_result = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None
        
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology):
        self.time_col = next(c.column_name for c in ontology.columns if c.role == "time_index")
        self.target_col = next(c.column_name for c in ontology.columns if c.role == "target")
        
        # Ensure datetime index
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or 'D' # Default to D if unknown
        
        # Fit Exponential Smoothing
        # Trend='add', Seasonal='add' is a safe default for "Additive Regression" style
        # We can make this smarter by checking for negatives (use multiplicative if strictly positive and growing variance)
        
        try:
            self.model = ExponentialSmoothing(
                df[self.target_col],
                trend='add',
                seasonal='add',
                seasonal_periods=None, # Let statsmodels infer or use default
                freq=self.freq
            )
            self.fit_result = self.model.fit()
        except Exception as e:
            # Fallback to simple HW without seasonality if it fails (e.g. too short history)
            print(f"Warning: Full HW failed ({e}), falling back to simple trend.")
            self.model = ExponentialSmoothing(
                df[self.target_col],
                trend='add',
                seasonal=None,
                freq=self.freq
            )
            self.fit_result = self.model.fit()

    def predict(self, horizon: int) -> pd.DataFrame:
        if not self.fit_result:
            raise ValueError("Model not fitted yet.")
            
        forecast_values = self.fit_result.forecast(horizon)
        
        # Create result DataFrame
        future_dates = pd.date_range(start=self.last_date, periods=horizon+1, freq=self.freq)[1:]
        
        result_df = pd.DataFrame({
            self.time_col: future_dates,
            self.target_col: forecast_values
        })
        
        return result_df

def get_forecaster(ontology: ForecastOntology) -> Forecaster:
    # Factory method to choose model based on ontology
    # For now, just return the default
    return SimpleAdditiveForecaster()
