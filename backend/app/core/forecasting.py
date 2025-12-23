from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet

from app.api.schemas import ForecastMetric
from app.models.ontology import ForecastOntology


class Forecaster(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> Dict[str, float]:
        """Fits the model and returns validation metrics."""
        pass

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """Generates future predictions."""
        pass

    @staticmethod
    @abstractmethod
    def get_metadata() -> Any:
        """Returns model metadata."""
        pass


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


class SimpleAdditiveForecaster(Forecaster):
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
            c.column_name for c in ontology.intent.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.intent.columns if c.role == "target"
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
    def get_metadata() -> Any:
        from app.models.ontology import ModelMetadata

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


class RandomForestForecaster(Forecaster):
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
            c.column_name for c in ontology.intent.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.intent.columns if c.role == "target"
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
        # Placeholder for recursive multi-step prediction
        # For prototype, we'll return a simple extrapolation or last known
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        # Simple implementation: use last known values to predict
        # This is a very basic recursive forecast
        # ... (simplified for prototype)
        last_val = self.model.predict(np.zeros((1, self.lags)))[
            0
        ]  # Extremely simplified
        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: [last_val] * horizon}
        )

    @staticmethod
    def get_metadata() -> Any:
        from app.models.ontology import ModelMetadata

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


class ProphetForecaster(Forecaster):
    """
    Facebook Prophet for daily data with multiple seasonality and holidays.
    """

    def __init__(self):
        self.model = None
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.regressors: List[str] = []
        self.last_date = None
        self.freq: Optional[str] = None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.intent.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.intent.columns if c.role == "target"
        )

        # Use identified regressors
        self.regressors = ontology.analysis.regressors

        # Prepare DataFrame for Prophet
        prophet_df = df.rename(columns={self.time_col: "ds", self.target_col: "y"})

        # Determine seasonality settings
        seasonality_mode = ontology.analysis.seasonality_mode
        if seasonality_mode == "none":
            # Prophet needs one, usually additive is safer default if unsure
            seasonality_mode = "additive"

        # Initialize Prophet
        self.model = Prophet(seasonality_mode=seasonality_mode)

        # Add regressors
        for reg in self.regressors:
            self.model.add_regressor(reg)

        # Train/Val Split
        split_idx = int(len(prophet_df) * 0.8)
        train, val = prophet_df.iloc[:split_idx], prophet_df.iloc[split_idx:]

        self.model.fit(train)

        # Predict on validation
        val_future = val[["ds"] + self.regressors] if self.regressors else val[["ds"]]
        val_forecast = self.model.predict(val_future)
        val_preds = val_forecast["yhat"]

        # Refit on full data
        self.model = Prophet(seasonality_mode=seasonality_mode)
        for reg in self.regressors:
            self.model.add_regressor(reg)
        self.model.fit(prophet_df)

        self.last_date = prophet_df["ds"].max()
        self.freq = pd.infer_freq(prophet_df["ds"]) or "D"

        return calculate_metrics(val["y"], val_preds.values)

    def predict(self, horizon: int) -> pd.DataFrame:
        future = self.model.make_future_dataframe(periods=horizon, freq=self.freq)

        # Handle regressors for future
        # For this prototype, we will assume regressors are static or use last value
        # if future values not provided.
        # Ideally, we would need a way to input future values for regressors.
        # Here we just fill with 0 or last value to avoid crash,
        # but warn this is a limitation
        if self.regressors:
            # Very simple imputation for future regressors: use last known value
            # This is NOT correct for real forecasting but sufficient for avoiding
            # crashes in this MVP
            for reg in self.regressors:
                if reg not in future.columns:
                    last_val = self.model.history[reg].iloc[-1]
                    future[reg] = last_val  # Naive extension

        forecast = self.model.predict(future)

        # Extract relevant part
        future_forecast = forecast.iloc[-horizon:][["ds", "yhat"]]
        future_forecast.columns = [self.time_col, self.target_col]

        return future_forecast

    @staticmethod
    def get_metadata() -> Any:
        from app.models.ontology import ModelMetadata

        return ModelMetadata(
            name="Prophet",
            description=(
                "A procedure for forecasting time series data based on an additive "
                "model where non-linear trends are fit with yearly, weekly, and "
                "daily seasonality."
            ),
            rationale=(
                "Chosen because your data appears to be daily with potential "
                "seasonality, which Prophet handles exceptionally well."
            ),
            educational_video_url="https://facebook.github.io/prophet/",
        )


def get_forecaster(ontology: ForecastOntology) -> Forecaster:
    # Check if Prophet is suitable
    # Criteria: Daily data + Seasonality detected
    is_daily = ontology.analysis.is_daily
    has_seasonality = ontology.analysis.seasonality_mode != "none"

    if is_daily and has_seasonality:
        return ProphetForecaster()

    if ontology.intent.problem.task_type == "time_series_regression":
        return SimpleAdditiveForecaster()

    return RandomForestForecaster()
