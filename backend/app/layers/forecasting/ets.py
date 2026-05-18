from typing import List, Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata
from app.layers.forecasting.base import InternalForecaster, calculate_metrics, walk_forward_backtest


class ETSForecaster(InternalForecaster):
    """
    Wrapper for statsmodels Exponential Smoothing covering multiple variants.
    """

    def __init__(self, config_name: str, trend=None, damped=False, seasonal=None):
        self.config_name = config_name
        self.trend = trend
        self.damped = damped
        self.seasonal = seasonal

        self.model = None
        self.fit_result = None
        self.time_col = None
        self.target_col = None
        self.last_date: Optional[pd.Timestamp] = None
        self.freq: Optional[str] = None

        # Assignments based on complexity
        if seasonal:
            self.complexity_score = 4
            self.archetype = "The Seasonal Specialist (Trend + Seasonality)"
        elif damped:
            self.complexity_score = 3
            self.archetype = "The Realistic Climber (Damped Trend)"
        elif trend:
            self.complexity_score = 2
            self.archetype = "The Steady Climber (Trend, No Seasonality)"
        else:
            self.complexity_score = 1
            self.archetype = "The Flat Line (No Trend, No Seasonality)"

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        df.index = pd.to_datetime(df.index)
        self.freq = pd.infer_freq(pd.DatetimeIndex(df.index)) or "D"
        df.index.freq = self.freq
        self.last_date = pd.Timestamp(df.index.max())

        # Determine seasonal_periods only if seasonal is specified
        seasonal_periods = None
        if self.seasonal is not None:
            if self.freq in ("D", "B"):
                seasonal_periods = 7
            elif self.freq in ("M", "MS"):
                seasonal_periods = 12
            elif self.freq in ("H", "h"):
                seasonal_periods = 24
            elif self.freq in ("T", "min"):
                seasonal_periods = 60
            elif self.freq in ("S", "s"):
                seasonal_periods = 60
            elif self.freq in ("ms", "L"):
                seasonal_periods = 1000
            else:
                seasonal_periods = 7  # Safe fallback

        horizon_steps = ontology.requirements.horizon_requirement.steps

        def _fit_predict(train_df: pd.DataFrame, val_df: pd.DataFrame) -> pd.Series:
            model = ExponentialSmoothing(
                train_df[self.target_col],
                trend=self.trend,
                damped_trend=self.damped,
                seasonal=self.seasonal,
                seasonal_periods=seasonal_periods,
                freq=self.freq,
            )
            fit_result = model.fit(optimized=True)
            return fit_result.forecast(len(val_df))

        try:
            val_preds, val_actuals = walk_forward_backtest(
                df,
                self.time_col,
                self.target_col,
                horizon_steps=horizon_steps,
                fit_predict_fn=_fit_predict,
            )

            if len(val_preds) == 0:
                return [
                    ForecastMetric(name="MAE", value=float("inf")),
                    ForecastMetric(name="RMSE", value=float("inf")),
                    ForecastMetric(name="MAPE", value=float("inf")),
                ]

            # FIT ON FULL DATA for later predict()
            self.model = ExponentialSmoothing(
                df[self.target_col],
                trend=self.trend,
                damped_trend=self.damped,
                seasonal=self.seasonal,
                seasonal_periods=seasonal_periods,
                freq=self.freq,
            )
            self.fit_result = self.model.fit(optimized=True)

            self.validation_predictions = val_preds
            self.validation_actuals = val_actuals
            self.residuals_std = (
                float((val_actuals - val_preds).std()) if len(val_preds) > 1 else 0.0
            )

            return calculate_metrics(val_actuals, val_preds)
        except (ValueError, RuntimeError, TypeError) as e:
            print(f"LOG: Model {self.config_name} failed: {e}")
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if not self.fit_result or self.last_date is None or self.freq is None:
            raise ValueError("Model not fitted.")

        # Point forecast
        forecast_values = self.fit_result.forecast(horizon)
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        # Simulation-based confidence intervals
        try:
            # Generate simulation paths
            simulations = self.fit_result.simulate(
                nsimulations=horizon,
                anchor="end",
                repetitions=1000,
                random_state=42,
            )
            # simulations shape: (horizon, 1000)

            # Calculate required percentiles
            # Median: 50%
            median_vals = np.percentile(simulations, 50, axis=1)

            # Layer 1 (Outer/80%): 10th and 90th
            conf_80_lower = np.percentile(simulations, 10, axis=1)
            conf_80_upper = np.percentile(simulations, 90, axis=1)

            # Layer 2 (Middle/60%): 20th and 80th
            conf_60_lower = np.percentile(simulations, 20, axis=1)
            conf_60_upper = np.percentile(simulations, 80, axis=1)

            # Layer 3 (Inner/30%): 35th and 65th
            conf_30_lower = np.percentile(simulations, 35, axis=1)
            conf_30_upper = np.percentile(simulations, 65, axis=1)

            # Fallback for legacy interval_width
            alpha = 1 - interval_width
            lower = np.percentile(simulations, (alpha / 2) * 100, axis=1)
            upper = np.percentile(simulations, (1 - alpha / 2) * 100, axis=1)

            df_data = {
                "date": future_dates,
                "median_forecast": median_vals,
                "mean": forecast_values.values,  # Keep actual point forecast as mean
                "lower": lower,
                "upper": upper,
                "conf_80_lower": conf_80_lower,
                "conf_80_upper": conf_80_upper,
                "conf_60_lower": conf_60_lower,
                "conf_60_upper": conf_60_upper,
                "conf_30_lower": conf_30_lower,
                "conf_30_upper": conf_30_upper,
            }

            if self.freq == "A" or self.freq == "Y":
                df_data["year"] = [d.year for d in future_dates]

            return pd.DataFrame(df_data)

        except (ValueError, RuntimeError, TypeError) as e:
            print(f"LOG: ETS simulation failed, using point forecast: {e}")
            # Fallback: use residual-based approach if simulation fails
            mean_vals = forecast_values.values
            intervals = self._calculate_multi_layer_intervals(
                mean_vals, self.residuals_std
            )
            lower, upper = self._calculate_intervals(
                mean_vals, interval_width, self.residuals_std
            )

            df_data = {
                "date": future_dates,
                "mean": mean_vals,
                "median_forecast": mean_vals,
                "lower": lower,
                "upper": upper,
                **intervals,
            }
            if self.freq == "A" or self.freq == "Y":
                df_data["year"] = [d.year for d in future_dates]

            return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=f"ETS ({self.config_name})",
            description="A method that smooths out noise in your data and gives more weight to recent history when making predictions.",
            rationale=f"Selected due to {self.archetype} characteristics.",
            educational_video_url="https://www.youtube.com/watch?v=Du8h_S_ndRE",
        )
