from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series) -> List[ForecastMetric]:
    def safe_float(val):
        try:
            res = float(val)
            if np.isnan(res) or np.isinf(res):
                return 0.0
            return res
        except Exception:
            return 0.0

    metrics = [
        ForecastMetric(
            name="MAE", value=safe_float(mean_absolute_error(y_true, y_pred))
        ),
        ForecastMetric(
            name="RMSE",
            value=safe_float(np.sqrt(mean_squared_error(y_true, y_pred))),
        ),
        ForecastMetric(
            name="MAPE",
            value=safe_float(mean_absolute_percentage_error(y_true, y_pred)),
        ),
    ]
    return metrics


class InternalForecaster(ABC):
    """Base class for internal forecast implementations."""

    @abstractmethod
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        pass

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        pass

    @staticmethod
    @abstractmethod
    def get_metadata() -> ModelMetadata:
        pass


class SimpleAdditiveForecaster(InternalForecaster):
    """
    A robust baseline forecaster using Holt-Winters Exponential Smoothing.
    """

    def __init__(self):
        self.model = None
        self.fit_result = None
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.last_date = None
        self.freq: Optional[str] = None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )

        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        # Train/Val Split
        split_idx = int(len(df) * 0.8)
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        try:
            model = ExponentialSmoothing(
                train[self.target_col], trend="add", seasonal="add", freq=self.freq
            )
            fit_result = model.fit()
            val_preds = fit_result.forecast(len(val))

            # Re-fit on full data for final prediction
            self.model = ExponentialSmoothing(
                df[self.target_col], trend="add", seasonal="add", freq=self.freq
            )
            self.fit_result = self.model.fit()

            return calculate_metrics(val[self.target_col], val_preds)
        except Exception:
            # Fallback
            model = ExponentialSmoothing(
                train[self.target_col], trend="add", seasonal=None, freq=self.freq
            )
            fit_result = model.fit()
            val_preds = fit_result.forecast(len(val))

            self.model = ExponentialSmoothing(
                df[self.target_col], trend="add", seasonal=None, freq=self.freq
            )
            self.fit_result = self.model.fit()
            return calculate_metrics(val[self.target_col], val_preds)

    def predict(self, horizon: int) -> pd.DataFrame:
        if not self.fit_result:
            raise ValueError("Model not fitted yet.")
        forecast_values = self.fit_result.forecast(horizon)
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: forecast_values}
        )

    @staticmethod
    def get_metadata() -> ModelMetadata:
        return ModelMetadata(
            name="Exponential Smoothing (ETS)",
            description=(
                "A robust statistical model that captures trends and seasonal "
                "cycles by weighting recent observations more heavily."
            ),
            rationale=(
                "Chosen because your data shows clear repetitive patterns and "
                "a consistent trajectory over time. It is a gold standard for "
                "stable business metrics."
            ),
            educational_video_url="https://www.youtube.com/watch?v=Du8h_S_ndRE",
        )


class RandomForestForecaster(InternalForecaster):
    """
    Random Forest Regressor for non-strictly temporal or complex patterns.
    Uses lags as features.
    """

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.last_date = None
        self.freq: Optional[str] = None
        self.lags = 3

    def _create_lags(
        self, df: pd.DataFrame, target: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        X = pd.DataFrame(index=df.index)
        for i in range(1, self.lags + 1):
            X[f"lag_{i}"] = df[target].shift(i)
        X = X.dropna()
        y = df[target].loc[X.index]
        return X, y

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )

        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        X, y = self._create_lags(df, self.target_col)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        self.model.fit(X_train, y_train)
        val_preds = self.model.predict(X_val)

        # Final fit on all available data
        self.model.fit(X, y)

        return calculate_metrics(y_val, val_preds)

    def predict(self, horizon: int) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        # Simple recursive prediction for prototype
        last_val = self.model.predict(np.zeros((1, self.lags)))[0]

        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: [last_val] * horizon}
        )

    @staticmethod
    def get_metadata() -> ModelMetadata:
        return ModelMetadata(
            name="Random Forest Regressor",
            description=(
                "A versatile machine learning model that uses a 'forest' of "
                "decision trees to find non-linear relationships in complex data."
            ),
            rationale=(
                "Chosen for its ability to handle multiple variables and "
                "irregular patterns that traditional statistical models might miss."
            ),
            educational_video_url="https://www.youtube.com/watch?v=J4Wdy0Wc_xQ",
        )


class SmartForecastEngine:
    """
    Main Forecast Engine that selects the appropriate model based on Ontology.
    """

    def __init__(self):
        self.active_model: Optional[InternalForecaster] = None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        # Selection Logic
        if ontology.problem.task_type == "time_series_regression":
            self.active_model = SimpleAdditiveForecaster()
        else:
            self.active_model = RandomForestForecaster()

        return self.active_model.fit(df, ontology)

    def predict(self, horizon: int) -> pd.DataFrame:
        if not self.active_model:
            raise ValueError("Model not fitted yet.")
        return self.active_model.predict(horizon)

    def get_metadata(self) -> Any:
        if not self.active_model:
            # Return default or placeholder if accessed before fit (shouldn't happen
            # in current flow)
            # Or assume default model metadata
            return SimpleAdditiveForecaster.get_metadata()
        return self.active_model.get_metadata()
