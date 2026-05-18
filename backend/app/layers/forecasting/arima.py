from typing import List, Optional

import numpy as np
import pandas as pd
from pmdarima import auto_arima  # type: ignore[reportMissingImports]

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata
from app.layers.forecasting.base import InternalForecaster, calculate_metrics, walk_forward_backtest


class ARIMAForecaster(InternalForecaster):
    """
    AutoARIMA implementation using pmdarima for fast, automated model selection.
    """

    def __init__(self):
        self.model = None
        self.time_col = None
        self.target_col = None
        self.last_date: Optional[pd.Timestamp] = None
        self.freq: Optional[str] = None
        self.residuals_std = 0.0
        self.complexity_score = 1.0  # Default, gets updated in fit()
        self.archetype = "The Autoregressive Pattern (Correlation with Past)"

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        if auto_arima is None:
            raise ImportError("pmdarima is required to use ARIMAForecaster.")
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df_index = df.set_index(self.time_col)
        df_index.index = pd.to_datetime(df_index.index)
        self.last_date = pd.Timestamp(df_index.index.max())
        self.freq = pd.infer_freq(pd.DatetimeIndex(df_index.index)) or "D"

        # Speed Constraints (Crucial)
        autoarima_params = {
            "stepwise": True,
            "suppress_warnings": True,
            "error_action": "ignore",
            "max_p": 3,
            "max_q": 3,
            "max_d": 2,
        }

        # Seasonal handling: 12 for month, 7 for day
        if self.freq in ["M", "MS", "BM", "BMS"]:
            autoarima_params.update({"seasonal": True, "m": 12, "max_P": 2, "max_Q": 2})
        elif self.freq in ["D", "B"]:
            autoarima_params.update({"seasonal": True, "m": 7, "max_P": 2, "max_Q": 2})

        horizon_steps = ontology.requirements.horizon_requirement.steps

        def _fit_predict(train_df: pd.DataFrame, val_df: pd.DataFrame) -> pd.Series:
            temp_model = auto_arima(train_df[self.target_col], **autoarima_params)
            preds = temp_model.predict(n_periods=len(val_df))
            return pd.Series(preds, index=val_df.index)

        try:
            val_preds, val_actuals = walk_forward_backtest(
                df_index,
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

            residuals = val_actuals.values - val_preds.values
            self.residuals_std = float(np.std(residuals)) if len(residuals) > 1 else 0.0
            self.validation_predictions = val_preds
            self.validation_actuals = val_actuals

            # Refit the model on the entire 100% dataframe using a single fast pass
            self.model = auto_arima(
                df_index[self.target_col],
                **autoarima_params,
                stepwise=False,
            )

            # Dynamic Complexity Scoring
            order = self.model.order
            seasonal_order = self.model.seasonal_order
            raw_complexity = 1 + (sum(order) + sum(seasonal_order[:3])) / 6.0
            self.complexity_score = max(1.0, min(4.0, raw_complexity))

            if sum(seasonal_order[:3]) > 0:
                self.archetype = (
                    "The Seasonal Autoregressive Pattern "
                    "(Seasonality + Past Correlation)"
                )
            else:
                self.archetype = "The Autoregressive Pattern (Correlation with Past)"

            return calculate_metrics(val_actuals, val_preds)

        except (ValueError, RuntimeError, TypeError) as e:
            print(f"LOG: AutoARIMA fit failed: {e}")
            inf_metrics = [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]
            return inf_metrics

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if not self.model or self.last_date is None or self.freq is None:
            raise ValueError("Model must be fitted before predict.")

        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        # Point forecast
        mean_vals = self.model.predict(n_periods=horizon)
        if hasattr(mean_vals, "values"):
            mean_vals = mean_vals.values

        # Generate multi-layer confidence intervals using base class logic
        intervals = self._calculate_multi_layer_intervals(mean_vals, self.residuals_std)
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

        if self.freq in ["A", "Y", "AS", "YS"]:
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        model_name = "AutoARIMA"
        if self.model:
            model_name = f"AutoARIMA {self.model.order}{self.model.seasonal_order}"

        return ModelMetadata(
            name=model_name,
            description="A classic statistical method that looks at past trends, repeating seasons, and recent shocks to project forward.",
            rationale=f"Selected due to: {self.archetype}",
            educational_video_url="https://www.youtube.com/watch?v=3UmyHed0iYe",
        )
