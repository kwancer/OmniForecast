import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from skforecast.direct import ForecasterDirect
from typing import Any, Dict, List, Optional, Tuple

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata
from app.layers.forecasting.base import InternalForecaster, calculate_metrics

class SkforecastForecaster(InternalForecaster):
    complexity_score = 7
    archetype = "The Direct Strategist (Zero-Leakage ML)"

    def __init__(self, regressor_type='lightgbm'):
        self.regressor_type = regressor_type
        if regressor_type == 'lightgbm':
            self.regressor = LGBMRegressor(random_state=42, n_estimators=100, verbose=-1)
        else:
            from sklearn.ensemble import RandomForestRegressor
            self.regressor = RandomForestRegressor(random_state=42, n_estimators=100)
            
        self.forecaster = None
        self.time_col = None
        self.target_col = None
        self.known_cols = []
        self.unknown_cols = []
        self.engineered_unknown_cols = []
        self.lag_window = 7
        self.last_date = None
        self.freq = None
        self.history_df = None
        self.residuals_std = 0.0

    def prep_forecasting_data(self, df: pd.DataFrame, target_col: str, known_cols: List[str], unknown_cols: List[str]):
        # 1. KNOWN FUTURES: Leave these exactly as they are.
        df_processed = df[[target_col] + known_cols].copy()
        
        # 2. UNKNOWN PASTS: Mathematically prevent leakage by shifting them.
        engineered_unknown = []
        for col in unknown_cols:
            for lag in range(1, self.lag_window + 1):
                lag_name = f"{col}_lag_{lag}"
                df_processed[lag_name] = df[col].shift(lag)
                engineered_unknown.append(lag_name)
                
        # Drop rows with NaNs caused by the lagging process
        df_processed = df_processed.dropna()
        return df_processed, engineered_unknown

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(c.column_name for c in ontology.columns if c.role == "time_index")
        self.target_col = next(c.column_name for c in ontology.columns if c.role == "target")
        
        # Identify buckets - ensuring we only take numeric columns for now to prevent model crashes
        # (categorical encoding could be added here in the future)
        self.known_cols = [
            c.column_name for c in ontology.columns 
            if c.role == "covariate" 
            and c.covariate_type in ["known_future", "controllable"]
            and pd.api.types.is_numeric_dtype(df[c.column_name])
        ]
        self.unknown_cols = [
            c.column_name for c in ontology.columns 
            if c.role == "covariate" 
            and c.covariate_type in ["unknown_past", "exogenous"]
            and pd.api.types.is_numeric_dtype(df[c.column_name])
        ]
        
        # Set index
        df = df.copy()
        df[self.time_col] = pd.to_datetime(df[self.time_col])
        df = df.set_index(self.time_col)
        self.freq = pd.infer_freq(df.index) or 'D'
        df.index.freq = self.freq # Crucial for skforecast
        self.last_date = df.index.max()
        
        # Prep data
        df_processed, self.engineered_unknown_cols = self.prep_forecasting_data(df, self.target_col, self.known_cols, self.unknown_cols)
        
        # Safety check: if lagging killed too many rows
        if len(df_processed) < 10:
            print(f"LOG: Skforecast skipped - only {len(df_processed)} rows left after lagging.")
            return [ForecastMetric(name="MAE", value=float("inf"))]

        self.history_df = df_processed.copy()
        
        all_exog_features = self.known_cols + self.engineered_unknown_cols
        horizon_steps = ontology.requirements.horizon_requirement.steps
        
        # Initialize Forecaster
        self.forecaster = ForecasterDirect(
            estimator=self.regressor,
            steps=horizon_steps,
            lags=14 # Target lags
        )
        
        # Train/Val Split (80/20)
        split_idx = int(len(df_processed) * 0.8)
        if split_idx < 20: split_idx = len(df_processed) - 5 # Ensure some val
        if split_idx <= 0: raise ValueError("Not enough data to train skforecast.")
        
        df_train = df_processed.iloc[:split_idx]
        df_val = df_processed.iloc[split_idx:]
        
        # Fit on train
        self.forecaster.fit(
            y=df_train[self.target_col],
            exog=df_train[all_exog_features] if all_exog_features else None
        )
        
        # Validate
        if len(df_val) > 0:
            # skforecast predict needs exog for the val period
            val_steps = len(df_val)
            # ForecasterAutoregDirect predict() only predicts up to 'steps' defined at init
            # If val_steps > steps, we need to handle it. For now assume it's okay or clamp.
            predict_steps = min(val_steps, horizon_steps)
            
            val_preds = self.forecaster.predict(
                steps=predict_steps,
                exog=df_val[all_exog_features].iloc[:predict_steps] if all_exog_features else None
            )
            
            y_val = df_val[self.target_col].iloc[:predict_steps]
            self.validation_predictions = val_preds
            self.validation_actuals = y_val
            
            metrics = calculate_metrics(y_val, val_preds)
            self.residuals_std = float(np.std(y_val.values - val_preds.values))
        else:
            metrics = [ForecastMetric(name="MAE", value=float("inf"))]

        # Refit on full data
        self.forecaster.fit(
            y=df_processed[self.target_col],
            exog=df_processed[all_exog_features] if all_exog_features else None
        )
        
        return metrics

    def predict(self, horizon: int, ontology: Optional[ForecastOntology] = None, interval_width: float = 0.80) -> pd.DataFrame:
        if not self.forecaster: raise ValueError("Model not fitted.")
        
        # 1. Prepare Future Exog
        # Known Future: from overrides
        overrides = ontology.scenario_overrides or {} if ontology else {}
        future_dates = pd.date_range(start=self.last_date, periods=horizon + 1, freq=self.freq)[1:]
        
        future_exog_known = pd.DataFrame(index=future_dates)
        for col in self.known_cols:
            val = overrides.get(col)
            if isinstance(val, list):
                # Use provided series
                future_exog_known[col] = (val + [val[-1]] * horizon)[:horizon]
            elif val is not None:
                future_exog_known[col] = float(val)
            else:
                # Status quo: use last historical value
                future_exog_known[col] = self.history_df[col].iloc[-1]
                
        # Unknown Past: Static block of last known lags
        last_known_lags = self.history_df[self.engineered_unknown_cols].iloc[-1:]
        future_exog_unknown = pd.concat([last_known_lags] * horizon)
        future_exog_unknown.index = future_dates
        
        final_future_exog = pd.concat([future_exog_known, future_exog_unknown], axis=1)
        all_features = self.known_cols + self.engineered_unknown_cols
        final_future_exog = final_future_exog[all_features] if all_features else None

        # 2. Predict
        # skforecast predict
        preds = self.forecaster.predict(steps=horizon, exog=final_future_exog)
        
        # 3. Intervals (Simple Normal approximation for now as skforecast intervals vary by regressor)
        z = 1.28 if interval_width == 0.80 else 1.96
        lower = preds - (z * self.residuals_std)
        upper = preds + (z * self.residuals_std)
        
        # Multi-layer intervals for premium UI
        intervals = self._calculate_multi_layer_intervals(preds.values, self.residuals_std)

        return pd.DataFrame({
            "date": future_dates,
            "mean": preds.values,
            "median_forecast": preds.values,
            "lower": lower.values,
            "upper": upper.values,
            **intervals
        })

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=f"skforecast ({self.regressor_type.title()})",
            description="Direct multi-step forecaster with zero-leakage covariate handling.",
            rationale="Mathematically rigorous handling of known vs unknown drivers.",
            educational_video_url=""
        )
