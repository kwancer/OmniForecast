from typing import List, Optional

import numpy as np
import pandas as pd

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata
from app.layers.forecasting.base import InternalForecaster, calculate_metrics


class SeasonalNaiveForecaster(InternalForecaster):
    complexity_score = 0.5
    archetype = "Seasonal Random Walk (Tomorrow = Same day last year/season)"

    def __init__(self, season_length=7):
        self.season_length = season_length
        self.history: Optional[pd.Series] = None
        self.time_col = None
        self.target_col = None
        self.last_date: Optional[pd.Timestamp] = None
        self.freq: Optional[str] = None
        self.residuals_std = 0.0

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        df.index = pd.to_datetime(df.index)
        self.last_date = pd.Timestamp(df.index.max())
        self.freq = pd.infer_freq(pd.DatetimeIndex(df.index)) or "D"

        if self.freq == "M":
            self.season_length = 12
        elif self.freq == "D":
            self.season_length = 7

        split_idx = int(len(df) * 0.8)
        if split_idx == 0:
            split_idx = 1
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        if len(val) == 0:
            # No validation data available; return worst-case metrics so that
            # this model is not incorrectly favored during model selection.
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        def get_seasonal_preds(history_series, steps):
            preds = []
            for i in range(steps):
                lookback_idx = (i % self.season_length) + 1
                try:
                    preds.append(history_series.iloc[-lookback_idx])
                except IndexError:
                    preds.append(history_series.iloc[-1])
            return preds

        val_preds_list = get_seasonal_preds(train[self.target_col], len(val))
        val_preds = pd.Series(val_preds_list, index=val.index)

        # Calculate residuals for confidence intervals
        residuals = val[self.target_col] - val_preds
        self.residuals_std = float(residuals.std()) if len(residuals) > 1 else 0.0
        self.validation_predictions = val_preds
        self.validation_actuals = val[self.target_col]

        self.history = df[self.target_col]
        return calculate_metrics(val[self.target_col], val_preds)

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if self.last_date is None or self.freq is None or self.history is None:
            raise ValueError("Model not fitted.")
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        preds = []
        last_season = self.history.iloc[-self.season_length :].values

        for i in range(horizon):
            preds.append(last_season[i % self.season_length])

        predictions = np.array(preds)

        # Multi-layer intervals
        intervals = self._calculate_multi_layer_intervals(
            predictions, self.residuals_std
        )

        # Legacy columns
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )

        df_data = {
            "date": future_dates,
            "mean": predictions,
            "median_forecast": predictions,
            "lower": lower,
            "upper": upper,
            **intervals,
        }

        if self.freq == "A" or self.freq == "Y":
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="Seasonal Naive",
            description="A simple benchmark that predicts the future will look like the same time period last year (or last week, etc.).",
            rationale="Robust baseline for seasonal data.",
            educational_video_url="",
        )
